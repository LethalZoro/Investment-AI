from ddgs import DDGS
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

news_agent = NewsAgent()
