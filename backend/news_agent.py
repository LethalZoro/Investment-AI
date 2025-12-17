from duckduckgo_search import DDGS
from llm_agent import llm_agent
from datetime import datetime
import json

class NewsAgent:
    def __init__(self):
        self.ddgs = DDGS()

    def fetch_market_news(self, query="PSX Pakistan Stock Exchange market news"):
        """Fetches latest news using multiple query variations for broader coverage."""
        
        # Generate query variations
        queries = [query]
        
        # If generic query, expand to specific categories
        if "PSX" in query and "Pakistan" in query:
            queries = [
                "Pakistan Stock Exchange breaking news companies",
                "PSX listed companies financial results announcements",
                "Pakistan business news economy updates",
                "KSE100 market sentiment analysis"
            ]
        # If specific symbol query (heuristic), add specific variations
        elif "stock" in query.lower():
            base_q = query.replace(" stock news", "").replace(" Pakistan Stock Exchange", "")
            queries.append(f"{base_q} financial results report")
            queries.append(f"{base_q} company announcement Pakistan")

        print(f"[NEWS AGENT] running queries: {queries}")
        
        all_results = []
        seen_urls = set()
        
        for q in queries:
            try:
                # Fetch fewer results per query to avoid rate limits/noise, but aggregate them
                # Use timelimit='w' (week) to ensure news is recent
                results = self.ddgs.text(q, max_results=20, timelimit="w") 
                if results:
                    for res in results:
                        if res.get('href') not in seen_urls:
                            all_results.append(res)
                            seen_urls.add(res.get('href'))
            except Exception as e:
                print(f"Error fetching news for '{q}': {e}")
                
        return all_results

    def search_web(self, query: str, limit: int = 5):
        """Perform a direct web search for specific user queries."""
        try:
            print(f"[NEWS AGENT] Searching web for: {query}")
            results = self.ddgs.text(query, max_results=limit, timelimit="w")
            return results if results else []
        except Exception as e:
            print(f"Error searching web: {e}")
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
        
        Identify any specific stocks (companies) that are likely to be significantly impacted.
        
        CRITICAL INSTRUCTIONS:
        1. Ignore general market indices like "KSE100", "KSE-100", "PSX", "All Share".
        2. Look for specific company names and their corresponding stock symbols (e.g., "SYS" for Systems Ltd, "OGDC" for OGDCL, "TRG" for TRG Pakistan).
        3. Only return alerts for specific TRADABLE stocks.
        
        Return a JSON object with a single key "alerts" containing a list of alerts. Format:
        {{
            "alerts": [
                {{
                    "symbol": "OGDC",
                    "signal": "BUY",
                    "reason": "Oil prices surged globally, positive impact expected.",
                    "url": "http://example.com/news-link"
                }}
            ]
        }}
        If no actionable insights for specific companies, return {{"alerts": []}}.
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

    def get_sentiment_score(self, query: str) -> dict:
        """
        Fetches news for a query and uses LLM to determine a sentiment score (-1.0 to +1.0).
        Returns: {"score": float, "summary": str}
        """
        print(f"[NEWS AGENT] Analyzing sentiment for: {query}")
        
        # 1. Fetch News
        results = self.search_web(f"{query} Pakistan Stock Exchange news", limit=5)
        if not results:
            print(f"[NEWS AGENT] No news found for {query}")
            return {"score": 0.0, "summary": "No recent news found."}
            
        news_text = "\n".join([f"- {item['title']} ({item['body']})" for item in results])
        
        # 2. Analyze with LLM
        prompt = f"""
        Analyze the sentiment of the following news regarding '{query}' in the context of the Pakistan Stock Exchange.
        
        News:
        {news_text}
        
        Determine a "Sentiment Score" from -1.0 (Very Negative/Bearish) to +1.0 (Very Positive/Bullish). 0.0 is Neutral.
        Also provide a 1-sentence summary of WHY.
        
        Return JSON: {{"score": float, "summary": "string"}}
        """
        
        messages = [
            {"role": "system", "content": "You are a financial sentiment analyzer. Return JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            if not llm_agent.client: return {"score": 0.0, "summary": "LLM invalid"}
            
            response = llm_agent.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            score = float(data.get("score", 0.0))
            summary = data.get("summary", "Neutral")
            
            print(f"[NEWS AGENT] {query} -> Score: {score} ({summary})")
            return {"score": score, "summary": summary}
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {"score": 0.0, "summary": "Error analyzing news"}

news_agent = NewsAgent()
