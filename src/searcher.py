# src/searcher.py みたいな場所に置いている想定

from typing import List, Dict, Tuple, Any
from pathlib import Path
import json

# constellation_bm25_vec_rrf_search.py と同じフォルダにある前提
from .constellation_bm25_vec_rrf_search import hybrid_search_constellations


class ConstellationSearcher:
    """
    星座検索クラス（BM25 + ベクトル + RRF 版）

    app.py からは：
        searcher = ConstellationSearcher(CONSTELLATION_DATA_PATH, INDEX_PATH)
        results = searcher.search(expanded_query, top_k=top_k)
    という形で呼ばれる前提でインターフェースを維持します。
    """

    def __init__(self, data_path: str | Path, index_path: str | Path):
        # data_path から星座データ(JSON)をロードしておく
        data_path = Path(data_path)
        with data_path.open("r", encoding="utf-8") as f:
            constellations: list[dict[str, Any]] = json.load(f)

        # id -> 星座情報 の辞書を作成
        self.constellations_by_id: dict[str, dict[str, Any]] = {}
        for c in constellations:
            cid = c.get("id")
            if cid:
                self.constellations_by_id[cid] = c

        # index_path は今のところ使っていないが、
        # 既存の __init__(data_path, index_path) の形は維持する
        self.data_path = data_path
        self.index_path = Path(index_path)

    # ここが app.py から呼ばれるメソッド
    def search(self, expanded_query: Dict, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        拡張クエリ(expanded_query)を受け取って、
        ハイブリッド検索の結果を [(星座dict, score), ...] で返す。
        """

        # expanded_query から元のクエリ文字列をなるべく取り出す
        query_text = self._extract_query_text(expanded_query)

        # BM25 + ベクトル + RRF で検索
        # constellation_bm25_vec_rrf_search.hybrid_search_constellations は
        # [{"id", "jp_name", "snippet", "rrf_score", "bm25_score", "vec_score"}, ...]
        # を返す想定
        raw_results = hybrid_search_constellations(
            query=query_text,
            topk=top_k,
        )

        results: list[tuple[dict[str, Any], float]] = []
        for r in raw_results:
            cid = r.get("id")
            score = float(r.get("rrf_score", r.get("score", 0.0)))

            # JSON 側にある詳細情報を優先して拾う
            base = self.constellations_by_id.get(cid, {}).copy()
            if not base:
                # JSON に無い場合は最低限の情報を埋める
                base = {
                    "id": cid,
                    "jp_name": r.get("jp_name"),
                }

            # snippet が欲しければここで追加
            if "snippet" not in base and "snippet" in r:
                base["snippet"] = r["snippet"]

            results.append((base, score))

        return results

    # expanded_query(dict) から文字列クエリを作るヘルパー
    def _extract_query_text(self, expanded_query: Dict) -> str:
        # もうすでに str の場合はそのまま
        if isinstance(expanded_query, str):
            return expanded_query

        if not isinstance(expanded_query, dict):
            return str(expanded_query)

        # よくありそうなキーを優先して見る（必要なら調整）
        for key in ("original", "query", "raw_query"):
            if key in expanded_query and isinstance(expanded_query[key], str):
                return expanded_query[key]

        # トークンやキーワードがあれば連結
        for key in ("tokens", "keywords"):
            if key in expanded_query and isinstance(expanded_query[key], (list, tuple)):
                return " ".join(str(t) for t in expanded_query[key])

        # 最後の手段：dict の value を全部つなげる
        parts: list[str] = []
        for v in expanded_query.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, (list, tuple)):
                parts.extend(str(x) for x in v)
            else:
                parts.append(str(v))
        return " ".join(parts)
