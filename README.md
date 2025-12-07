# 🌟 ConstellaChat - 星座検索アプリ
# 🌟 ConstellaChat - 星座検索アプリ

LLMを使ったクエリ拡張で、あいまいな入力から今夜見える星座を探すアプリです。

## 機能

- **あいまい検索**: 「冬の寒い日、最高気温10度くらい」のような自然な入力から星座を検索
- **LLMクエリ拡張**: GPT-4oを使って入力を解析し、検索キーワードを拡張
- **転置インデックス検索**: 高速な星座検索
- **神話ストーリー**: 星座にまつわる神話を表示

## セットアップ

### 1. 必要環境

- Python 3.10以上
- OpenAI API Key

### 2. インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/skylore.git
cd skylore

# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
# .env.exampleをコピーして.envを作成
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# OPENAI_API_KEY=your-api-key-here
```

**注意**: `.env`ファイルはGitにコミットしないでください（.gitignoreに含まれています）

### 4. 実行

```bash
streamlit run app.py
```

## プロジェクト構造

```
ConstellaChat/
├── app.py                    # Streamlitメインアプリ
├── config.py                 # 設定ファイル
├── requirements.txt          # 依存パッケージ
├── src/
│   ├── __init__.py
│   ├── query_expander.py     # LLMクエリ拡張
│   └── searcher.py           # 転置インデックス検索
└── data/
    ├── constellations.json   # 星座データ（要作成）
    └── inverted_index.json   # 転置インデックス（要作成）
```

## 担当分担

| 担当者 | タスク |
|--------|--------|
| さり | 星座データ (`constellations.json`) の作成 |
| さり | 転置インデックス (`inverted_index.json`) の構築 |
| あいら | アプリのメインロジック（このリポジトリ） |

## 星座データのフォーマット

`data/constellations.json` は以下の形式で作成：

```json
[
    {
        "id": "Orion",
        "jp_name": "オリオン座",
        "myth_summary": "狩人オリオンの神話...",
        "best_months": [11, 12, 1, 2, 3],
        "keywords": ["冬", "狩人", "ベテルギウス", "冬の大三角"],
        "related": ["Scorpius", "Canis Major"]
    }
]
```

## 転置インデックスのフォーマット

`data/inverted_index.json` は以下の形式で作成：

```json
{
    "冬": ["Orion", "Gemini", "Taurus"],
    "12": ["Orion", "Andromeda"],
    "オリオン座": ["Orion"],
    "狩人": ["Orion"],
    "ゼウス": ["Taurus", "Cygnus", "Aquarius"]
}
```

## 使用例

### 入力例
- 「冬の寒い日、最高気温10度くらい」
- 「夏の暑い夜に見える星座は？」
- 「オリオン座について教えて」
- 「ギリシャ神話に出てくる星座」

### クエリ拡張の仕組み

1. ユーザー入力: 「冬の寒い日、最高気温10度くらい」
2. LLMが解析:
   - 季節: 冬
   - 月: [12, 1, 2]
   - キーワード: ["冬", "寒い"]
3. 転置インデックスで検索
4. スコアリングして上位K件を返す

## 技術スタック

- **フロントエンド**: Streamlit
- **LLM**: OpenAI GPT-4o-mini
- **検索**: 転置インデックス（BM25風スコアリング）

## ライセンス

MIT License

## 参考

- Gen-QER: https://github.com/kikibasic/Gen-QER
- MuGI論文: "Exploring the Best Practices of Query Expansion with Large Language Models"
