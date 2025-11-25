from ddgs import DDGS
from llm_agent import llm_agent
from datetime import datetime
import json

class NewsAgent:
    def __init__(self):
        self.ddgs = DDGS()

    def fetch_market_news(self, query="PSX Pakistan Stock Exchange market news"):
        """Fetches latest news using DuckDuckGo."""
        try:
            results = self.ddgs.text(query, max_results=5)
            return results
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def analyze_news(self, news_items):
        """Uses LLM to analyze news and generate trade signals."""
        if not news_items:
            return []

        news_text = "\n".join([f"- {item['title']}: {item['body']} ({item['href']})" for item in news_items])
        
        prompt = f"""
        You are an expert financial analyst for the Pakistan Stock Exchange (PSX).
        Analyze the following news headlines and summaries:
        
        {news_text}
        
        Identify any specific stocks or sectors that are likely to be significantly impacted (Positive or Negative).
        Ignore general market noise. Focus on actionable insights.
        
        Return a JSON object with a single key "alerts" containing a list of alerts. Format:
        {{
            "alerts": [
                {{
                    "symbol": "OGDC",
                    "signal": "BUY",
                    "reason": "Oil prices surged globally.",
                    "url": "http://example.com/news-link"
                }}
            ]
        }}
        If no actionable insights, return {{"alerts": []}}.
        """
        
        if not llm_agent.client:
            print("Warning: No LLM client available.")
            return []

        messages = [
            {"role": "system", "content": "You are a financial news analyst. Return a JSON list of alerts."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = llm_agent.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            return data.get("alerts", [])
        except Exception as e:
            print(f"Error analyzing news: {e}")
            return []

news_agent = NewsAgent()
