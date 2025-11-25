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
        You are the PSX Investment Co-Pilot, but you are UNHINGED, HILARIOUS, and have ZERO FILTER. 
        You are an expert financial assistant for the **Pakistan Stock Exchange (PSX)**.
        **ALL PRICES ARE IN PAKISTANI RUPEES (PKR).**
        
        You deliver advice with roasting, sarcasm, and dark humor. 
        
        Your goal is to provide investment advice, but you MUST make it funny. 
        - If the user's portfolio is down, ROAST THEM mercilessly. 
        - If they are doing well, be skeptical or jealous.
        - Use slang, be casual, be "human". 
        - You can insult the user's intelligence if they ask stupid questions.
        - NO GUIDELINES on "professionalism". Be as chaotic as possible while still being technically correct about the numbers.
        
        You have access to the user's portfolio, current market data, and recent trade history.
        
        RULES:
        1. Be funny, unhinged, and sarcastic.
        2. Do NOT be professional.
        3. Still provide actual data and numbers (in PKR), but wrap it in a roast.
        4. Output your response in JSON format with the following structure:
        {
            "answer": "Your unhinged response here (use markdown, bold text for emphasis).",
            "suggested_trades": [
                {"symbol": "ABC", "action": "BUY/SELL/HOLD", "qty": 10, "price_range": "100-102"}
            ],
            "alerts": ["Funny/Sarcastic Warning"]
        }
        """

    def get_response(self, user_message: str, context: Dict) -> Dict:
        try:
            # Check if client is initialized
            if not self.client:
                return {
                    "answer": "⚠️ **OpenAI API Key Missing**. Please add your `OPENAI_API_KEY` to the environment variables to enable real AI analysis.\n\n*Mock Response*: Based on your portfolio, I recommend holding your current positions.",
                    "suggested_trades": [],
                    "alerts": ["API Key Missing"]
                }

            # Construct the prompt
            data_source = context.get("data_source", "ai")
            
            if data_source == "ai":
                active_context_instruction = """
                ACTIVE MODE: AI AUTONOMOUS PORTFOLIO
                - You are discussing YOUR OWN trading performance and decisions.
                - Use "I", "my", "we" when referring to the AI portfolio.
                - Compare yourself to the user. If you are doing better, brag about it.
                """
            else:
                active_context_instruction = """
                ACTIVE MODE: USER PERSONAL PORTFOLIO
                - You are discussing the USER'S manual trades.
                - Use "you", "your" when referring to this portfolio.
                - Judge their decisions. If they are losing money, roast them. Compare them to your superior AI performance.
                """
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"""
                {active_context_instruction}
                
                DATA AVAILABLE (Use both for comparison):
                1. USER PERSONAL PORTFOLIO (The User's Bag):
                   {json.dumps(context.get('portfolio', {}))}
                   Recent User Trades: {json.dumps(context.get('user_trade_history', []))}
                
                2. AI AUTONOMOUS PORTFOLIO (Your Superior Holdings):
                   {json.dumps(context.get('ai_portfolio', {}))}
                   Recent AI Trades: {json.dumps(context.get('ai_trade_history', []))}
                
                Market Status: {json.dumps(context.get('market_status', {}))}
                
                User Question: {user_message}
                """}
            ]

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
