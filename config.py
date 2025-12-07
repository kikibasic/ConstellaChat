"""
SkyLore - 設定ファイル
"""
import os
import argparse
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# OpenAI API設定（OPENAI_API_KEY または OPENAI_KEY のどちらでも対応）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY", "")

# デフォルト設定
DEFAULT_LLM = "gpt-4o-mini"
DEFAULT_TOP_K = 5  # 検索結果の上位K件

# ファイルパス
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CONSTELLATION_DATA_PATH = os.path.join(DATA_DIR, "constellations.json")
INDEX_PATH = os.path.join(DATA_DIR, "inverted_index.json")

# 月と季節のマッピング
MONTH_TO_SEASON = {
    1: "冬", 2: "冬", 3: "春",
    4: "春", 5: "春", 6: "夏",
    7: "夏", 8: "夏", 9: "秋",
    10: "秋", 11: "秋", 12: "冬"
}

SEASON_TO_MONTHS = {
    "春": [3, 4, 5],
    "夏": [6, 7, 8],
    "秋": [9, 10, 11],
    "冬": [12, 1, 2]
}

# 気温と季節の目安（日本基準）
TEMP_TO_SEASON = {
    (None, 10): "冬",
    (10, 20): "春秋",
    (20, 30): "夏",
    (30, None): "夏"
}


def get_args():
    """コマンドライン引数を取得"""
    parser = argparse.ArgumentParser(description="SkyLore - 星座検索アプリ")
    parser.add_argument("--llm", type=str, default=DEFAULT_LLM,
                        help="使用するLLMモデル")
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOP_K,
                        help="表示する星座の数")
    parser.add_argument("--debug", action="store_true",
                        help="デバッグモード")
    return parser.parse_args()
