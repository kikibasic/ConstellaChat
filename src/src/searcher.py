"""
SkyLore - 検索モジュール
転置インデックスを使って星座を検索する
"""
import json
import os
from typing import List, Dict, Tuple
from collections import defaultdict

# 友達が作成する転置インデックスのインターフェース
# 転置インデックスの想定フォーマット:
# {
#   "冬": ["Orion", "Gemini", "Taurus", ...],
#   "12": ["Orion", "Andromeda", ...],
#   "オリオン": ["Orion"],
#   ...
# }


class ConstellationSearcher:
    """星座検索クラス"""
    
    def __init__(self, data_path: str, index_path: str):
        """
        Args:
            data_path: 星座データJSONのパス
            index_path: 転置インデックスJSONのパス
        """
        self.constellations = self._load_constellations(data_path)
        self.inverted_index = self._load_index(index_path)
        
        # IDから星座データへのマッピング
        self.id_to_constellation = {c["id"]: c for c in self.constellations}
    
    def _load_constellations(self, path: str) -> List[Dict]:
        """星座データを読み込む"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: {path} が見つかりません。空のデータを使用します。")
            return []
    
    def _load_index(self, path: str) -> Dict[str, List[str]]:
        """転置インデックスを読み込む"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: {path} が見つかりません。インデックスを自動生成します。")
            return self._build_simple_index()
    
    def _build_simple_index(self) -> Dict[str, List[str]]:
        """
        簡易的な転置インデックスを構築
        ※ 友達が本格的なものを作るまでの仮実装
        """
        index = defaultdict(list)
        
        for constellation in self.constellations:
            cid = constellation["id"]
            
            # 月からインデックス
            for month in constellation.get("best_months", []):
                index[str(month)].append(cid)
                
                # 季節もインデックス
                if month in [12, 1, 2]:
                    index["冬"].append(cid)
                elif month in [3, 4, 5]:
                    index["春"].append(cid)
                elif month in [6, 7, 8]:
                    index["夏"].append(cid)
                elif month in [9, 10, 11]:
                    index["秋"].append(cid)
            
            # 日本語名からインデックス
            jp_name = constellation.get("jp_name", "")
            index[jp_name].append(cid)
            
            # キーワードからインデックス（あれば）
            for keyword in constellation.get("keywords", []):
                index[keyword].append(cid)
            
            # 神話のキーワードからインデックス
            myth = constellation.get("myth_summary", "")
            # 簡易的な形態素解析（本格的にはMeCab等を使う）
            for word in ["ゼウス", "ヘルクレス", "オリオン", "ペルセウス", "アポロン", 
                        "ポセイドン", "ヘラ", "アフロディーテ", "狩人", "勇者", "怪物"]:
                if word in myth:
                    index[word].append(cid)
        
        # 重複を除去
        return {k: list(set(v)) for k, v in index.items()}
    
    def search(self, expanded_query: Dict, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        拡張されたクエリで星座を検索
        
        Args:
            expanded_query: QueryExpanderからの拡張結果
            top_k: 返す結果の数
        
        Returns:
            (星座データ, スコア) のリスト
        """
        scores = defaultdict(float)
        
        # 月でスコアリング（重み: 3）
        for month in expanded_query.get("months", []):
            for cid in self.inverted_index.get(str(month), []):
                scores[cid] += 3.0
        
        # 季節でスコアリング（重み: 2）
        season = expanded_query.get("season")
        if season:
            for cid in self.inverted_index.get(season, []):
                scores[cid] += 2.0
        
        # キーワードでスコアリング（重み: 1）
        for keyword in expanded_query.get("keywords", []):
            for cid in self.inverted_index.get(keyword, []):
                scores[cid] += 1.0
        
        # 星座ヒントでスコアリング（重み: 5）- 直接言及された星座を優先
        for hint in expanded_query.get("constellation_hints", []):
            # 日本語名で検索
            for cid in self.inverted_index.get(hint, []):
                scores[cid] += 5.0
            # 部分一致も試みる
            hint_base = hint.replace("座", "")
            for key, cids in self.inverted_index.items():
                if hint_base in key:
                    for cid in cids:
                        scores[cid] += 3.0
        
        # スコア順にソート
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # 上位K件を返す
        results = []
        for cid, score in sorted_results[:top_k]:
            if cid in self.id_to_constellation:
                results.append((self.id_to_constellation[cid], score))
        
        return results
    
    def get_related_constellations(self, constellation_id: str) -> List[Dict]:
        """関連する星座を取得"""
        constellation = self.id_to_constellation.get(constellation_id)
        if not constellation:
            return []
        
        related_ids = constellation.get("related", [])
        return [self.id_to_constellation[rid] for rid in related_ids 
                if rid in self.id_to_constellation]
    
    def get_constellation_by_id(self, constellation_id: str) -> Dict:
        """IDから星座を取得"""
        return self.id_to_constellation.get(constellation_id)
    
    def search_by_month(self, month: int) -> List[Dict]:
        """月から見える星座を検索"""
        cids = self.inverted_index.get(str(month), [])
        return [self.id_to_constellation[cid] for cid in cids 
                if cid in self.id_to_constellation]


# テスト用
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import CONSTELLATION_DATA_PATH, INDEX_PATH
    
    searcher = ConstellationSearcher(CONSTELLATION_DATA_PATH, INDEX_PATH)
    
    # テスト検索
    test_query = {
        "season": "冬",
        "months": [12, 1, 2],
        "keywords": ["冬", "寒い"],
        "constellation_hints": []
    }
    
    results = searcher.search(test_query)
    print("検索結果:")
    for constellation, score in results:
        print(f"  {constellation['jp_name']}: スコア {score}")
