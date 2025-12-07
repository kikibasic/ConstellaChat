"""
SkyLore - クエリ拡張モジュール
Gen-QERの仕組みを参考に、LLMを使ってあいまいなクエリを拡張する
"""
import os
from openai import OpenAI

# プロンプトテンプレート
QUERY_EXPANSION_PROMPT = """あなたは星座検索システムのクエリ拡張アシスタントです。
ユーザーの入力から、星座検索に役立つキーワードを抽出・拡張してください。

## タスク
ユーザーの入力を分析し、以下の情報を推測してJSON形式で出力してください：

1. season: 推測される季節（春/夏/秋/冬）
2. months: 推測される月のリスト（1-12）
3. keywords: 検索に使うキーワードのリスト
4. constellation_hints: 言及されている星座名があれば

## ルール
- 気温から季節を推測（0-10度:冬、10-20度:春秋、20-30度:夏、30度以上:猛暑）
- 「寒い」「暑い」などの表現からも季節を推測
- 「冬の大三角」「夏の大三角」などの有名なアステリズムも考慮
- 日本の四季を基準にする

## 出力形式（JSON のみ、説明不要）
{
  "season": "冬",
  "months": [12, 1, 2],
  "keywords": ["冬", "寒い", "オリオン", "冬の大三角"],
  "constellation_hints": ["オリオン座"]
}

## ユーザー入力
"""

STORY_GENERATION_PROMPT = """あなたは星座の語り部です。
以下の星座について、神話や見どころを魅力的に紹介してください。

## 星座情報
{constellation_data}

## ルール
- 200文字程度で簡潔に
- 神話のエッセンスを伝える
- 関連する星座があれば言及する
- 親しみやすい語り口で

## 出力
"""


class QueryExpander:
    """LLMを使ったクエリ拡張クラス"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def expand(self, query: str) -> dict:
        """
        ユーザークエリを拡張する
        
        Args:
            query: ユーザーの入力（例：「冬の寒い日、最高気温10度くらい」）
        
        Returns:
            拡張された検索情報を含む辞書
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは星座検索のクエリ拡張アシスタントです。JSONのみを出力してください。"},
                    {"role": "user", "content": QUERY_EXPANSION_PROMPT + query}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"クエリ拡張エラー: {e}")
            # フォールバック: 基本的なキーワード抽出
            return self._fallback_expand(query)
    
    def _fallback_expand(self, query: str) -> dict:
        """APIエラー時のフォールバック処理"""
        keywords = []
        season = None
        months = []
        
        # 季節キーワードの検出
        if any(w in query for w in ["冬", "寒い", "冷たい"]):
            season = "冬"
            months = [12, 1, 2]
            keywords.extend(["冬", "寒い"])
        elif any(w in query for w in ["夏", "暑い", "熱い"]):
            season = "夏"
            months = [6, 7, 8]
            keywords.extend(["夏", "暑い"])
        elif any(w in query for w in ["春", "暖かい", "桜"]):
            season = "春"
            months = [3, 4, 5]
            keywords.extend(["春", "暖かい"])
        elif any(w in query for w in ["秋", "涼しい", "紅葉"]):
            season = "秋"
            months = [9, 10, 11]
            keywords.extend(["秋", "涼しい"])
        
        # 気温からの推測
        import re
        temp_match = re.search(r'(\d+)度', query)
        if temp_match:
            temp = int(temp_match.group(1))
            if temp <= 10:
                season = "冬"
                months = [12, 1, 2]
            elif temp <= 20:
                season = "春秋"
                months = [3, 4, 5, 9, 10, 11]
            else:
                season = "夏"
                months = [6, 7, 8]
        
        return {
            "season": season,
            "months": months,
            "keywords": keywords,
            "constellation_hints": []
        }


class StoryGenerator:
    """星座のストーリーを生成するクラス"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate(self, constellation_data: dict, related_constellations: list = None) -> str:
        """
        星座のストーリーを生成する
        
        Args:
            constellation_data: 星座の情報
            related_constellations: 関連する星座のリスト
        
        Returns:
            生成されたストーリー文字列
        """
        # 既存の神話がある場合はそれをベースに
        if constellation_data.get("myth_summary"):
            base_story = constellation_data["myth_summary"]
        else:
            base_story = f"{constellation_data['jp_name']}の星座です。"
        
        # 関連星座の情報を追加
        context = f"""
星座名: {constellation_data['jp_name']}
英語名: {constellation_data['id']}
神話: {base_story}
見頃の月: {constellation_data.get('best_months', [])}
"""
        if related_constellations:
            context += f"関連星座: {', '.join(related_constellations)}\n"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは星座の魅力を伝える語り部です。"},
                    {"role": "user", "content": STORY_GENERATION_PROMPT.format(constellation_data=context)}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"ストーリー生成エラー: {e}")
            return base_story


# テスト用
if __name__ == "__main__":
    expander = QueryExpander()
    
    test_queries = [
        "冬の寒い日、最高気温10度くらい",
        "夏の暑い夜に見える星座は？",
        "オリオン座が見たい",
        "今日は涼しくて過ごしやすい"
    ]
    
    for query in test_queries:
        print(f"\n入力: {query}")
        result = expander.expand(query)
        print(f"拡張結果: {result}")
