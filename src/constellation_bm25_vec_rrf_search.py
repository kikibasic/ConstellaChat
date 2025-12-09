# constellation_search.py
# BM25 + Vector Store + RRF ハイブリッドで星座検索する専用スクリプト


from pathlib import Path
import os
import joblib
from openai import OpenAI
from constellation_bm25_build import InvertedIndexArray

# =========================
# 設定
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent
INDEX_DIR = PROJECT_ROOT / "data/index_constellation"

# さっき作った Vector Store の ID（ログに出ていたものをそのまま貼る）
VECTOR_STORE_ID = "vs_6936a06353e48191ab2d280aedb802d6"

# APIキー（環境変数で設定しておくこと）
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# =========================
# BM25 インデックスのロード
# =========================

bm25_index = joblib.load(INDEX_DIR / "bm25_index.joblib")   # InvertedIndexArray
docs_list  = joblib.load(INDEX_DIR / "docs.joblib")         # List[str] index_text
keys       = joblib.load(INDEX_DIR / "keys.joblib")         # List[str] "Orion" など
titles     = joblib.load(INDEX_DIR / "titles.joblib")       # dict[id] -> jp_name

# id -> doc_id の逆引きテーブル
id2doc_id = {cid: i for i, cid in enumerate(keys)}


# =========================
# BM25 検索
# =========================

def search_constellations_bm25(query: str, k: int = 10):
    """
    BM25 だけで検索して、id / jp_name / score / snippet を返す。
    """
    results = bm25_index.bm25_search(query, topk=k)

    out = []
    for doc_id, score in results:
        cid = keys[doc_id]
        jp_name = titles.get(cid, cid)
        snippet = docs_list[doc_id][:120].replace("\n", "")
        out.append(
            {
                "id": cid,
                "jp_name": jp_name,
                "score": float(score),
                "snippet": snippet,
            }
        )
    return out


# =========================
# ベクトル検索（Vector Store）
# =========================

def search_constellations_vec(query: str, k: int = 10):
    """
    OpenAI Vector Store に対して semantic search。
    constellation_vec_upload.py で attributes["filename"] = id を入れている前提。
    """
    res = client.vector_stores.search(
        vector_store_id=VECTOR_STORE_ID,
        query=query,
        max_num_results=k,
        # rewrite_query=False  # 必要なら明示的に
    )

    out = []

    for item in res.data[:k]:
        # attributes["filename"] に "Orion" などが入っている想定
        cid = None
        attrs = getattr(item, "attributes", None)
        if attrs:
            cid = attrs.get("filename")

        # 念のため filename も fallback に見る
        if not cid and hasattr(item, "filename"):
            cid = item.filename

        # id から jp_name / snippet を復元
        if cid in id2doc_id:
            doc_id = id2doc_id[cid]
            jp_name = titles.get(cid, cid)
            snippet = docs_list[doc_id][:120].replace("\n", "")
        else:
            jp_name = cid or "(unknown)"
            snippet = ""

        score = float(getattr(item, "score", 0.0))

        out.append(
            {
                "id": cid,
                "jp_name": jp_name,
                "score": score,
                "snippet": snippet,
            }
        )

    return out


# =========================
# Reciprocal Rank Fusion (RRF)
# =========================

def reciprocal_rank_fusion(bm25_results, vec_results, rrf_k: int = 60):
    """
    bm25_results, vec_results はどちらも
      [{"id": ..., "jp_name": ..., "score": ..., "snippet": ...}, ...]
    という形式を前提。
    """
    merged = {}

    # BM25 側
    for rank, r in enumerate(bm25_results, start=1):
        cid = r["id"]
        if cid is None:
            continue
        if cid not in merged:
            merged[cid] = {
                "id": cid,
                "jp_name": r["jp_name"],
                "snippet": r["snippet"],
                "bm25_score": r["score"],
                "vec_score": 0.0,
                "rrf_score": 0.0,
            }
        merged[cid]["rrf_score"] += 1.0 / (rrf_k + rank)

    # ベクトル側
    for rank, r in enumerate(vec_results, start=1):
        cid = r["id"]
        if cid is None:
            continue
        if cid not in merged:
            merged[cid] = {
                "id": cid,
                "jp_name": r["jp_name"],
                "snippet": r["snippet"],
                "bm25_score": 0.0,
                "vec_score": r["score"],
                "rrf_score": 0.0,
            }
        else:
            merged[cid]["vec_score"] = r["score"]
        merged[cid]["rrf_score"] += 1.0 / (rrf_k + rank)

    # スコアでソートしてリスト化
    merged_list = list(merged.values())
    merged_list.sort(key=lambda x: x["rrf_score"], reverse=True)
    return merged_list


def hybrid_search_constellations(query: str, k_bm25: int = 20, k_vec: int = 20, topk: int = 10):
    """
    BM25 + ベクトル検索を RRF でマージして上位 topk を返す。
    """
    bm25_results = search_constellations_bm25(query, k=k_bm25)
    vec_results = search_constellations_vec(query, k=k_vec)
    merged = reciprocal_rank_fusion(bm25_results, vec_results, rrf_k=60)
    return merged[:topk]


# =========================
# 動作確認（テスト用）
# =========================

if __name__ == "__main__":
    q = "冬の明るい星が目立つ星座"

    print("=== BM25 only ===")
    for r in search_constellations_bm25(q, k=5):
        print(f"- {r['jp_name']} ({r['id']}) bm25={r['score']:.3f}")
        print(f"  {r['snippet']}\n")

    print("=== Vector only ===")
    for r in search_constellations_vec(q, k=5):
        print(f"- {r['jp_name']} ({r['id']}) vec={r['score']:.3f}")
        print(f"  {r['snippet']}\n")

    print("=== Hybrid (RRF) ===")
    for r in hybrid_search_constellations(q, topk=5):
        print(
            f"- {r['jp_name']} ({r['id']}) "
            f"rrf={r['rrf_score']:.4f} bm25={r['bm25_score']:.3f} vec={r['vec_score']:.3f}"
        )
        print(f"  {r['snippet']}\n")
