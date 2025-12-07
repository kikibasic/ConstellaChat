"""
転置インデックス構築スクリプト
※ これは友達が本格的なものを作るまでの仮実装です

友達へ：
このスクリプトを参考に、より本格的な転置インデックスを構築してください。
改善ポイント：
1. MeCabなどを使った形態素解析
2. TF-IDFやBM25によるスコアリング
3. 同義語辞書の追加
4. キーワードの重み付け
"""
import json
import os
from collections import defaultdict

# パス設定
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CONSTELLATION_PATH = os.path.join(DATA_DIR, "constellations.json")
INDEX_PATH = os.path.join(DATA_DIR, "inverted_index.json")

# 季節と月のマッピング
SEASON_MONTHS = {
    "春": [3, 4, 5],
    "夏": [6, 7, 8],
    "秋": [9, 10, 11],
    "冬": [12, 1, 2]
}

# 神話のキーワード（手動で定義）
MYTH_KEYWORDS = [
    "ゼウス", "ヘラ", "アポロン", "アルテミス", "ポセイドン", "ハデス",
    "ヘルクレス", "ペルセウス", "オリオン", "アンドロメダ",
    "勇者", "狩人", "怪物", "王", "王女", "神", "女神",
    "ヒドラ", "サソリ", "ライオン", "牡牛", "馬", "鳥", "魚",
    "愛", "戦い", "冒険", "神話", "伝説"
]

# 有名なアステリズム
ASTERISMS = {
    "冬の大三角": ["Orion", "Canis Major", "Canis Minor"],
    "夏の大三角": ["Lyra", "Cygnus", "Aquila"],
    "春の大三角": ["Leo", "Virgo", "Bootes"],
    "春の大曲線": ["UrsaMajor", "Bootes", "Virgo"],
}


def build_index():
    """転置インデックスを構築"""
    
    # 星座データを読み込み
    with open(CONSTELLATION_PATH, "r", encoding="utf-8") as f:
        constellations = json.load(f)
    
    index = defaultdict(list)
    
    for c in constellations:
        cid = c["id"]
        jp_name = c.get("jp_name", "")
        myth = c.get("myth_summary", "")
        best_months = c.get("best_months", [])
        keywords = c.get("keywords", [])
        
        # 1. 日本語名でインデックス
        if jp_name:
            index[jp_name].append(cid)
            # 「座」を除いた名前でも
            base_name = jp_name.replace("座", "")
            index[base_name].append(cid)
        
        # 2. 英語名でインデックス
        index[cid].append(cid)
        index[cid.lower()].append(cid)
        
        # 3. 月でインデックス
        for month in best_months:
            index[str(month)].append(cid)
            index[f"{month}月"].append(cid)
        
        # 4. 季節でインデックス
        for season, months in SEASON_MONTHS.items():
            if any(m in best_months for m in months):
                index[season].append(cid)
        
        # 5. 神話キーワードでインデックス
        for keyword in MYTH_KEYWORDS:
            if keyword in myth:
                index[keyword].append(cid)
        
        # 6. カスタムキーワードでインデックス
        for keyword in keywords:
            index[keyword].append(cid)
    
    # 7. アステリズムでインデックス
    for asterism, cids in ASTERISMS.items():
        for cid in cids:
            index[asterism].append(cid)
    
    # 重複を除去
    index = {k: list(set(v)) for k, v in index.items()}
    
    # インデックスを保存
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 転置インデックスを構築しました: {INDEX_PATH}")
    print(f"   - キーワード数: {len(index)}")
    print(f"   - 星座数: {len(constellations)}")
    
    # インデックスの統計情報
    print("\n📊 インデックス統計:")
    season_counts = {s: len(index.get(s, [])) for s in ["春", "夏", "秋", "冬"]}
    for season, count in season_counts.items():
        print(f"   {season}: {count}星座")


if __name__ == "__main__":
    build_index()
