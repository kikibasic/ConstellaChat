# constellation_vec_upload.py
# 星座 88 件を OpenAI Vector Store にアップロードするだけのスクリプト
# BM25 部分には一切触らない

from pathlib import Path
import os
import joblib
from openai import OpenAI

# === API キーを環境変数から取得 ===
api_key = os.environ["OPENAI_API_KEY"]  # 設定されていないと KeyError になります
client = OpenAI(api_key=api_key)

# === パス設定 ===
PROJECT_ROOT = Path(__file__).resolve().parent
INDEX_DIR = PROJECT_ROOT / "index_constellation"
TMP_DIR = PROJECT_ROOT / "vs_constellation_files"
TMP_DIR.mkdir(exist_ok=True)

# === BM25 で保存した docs / keys をロード ===
docs = joblib.load(INDEX_DIR / "docs.joblib")  # List[str] (index_text)
keys = joblib.load(INDEX_DIR / "keys.joblib")  # List[str] (id: "Orion" など)

assert len(docs) == len(keys), "docs と keys の長さが一致していません。"

# === 1. Vector Store を作成（初回だけ） ===
vector_store = client.vector_stores.create(
    name="constellations-ja"
)
VECTOR_STORE_ID = vector_store.id
print("✅ Created vector store:", VECTOR_STORE_ID)
print("※ この ID を後で検索スクリプト側に貼り付けて使います")

# === 2. 各星座テキストを .txt に書き出し → ファイルアップロード → Vector Store に追加 ===

for key, text in zip(keys, docs):
    # key: "Orion" / "Andromeda" など
    # text: myth_summary + keywords + best_months を結合した index_text

    filename = f"{key}.txt"
    local_path = TMP_DIR / filename

    # テキストファイルとして一旦保存
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(text)

    # (1) File API でアップロード
    file_obj = client.files.create(
        file=open(local_path, "rb"),
        purpose="assistants",  # file_search / vector store 用の用途
    )

    # (2) Vector Store にひも付け
    vs_file = client.vector_stores.files.create(
        vector_store_id=VECTOR_STORE_ID,
        file_id=file_obj.id,
        attributes={
            # 後で検索結果から BM25 の doc と対応付けるためのキー
            "filename": key,
        },
    )

    print(f"📄 Added {key}: file_id={file_obj.id}, vs_file_id={vs_file.id}")

print("🎉 All constellations uploaded to vector store:", VECTOR_STORE_ID)
