# constellation_bm25_build.py
# 星座データ（myth_summary + keywords + best_months）から
# BM25 用インデックスを作成するだけのスクリプト
# ベクトル検索やRRFは一切含まない「授業準拠BM25版」

import json
import math
import re
from collections import Counter
from pathlib import Path

import joblib
from fugashi import Tagger


# ================================================================
# 設定
# ================================================================

# 星座データ（すでに keywords 付きにした JSON）
DATA_PATH = Path("./data/constellation_data_with_keywords.json")

# BM25インデックスを保存するディレクトリ
INDEX_DIR = Path("index_constellation")
INDEX_DIR.mkdir(exist_ok=True, parents=True)


# ================================================================
# 正規化 + 日本語トークナイズ（授業準拠：fugashi使用）
# ================================================================

_tagger = Tagger()  # 必要ならオプションはここで調整

def normalize(text: str) -> str:
    """簡単な正規化（スペース類を整理）"""
    if not text:
        return ""
    t = text.replace("\u3000", " ")
    t = re.sub(r"[\t\r\n]+", " ", t)
    t = re.sub(r"[ ]{2,}", " ", t)
    return t.strip()


def tokenize_ja(text: str):
    """
    授業ノートと同じ発想で、fugashi(MeCab)で分かち書き。
    記号・英数字だけのトークンは落とす。
    """
    text = normalize(text)
    tokens = []
    for w in _tagger(text):
        s = w.surface.strip()
        if not s:
            continue
        # 英数字・記号のみのトークンを除外
        if re.match(r"^[0-9A-Za-z!-/:-@[-`{-~]+$", s):
            continue
        tokens.append(s)
    return tokens


# ================================================================
# 検索用テキストの構築
# myth_summary + keywords + best_months を1本の文字列にする
# ================================================================

def build_index_text(entry: dict) -> str:
    """
    星座1件分のエントリから、BM25用の index_text を生成。
    - myth_summary
    - keywords
    - best_months（例: 11,12,1 → "11月 12月 1月"）
    """
    parts = []

    myth = entry.get("myth_summary", "")
    if myth:
        parts.append(myth)

    keywords = entry.get("keywords", [])
    if keywords:
        parts.append(" ".join(keywords))

    months = entry.get("best_months", [])
    if months:
        month_tokens = [f"{m}月" for m in months]
        parts.append(" ".join(month_tokens))

    return "。".join(parts)


# ================================================================
# 転置インデックス + BM25（授業ノート準拠）
# ================================================================

class InvertedIndexArray:
    def __init__(self):
        self.vocab = []
        self.postings = {}   # term -> [(doc_id, tf), ...]
        self.doc_count = 0
        self.avgdl = 0.0
        self.doc_lens = []

    def build(self, docs):
        """TF付き転置インデックスを構築"""
        self.doc_count = len(docs)
        vocab_set = set()
        postings = {}
        self.doc_lens = []

        for doc_id, doc in enumerate(docs):
            tokens = tokenize_ja(doc)
            tf_counts = Counter(tokens)
            self.doc_lens.append(len(tokens))

            for term, tf in tf_counts.items():
                vocab_set.add(term)
                postings.setdefault(term, []).append((doc_id, tf))

        self.avgdl = sum(self.doc_lens) / max(1, len(self.doc_lens))
        self.vocab = sorted(vocab_set)

        # doc_id順に整列（なくても動くが一応揃えておく）
        for t in postings:
            postings[t] = sorted(postings[t], key=lambda x: x[0])
        self.postings = postings

    def bm25(self, query_terms, k1=1.5, b=0.75):
        """BM25スコアを計算"""
        scores = {doc_id: 0.0 for doc_id in range(self.doc_count)}

        for term in query_terms:
            plist = self.postings.get(term, [])
            df = len(plist)
            if df == 0:
                continue
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)

            for doc_id, tf in plist:
                dl = self.doc_lens[doc_id]
                denom = tf + k1 * (1 - b + b * dl / self.avgdl)
                score = idf * (tf * (k1 + 1)) / denom
                scores[doc_id] += score

        return scores

    def bm25_search(self, query, topk=10):
        """クエリ文字列を入力して上位文書を返す（doc_id, score のリスト）"""
        terms = tokenize_ja(query)
        scores = self.bm25(terms)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:topk]


# ================================================================
# インデックス構築
# ================================================================

def build_constellation_index():
    """
    constellation_data_with_keywords.json から
    - docs: id -> index_text
    - titles: id -> jp_name
    を作成し、BM25インデックスを構築して joblib で保存する。
    """
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = {}    # id -> index_text
    titles = {}  # id -> jp_name

    for entry in data:
        cid = entry["id"]  # 例: "Orion"
        jp_name = entry.get("jp_name", cid)

        index_text = build_index_text(entry)

        docs[cid] = index_text
        titles[cid] = jp_name

    # docs.values() を BM25 に与える（keys() と順番を揃える）
    keys = list(docs.keys())
    docs_list = list(docs.values())

    index = InvertedIndexArray()
    index.build(docs_list)

    # 授業ノートと同じように4ファイルに分けて保存
    joblib.dump(index, INDEX_DIR / "bm25_index.joblib")
    joblib.dump(docs_list, INDEX_DIR / "docs.joblib")
    joblib.dump(keys, INDEX_DIR / "keys.joblib")
    joblib.dump(titles, INDEX_DIR / "titles.joblib")

    print(f"✅ Indexed {len(docs)} constellations")
    print(f"📦 Saved to {INDEX_DIR.resolve()}")


# ================================================================
# 簡単なBM25検索テスト（BM25だけ）
# ================================================================

def test_bm25():
    index = joblib.load(INDEX_DIR / "bm25_index.joblib")
    docs_list = joblib.load(INDEX_DIR / "docs.joblib")
    keys = joblib.load(INDEX_DIR / "keys.joblib")
    titles = joblib.load(INDEX_DIR / "titles.joblib")

    query = "冬の明るい星が目立つ星座"
    results = index.bm25_search(query, topk=5)

    print("\n=== BM25 only (test) ===")
    for doc_id, score in results:
        cid = keys[doc_id]
        name = titles.get(cid, cid)
        snippet = docs_list[doc_id][:120].replace("\n", "")
        print(f"- {name} ({cid}) score={score:.3f}")
        print(f"  {snippet}")
        print()


if __name__ == "__main__":
    # ① インデックスを作成（毎回上書きでOK）
    build_constellation_index()

    # ② 簡単なBM25テスト
    test_bm25()
