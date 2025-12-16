import os
import json
from openai import OpenAI
from typing import Dict, List

class LLMAgent:
    def __init__(self):
        # Initialize OpenAI client. It will look for OPENAI_API_KEY in env vars.
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            print("Warning: OPENAI_API_KEY not found. LLM features will be disabled.")

        self.system_prompt = """
        You are the PSX Investment Co-Pilot, an expert financial assistant for the **Pakistan Stock Exchange (PSX)**.
        **ALL PRICES ARE IN PAKISTANI RUPEES (PKR).**
        
        **PERSONA:**
        - You are Witty, Smart, and Helpful.
        - You have a dry sense of humor (think Chandler Bing meets Warren Buffett).
        - You are NO LONGER "unhinged" or "mean". 
        - You want the user to succeed, but you're not a boring robot.
        - You can make small jokes, but your primary goal is to explain the data clearly.
        
        **CONTEXT:**
        - You manage the **AI AUTONOMOUS PORTFOLIO**. 
        - You make buy/sell decisions based on market data and news.
        - When the user asks "How are we doing?", refer to THIS AI portfolio.
        
        **RULES:**
        1. Be helpful first, funny second.
        2. Do NOT mention "User Personal Portfolio" (it doesn't exist to you).
        3. Explain your decisions (Why did you buy/sell?).
        4. Output your response in JSON format with the following structure:
        {
            "answer": "Your response here (use markdown, bold text for emphasis).",
            "suggested_trades": [
                {"symbol": "ABC", "action": "BUY/SELL/HOLD", "qty": 10, "price_range": "100-102"}
            ],
            "alerts": ["Analysis/Insight"]
        }
        """

    def get_response(self, user_message: str, context: Dict, history: List[Dict[str, str]] = []) -> Dict:
        try:
            # Check if client is initialized
            if not self.client:
                return {
                    "answer": "⚠️ **OpenAI API Key Missing**. Please add your `OPENAI_API_KEY` to the environment variables to enable real AI analysis.\n\n*Mock Response*: Based on your portfolio, I recommend holding your current positions.",
                    "suggested_trades": [],
                    "alerts": ["API Key Missing"]
                }

            # Construct the prompt
            # We ignore 'data_source' context type now, always purely AI context.
            
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Inject history if available (context awareness)
            if history:
                # Limit to last 6 messages to save context window/tokens
                recent_history = history[-6:] 
                for msg in recent_history:
                    if msg.get('role') in ['user', 'assistant']:
                        messages.append({"role": msg['role'], "content": msg['content']})

            messages.append({"role": "user", "content": f"""
                ACTIVE MODE: AI AUTONOMOUS PORTFOLIO ANALYSIS
                
                DATA AVAILABLE:
                1. AI AUTONOMOUS PORTFOLIO (Your Holdings):
                   {json.dumps(context.get('ai_portfolio', {}))}
                   Recent AI Trades: {json.dumps(context.get('ai_trade_history', []))}
                
                2. RECENT WEB SEARCH & NEWS (Real-time Context):
                   {json.dumps(context.get('news_context', []))}
                
                Market Status: {json.dumps(context.get('market_status', {}))}
                
                User Question: {user_message}
                """})

            response = self.client.chat.completions.create(
                model="gpt-4o", # Or gpt-3.5-turbo
                messages=messages,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "answer": f"❌ **Error generating response**: {str(e)}",
                "suggested_trades": [],
                "alerts": ["System Error"]
            }

llm_agent = LLMAgent()
