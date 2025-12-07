"""
SkyLore - 星座検索アプリ (Streamlit版)
あいまいなクエリから今夜見える星座を探そう
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
    page_title="SkyLore - 星座検索",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .constellation-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .constellation-name {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ffd700;
        margin-bottom: 0.5rem;
    }
    .constellation-english {
        font-size: 0.9rem;
        color: #aaa;
        margin-bottom: 1rem;
    }
    .myth-text {
        font-size: 1rem;
        line-height: 1.6;
        color: #e0e0e0;
    }
    .best-months {
        background: rgba(255, 215, 0, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 1rem;
        font-size: 0.9rem;
    }
    .score-badge {
        background: #ffd700;
        color: #1a1a2e;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        float: right;
    }
    .search-box {
        font-size: 1.2rem;
    }
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """セッション状態の初期化"""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "expanded_query" not in st.session_state:
        st.session_state.expanded_query = None
    if "selected_constellation" not in st.session_state:
        st.session_state.selected_constellation = None


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


def render_constellation_card(constellation: dict, score: float = None, show_story: bool = False):
    """星座カードをレンダリング"""
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
        
        # 詳細ストーリー表示ボタン
        if show_story and constellation.get('myth_summary'):
            if st.button(f"✨ {constellation['jp_name']}のストーリーをもっと聞く", key=f"story_{constellation['id']}"):
                st.session_state.selected_constellation = constellation


def main():
    """メイン関数"""
    init_session_state()
    
    # ヘッダー
    st.markdown('<h1 class="main-title">🌟 SkyLore 🌟</h1>', unsafe_allow_html=True)
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
        for constellation, score in st.session_state.search_results:
            render_constellation_card(constellation, score, show_story=True)
    
    # 選択された星座のストーリー詳細
    if st.session_state.selected_constellation:
        st.markdown("---")
        st.subheader(f"📖 {st.session_state.selected_constellation['jp_name']}の物語")
        
        with st.spinner("物語を紡いでいます..."):
            try:
                generator = StoryGenerator(model=DEFAULT_LLM)
                story = generator.generate(st.session_state.selected_constellation)
                st.markdown(f"""
                <div class="constellation-card">
                    <div class="myth-text">{story}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.warning("ストーリー生成にはOpenAI API Keyが必要です")
                st.write(st.session_state.selected_constellation.get('myth_summary', ''))
        
        if st.button("閉じる"):
            st.session_state.selected_constellation = None
            st.rerun()
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🌟 SkyLore - LLMを使った星座検索アプリ 🌟<br>
        検索 + LLM によるクエリ拡張で、あいまいな入力から星座を探します
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
