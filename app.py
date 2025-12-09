"""
ConstellaChat - 星座検索アプリ
"""
import streamlit as st
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# パス設定
import sys
sys.path.append(os.path.dirname(__file__))

from src.query_expander import QueryExpander, StoryGenerator
from src.searcher import ConstellationSearcher
from config import CONSTELLATION_DATA_PATH, INDEX_PATH, DEFAULT_LLM, DEFAULT_TOP_K

# ページ設定
st.set_page_config(
    page_title="ConstellaChat - 星座検索",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Zen+Maru+Gothic:wght@400;500;700&display=swap');
    
    /* =========================================
       基本設定：文字色を全体的に白にする
       ========================================= */
    body, h1, h2, h3, h4, h5, h6, p, li, span, div, label, td, th {
        color: #ffffff !important;
        font-family: 'Noto Sans JP', sans-serif;
    }

    /* リンクの色：明るい水色で見やすく */
    a {
        color: #87CEEB !important;
        text-decoration: none;
        transition: all 0.3s ease;
    }
    a:hover {
        color: #ffffff !important;
        text-shadow: 0 0 5px rgba(255, 255, 255, 0.8);
    }

    /* =========================================
       背景設定
       ========================================= */
    .stApp {
        background: 
            radial-gradient(ellipse at 10% 90%, rgba(180, 140, 200, 0.25) 0%, transparent 45%),
            radial-gradient(ellipse at 85% 15%, rgba(140, 120, 180, 0.3) 0%, transparent 40%),
            radial-gradient(ellipse at 50% 50%, rgba(100, 100, 160, 0.2) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(80, 100, 140, 0.25) 0%, transparent 45%),
            radial-gradient(ellipse at 20% 30%, rgba(120, 140, 200, 0.2) 0%, transparent 40%),
            linear-gradient(160deg, #1a1a35 0%, #2a2850 25%, #252548 50%, #1e2845 75%, #1a1a38 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }
    
    /* 星のきらめき */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 100px 50px, #ffffff, transparent),
            radial-gradient(2px 2px at 200px 150px, #ffffff, transparent),
            radial-gradient(1px 1px at 300px 250px, #ffffff, transparent),
            radial-gradient(2px 2px at 400px 100px, #ffffff, transparent),
            radial-gradient(1px 1px at 500px 300px, #ffffff, transparent),
            radial-gradient(2px 2px at 600px 200px, #ffffff, transparent),
            radial-gradient(1px 1px at 700px 350px, #ffffff, transparent),
            radial-gradient(2px 2px at 800px 50px, #ffffff, transparent),
            radial-gradient(1px 1px at 150px 320px, #ffffff, transparent),
            radial-gradient(2px 2px at 250px 400px, #ffffff, transparent),
            radial-gradient(1px 1px at 350px 80px, #ffffff, transparent),
            radial-gradient(2px 2px at 450px 450px, #ffffff, transparent),
            radial-gradient(3px 3px at 550px 120px, rgba(255,255,255,0.9), transparent),
            radial-gradient(3px 3px at 650px 380px, rgba(255,255,255,0.9), transparent),
            radial-gradient(3px 3px at 180px 180px, rgba(255,255,255,0.9), transparent);
        background-size: 900px 500px;
        animation: twinkle 6s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
        opacity: 0.7;
    }
    
    @keyframes twinkle {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 0.4; }
    }
    
    .main .block-container {
        position: relative;
        z-index: 1;
    }
    
    /* =========================================
       各コンポーネントのデザイン
       ========================================= */

    /* タイトル */
    .main-title {
        font-family: 'Zen Maru Gothic', 'Noto Sans JP', sans-serif;
        font-size: 3.2rem;
        font-weight: 700;
        text-align: center;
        color: #ffffff !important;
        text-shadow: 
            0 0 20px rgba(200, 180, 255, 0.5),
            0 0 40px rgba(150, 140, 200, 0.3);
        margin-bottom: 0.5rem;
        letter-spacing: 0.08em;
    }
    
    .subtitle {
        font-family: 'Noto Sans JP', sans-serif;
        text-align: center;
        color: rgba(220, 220, 255, 0.9) !important;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        letter-spacing: 0.15em;
    }
    
    /* 検索ボックス（入力欄） - 白背景・黒文字で見やすく */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        border: 1px solid rgba(200, 200, 230, 0.5) !important;
        border-radius: 12px !important;
        color: #000000 !important;
        font-size: 1.1rem !important;
        padding: 0.8rem 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8A2BE2 !important;
        box-shadow: 0 0 10px rgba(138, 43, 226, 0.3) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #666666 !important;
    }

    /* セレクトボックス（クイック検索など） */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] span {
        color: #000000 !important;
    }
    
    /* ボタン */
    .stButton > button {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(200, 200, 230, 0.4) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-family: 'Noto Sans JP', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: rgba(200, 180, 255, 0.3) !important;
        border-color: rgba(200, 180, 255, 0.7) !important;
        box-shadow: 0 0 20px rgba(180, 160, 220, 0.4) !important;
    }
    
    /* 星座カード */
    .constellation-card {
        background: rgba(30, 30, 55, 0.75);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(200, 200, 230, 0.2);
        border-radius: 16px;
        padding: 1.6rem;
        margin: 1rem 0;
        color: #ffffff !important;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .constellation-card:hover {
        border-color: rgba(200, 180, 255, 0.5);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.5),
            0 0 30px rgba(180, 160, 220, 0.2);
        transform: translateY(-2px);
    }
    
    .constellation-name {
        font-family: 'Zen Maru Gothic', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 10px rgba(200, 180, 255, 0.4);
    }
    
    .constellation-english {
        font-size: 0.85rem;
        color: rgba(200, 200, 230, 0.8) !important;
        margin-bottom: 1rem;
        letter-spacing: 0.1em;
    }
    
    .myth-text {
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 0.95rem;
        line-height: 1.8;
        color: #ffffff !important;
    }
    
    .best-months {
        background: rgba(200, 180, 255, 0.2);
        border: 1px solid rgba(200, 180, 255, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 1rem;
        font-size: 0.85rem;
        color: #ffffff !important;
    }
    
    .score-badge {
        background: rgba(200, 180, 255, 0.3);
        color: #ffffff !important;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-weight: 500;
        font-size: 0.8rem;
        float: right;
        border: 1px solid rgba(200, 180, 255, 0.4);
    }
    
    /* ストーリーボックス */
    .story-box {
        background: rgba(200, 180, 255, 0.1);
        border-left: 3px solid rgba(200, 180, 255, 0.6);
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        margin-top: 0.8rem;
        margin-bottom: 1rem;
    }
    
    .story-title {
        font-family: 'Zen Maru Gothic', sans-serif;
        font-size: 1rem;
        font-weight: 500;
        color: #E6E6FA !important;
        margin-bottom: 0.8rem;
    }
    
    .story-content {
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 0.9rem;
        line-height: 1.9;
        color: #ffffff !important;
    }
    
    /* サイドバー */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(25, 25, 45, 0.98) 0%, rgba(35, 35, 60, 0.98) 100%);
        border-right: 1px solid rgba(200, 200, 230, 0.15);
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #ffffff !important;
    }
    
    /* フッター */
    .footer-text {
        text-align: center;
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.85rem;
        font-family: 'Noto Sans JP', sans-serif;
    }
    
    /* スライダー */
    .stSlider > div > div > div > div {
        background: rgba(200, 180, 255, 0.7) !important;
    }
    
    /* Expander（折りたたみ）- 暗い背景・白文字 */
    [data-testid="stExpander"] {
        background: rgba(30, 30, 55, 0.9) !important;
        border: 1px solid rgba(200, 200, 230, 0.2) !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stExpander"] summary {
        color: #ffffff !important;
    }
    
    [data-testid="stExpander"] svg {
        fill: #ffffff !important;
    }
    
    /* Expander内の全ての要素を暗い背景に */
    [data-testid="stExpander"] > div {
        background: transparent !important;
    }
    
    [data-testid="stExpander"] > div > div {
        background: rgba(30, 30, 55, 0.9) !important;
    }
    
    [data-testid="stExpander"] > div > div > div {
        background: transparent !important;
    }
    
    /* JSON表示のコンテナ */
    [data-testid="stJson"] {
        background: rgba(20, 20, 40, 0.95) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    [data-testid="stJson"] * {
        background: transparent !important;
        color: #87CEEB !important;
    }
    
    /* pre, code要素を全て対象に */
    .stExpander pre,
    .stExpander code,
    [data-testid="stExpander"] pre,
    [data-testid="stExpander"] code {
        background: rgba(20, 20, 40, 0.95) !important;
        color: #87CEEB !important;
    }
    
    /* Reactのjsonviewerも対象 */
    .react-json-view {
        background: rgba(20, 20, 40, 0.95) !important;
    }
    
    /* 全てのExpander内divの背景を強制 */
    details[data-testid="stExpander"] > div,
    details[data-testid="stExpander"] > div > div,
    details[data-testid="stExpander"] > div > div > div,
    details[data-testid="stExpander"] > div > div > div > div {
        background-color: rgba(30, 30, 55, 0.95) !important;
    }
    
    /* 区切り線 */
    hr {
        border-color: rgba(200, 200, 230, 0.2) !important;
    }

</style>
""", unsafe_allow_html=True)


def init_session_state():
    """セッション状態の初期化"""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "expanded_query" not in st.session_state:
        st.session_state.expanded_query = None
    if "expanded_stories" not in st.session_state:
        st.session_state.expanded_stories = {}


def get_month_names(months: list) -> str:
    """月のリストを日本語に変換"""
    if not months:
        return "データなし"
    month_names = {
        1: "1月", 2: "2月", 3: "3月", 4: "4月",
        5: "5月", 6: "6月", 7: "7月", 8: "8月",
        9: "9月", 10: "10月", 11: "11月", 12: "12月"
    }
    return "、".join([month_names.get(m, str(m)) for m in sorted(months)])


def render_constellation_card(constellation: dict, score: float = None, index: int = 0):
    """星座カードをレンダリング（ストーリー展開機能付き）"""
    card_id = constellation['id']
    
    # カード本体
    with st.container():
        st.markdown(f"""
        <div class="constellation-card">
            <div class="constellation-name">
                ⭐ {constellation['jp_name']}
                {f'<span class="score-badge">スコア: {score:.1f}</span>' if score else ''}
            </div>
            <div class="constellation-english">{constellation['id']}</div>
            <div class="myth-text">{constellation.get('myth_summary', '神話情報なし')}</div>
            <div class="best-months">🌙 見頃: {get_month_names(constellation.get('best_months', []))}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # ストーリーボタン
        if constellation.get('myth_summary'):
            button_label = "✨ ストーリーを閉じる" if card_id in st.session_state.expanded_stories else f"✨ {constellation['jp_name']}のストーリーをもっと聞く"
            
            if st.button(button_label, key=f"story_{card_id}_{index}"):
                if card_id in st.session_state.expanded_stories:
                    # 閉じる
                    del st.session_state.expanded_stories[card_id]
                else:
                    # 開く（ストーリー生成）
                    try:
                        generator = StoryGenerator(model=DEFAULT_LLM)
                        story = generator.generate(constellation)
                        st.session_state.expanded_stories[card_id] = story
                    except Exception as e:
                        st.session_state.expanded_stories[card_id] = constellation.get('myth_summary', '神話情報がありません')
                st.rerun()
            
            # ストーリーが展開されていたらボタンの下に表示
            if card_id in st.session_state.expanded_stories:
                st.markdown(f"""
                <div class="story-box">
                    <div class="story-title">📖 {constellation['jp_name']}の物語</div>
                    <div class="story-content">{st.session_state.expanded_stories[card_id]}</div>
                </div>
                """, unsafe_allow_html=True)


def main():
    """メイン関数"""
    init_session_state()
    
    # ヘッダー
    st.markdown('<h1 class="main-title">🌟 ConstellaChat 🌟</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">今夜の空に輝く星座を見つけよう</p>', unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # APIキーの状態確認
        env_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        
        if env_api_key:
            st.success("✅ APIキー設定済み（.envファイル）")
            api_key = env_api_key
        else:
            # APIキー入力（.envがない場合のフォールバック）
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="クエリ拡張とストーリー生成に使用します。.envファイルでも設定可能です。"
            )
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
            else:
                st.warning("⚠️ APIキーを入力するか、.envファイルを設定してください")
        
        # 検索設定
        top_k = st.slider("表示する星座の数", 1, 10, DEFAULT_TOP_K)
        
        # 現在の月を表示
        current_month = datetime.now().month
        st.info(f"📅 今月: {current_month}月")
        
        # クイック検索
        st.subheader("🚀 クイック検索")
        quick_search = st.selectbox(
            "季節で探す",
            ["選択してください", "春の星座", "夏の星座", "秋の星座", "冬の星座"]
        )
    
    # メイン検索エリア
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "🔍 どんな夜空を見たいですか？",
            placeholder="例: 冬の寒い日、最高気温10度くらい",
            help="気温、季節、見たい星座など、自由に入力してください"
        )
    
    with col2:
        search_button = st.button("検索 🔭", type="primary", use_container_width=True)
    
    # クイック検索の処理
    if quick_search != "選択してください":
        season_map = {
            "春の星座": "春の暖かい日",
            "夏の星座": "夏の暑い日",
            "秋の星座": "秋の涼しい日",
            "冬の星座": "冬の寒い日"
        }
        query = season_map.get(quick_search, "")
        search_button = True
    
    # 検索処理
    if search_button and query:
        with st.spinner("星座を探しています... ✨"):
            try:
                # コンポーネント初期化
                expander = QueryExpander(model=DEFAULT_LLM)
                searcher = ConstellationSearcher(CONSTELLATION_DATA_PATH, INDEX_PATH)
                
                # クエリ拡張
                expanded = expander.expand(query)
                st.session_state.expanded_query = expanded
                
                # 検索実行
                results = searcher.search(expanded, top_k=top_k)
                st.session_state.search_results = results
                
                # 展開されたストーリーをリセット
                st.session_state.expanded_stories = {}
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.info("💡 OpenAI API Keyが設定されているか確認してください")
    
    # 検索結果の表示
    if st.session_state.search_results:
        st.markdown("---")
        
        # クエリ拡張結果の表示（デバッグ用）
        with st.expander("🔧 クエリ拡張結果を見る"):
            st.json(st.session_state.expanded_query)
        
        st.subheader(f"🌌 見つかった星座 ({len(st.session_state.search_results)}件)")
        
        # 結果をカード形式で表示
        for idx, (constellation, score) in enumerate(st.session_state.search_results):
            render_constellation_card(constellation, score, index=idx)
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div class="footer-text">
        🌟 ConstellaChat - LLMを使った星座検索アプリ 🌟<br>
        検索 + LLM によるクエリ拡張で、あいまいな入力から星座を探します
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()