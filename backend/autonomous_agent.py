import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict
from openai import OpenAI

from models import UserSettings, DailyPlan, PortfolioItem, AIAlert, AIPortfolioItem, AINotification, AITradeHistory
from market_data import market_data
from news_agent import news_agent
from portfolio_engine import PortfolioEngine
from budget_engine import BudgetEngine
from risk_engine import RiskEngine
from strategy_engine import StrategyEngine

class AutonomousAgent:
    def __init__(self, db: Session):
        self.db = db
        self.budget_engine = BudgetEngine(db)
        self.portfolio_engine = PortfolioEngine(db) # Still useful for user portfolio, but we need AI specific logic
        self.strategy_engine = StrategyEngine()
        
        # Initialize OpenAI client for GPT-driven decisions
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
            print("Warning: OPENAI_API_KEY not found. GPT decision-making will be disabled.")


    def run_trading_cycle(self):
        """
        Executes the full AI trading cycle:
        1. Analyze News & Market (Signal Generation)
        2. Monitor Existing Portfolio (Stop Loss/Take Profit)
        3. Execute New Trades (Buy/Sell based on signals)
        """
        notifications = []

        # 1. Get Settings & Check Trading Hours
        settings = self.db.query(UserSettings).first()
        if not settings:
            settings = UserSettings()
            self.db.add(settings)
            self.db.commit()
            
        # Check Trading Hours
        now = datetime.now().strftime("%H:%M")
        start_time = settings.trading_start_time or "09:30"
        end_time = settings.trading_end_time or "15:30"
        
        if not (start_time <= now <= end_time):
            print(f"[TRADING CYCLE] Skipping: Current time {now} is outside trading hours ({start_time} - {end_time})")
            return []

        # 2. Monitor Existing Portfolio
        self.monitor_portfolio(notifications)
        
        current_budget = settings.ai_cash_balance
        
        # 3. Broad Market Scan (News + Market Data)
        # Search for potential candidates
        candidates = self._scan_market_candidates()
        
        # 4. Analyze Candidates
        for symbol in candidates:
            # Check if we already hold it
            existing = self.db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == symbol).first()
            if existing: continue
            
            # Analyze News for this specific stock
            news = news_agent.fetch_market_news(f"{symbol} stock news Pakistan Stock Exchange")
            analysis = news_agent.analyze_news(news)
            
            # If analysis returns a BUY signal
            for alert in analysis:
                if alert.get('signal') == 'BUY' and alert.get('symbol') == symbol:
                     self._evaluate_and_trade(
                         {"symbol": symbol, "price": market_data.get_live_price(symbol)}, 
                         "BUY", 
                         f"News Sentiment: {alert.get('reason')}", 
                         settings, 
                         notifications
                     )

        return notifications

    def _scan_market_candidates(self):
        """Scans for potential stocks using market data and news search."""
        candidates = set()
        
        # 1. Market Data: Top Gainers/Losers
        market_stats = market_data.get_market_summary()
        for stock in market_stats.get("top_gainers", []):
            candidates.add(stock["symbol"])
        for stock in market_stats.get("top_losers", []):
            candidates.add(stock["symbol"])
            
        # 2. News Search: "Best stocks to buy"
        # This is a mock implementation. In a real scenario, we'd parse the news results.
        # For now, we'll rely on the market data + specific news analysis in the loop above.
        # We could add a few hardcoded "blue chip" stocks to always check
        candidates.update(["OGDC", "PPL", "TRG", "LUCK", "ENGRO"])
        
        return list(candidates)

    def _analyze_position_with_gpt(self, symbol: str, quantity: int, avg_cost: float, current_price: float, purchased_at: datetime = None) -> Dict:
        """
        Uses GPT to intelligently decide whether to HOLD, SELL (partial/full), or BUY_MORE for a position.
        Returns: {"action": "HOLD/SELL/BUY_MORE", "quantity": int, "confidence": str, "reason": str}
        """
        
        # Fallback decision if GPT is not available
        if not self.openai_client:
            pnl_percent = (current_price - avg_cost) / avg_cost
            if pnl_percent < -0.05:
                return {"action": "SELL", "quantity": quantity, "confidence": "LOW", "reason": "Fallback: Stop Loss"}
            elif pnl_percent > 0.10:
                return {"action": "SELL", "quantity": max(1, int(quantity * 0.5)), "confidence": "LOW", "reason": "Fallback: Take Profit"}
            else:
                return {"action": "HOLD", "quantity": 0, "confidence": "LOW", "reason": "Fallback: Within range"}
        
        # Calculate position metrics
        pnl_percent = ((current_price - avg_cost) / avg_cost) * 100
        pnl_amount = (current_price - avg_cost) * quantity
        position_value = current_price * quantity
        
        # Calculate holding period
        if purchased_at:
            holding_duration = datetime.now() - purchased_at
            holding_days = holding_duration.days
            holding_hours = holding_duration.total_seconds() / 3600
            if holding_days > 0:
                holding_period_str = f"{holding_days} day{'s' if holding_days != 1 else ''}"
            else:
                holding_period_str = f"{holding_hours:.1f} hours"
        else:
            holding_period_str = "Unknown"
            holding_days = 999  # Assume old position
        
        # Fetch recent news for context
        try:
            news = news_agent.fetch_market_news(f"{symbol} stock Pakistan Stock Exchange latest")
            news_summary = " | ".join([f"{item.get('title', 'N/A')}" for item in news[:3]]) if news else "No recent news available"
        except Exception as e:
            news_summary = f"Error fetching news: {str(e)}"
        
        # Get market context
        try:
            market_stats = market_data.get_market_summary()
            market_sentiment = "BULLISH" if market_stats.get("overall_change", 0) > 0 else "BEARISH"
        except:
            market_sentiment = "NEUTRAL"

        # Fetch Past Trades for Context
        past_trades = self.db.query(AITradeHistory).filter(AITradeHistory.symbol == symbol).order_by(AITradeHistory.timestamp.desc()).limit(5).all()
        past_trades_str = "\n".join([f"- {t.action} {t.quantity} @ {t.price:.2f} on {t.timestamp.strftime('%Y-%m-%d')} (PnL: {t.pnl})" for t in past_trades]) if past_trades else "No recent trades."
        
        # Construct intelligent prompt for GPT
        prompt = f"""You are an expert autonomous trading AI managing a position in {symbol} on the Pakistan Stock Exchange (PSX).
        **ALL PRICES ARE IN PAKISTANI RUPEES (PKR).**

POSITION DETAILS:
- Symbol: {symbol}
- Quantity Held: {quantity} shares
2. **Time Horizon**: Positions held <3 days should be given more time unless fundamentally broken.
3. **Risk Management**: Cut significant losses (>8-10%) to preserve capital.
4. **Profit Taking**: Capture gains at +15-20% or on strong news catalysts.

**Specific Guidelines:**
- If holding period <3 days AND loss <5%: Default to HOLD unless severe negative news
- If holding period <24 hours AND loss <3%: Almost always HOLD (too early to judge)
- If loss >10%: Consider SELL to limit damage
- If profit >15%: Consider partial profit taking (sell 30-50%)
- News sentiment should override small P&L fluctuations

**What to Consider:**
✓ Is the loss/gain significant enough to act on?
✓ Has there been material news that changes the thesis?
✓ Is this a normal market fluctuation or a real problem?
✓ Have we given the position enough time to work?
✓ What's the overall market doing today?

**Actions Available:**
1. HOLD - Keep the position (PREFER THIS for early-stage small losses)
2. SELL - Exit partially or fully (specify quantity)
3. BUY_MORE - Only if extremely bullish on new positive catalyst

OUTPUT FORMAT (JSON):
{{
    "action": "HOLD/SELL/BUY_MORE",
    "quantity": <number of shares to sell/buy, 0 for HOLD>,
    "confidence": "HIGH/MEDIUM/LOW",
    "reason": "<1-2 sentence explanation>"
}}

Make a measured, patient decision. Short-term noise should not trigger premature exits."""

        try:
            print(f"\n[GPT DECISION] Analyzing position: {symbol}")
            print(f"[GPT DECISION] PnL: {pnl_percent:.2f}% | Held: {holding_period_str} | News: {news_summary[:80]}...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert autonomous trading AI focused on disciplined, patient decision-making. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5  # Lower temperature for more consistent decisions
            )
            
            decision = json.loads(response.choices[0].message.content)
            
            # Validate and log decision
            print(f"[GPT DECISION] Result: {decision.get('action')} | Reason: {decision.get('reason')}")
            
            # Ensure quantity is valid
            if decision.get("action") == "SELL":
                decision["quantity"] = min(decision.get("quantity", quantity), quantity)
            
            return decision
            
        except Exception as e:
            print(f"[GPT DECISION ERROR] {symbol}: {str(e)}")
            # Fallback to conservative HOLD
            return {
                "action": "HOLD",
                "quantity": 0,
                "confidence": "LOW",
                "reason": f"GPT Error: {str(e)[:50]}. Holding position for safety."
            }

    def monitor_portfolio(self, notifications):
        """Checks current AI holdings and uses GPT to make intelligent exit/hold decisions."""
        holdings = self.db.query(AIPortfolioItem).all()
        settings = self.db.query(UserSettings).first()
        
        print(f"\n[PORTFOLIO MONITOR] Analyzing {len(holdings)} positions with GPT...")
        
        for item in holdings:
            current_price = market_data.get_live_price(item.symbol)
            if current_price <= 0: 
                print(f"[PORTFOLIO MONITOR] {item.symbol}: Invalid price, skipping")
                continue
            
            # Update cached price
            item.current_price = current_price
            
            # Use GPT to analyze the position
            decision = self._analyze_position_with_gpt(
                symbol=item.symbol,
                quantity=item.quantity,
                avg_cost=item.avg_cost,
                current_price=current_price,
                purchased_at=item.purchased_at  # Pass holding period info
            )
            
            action = decision.get("action", "HOLD")
            qty = decision.get("quantity", 0)
            reason = decision.get("reason", "No reason provided")
            confidence = decision.get("confidence", "UNKNOWN")
            
            # Execute the decision
            if action == "SELL" and qty > 0:
                print(f"[PORTFOLIO MONITOR] Executing SELL: {qty} {item.symbol} | Confidence: {confidence}")
                self.execute_trade(item.symbol, "SELL", qty, current_price, f"GPT Decision ({confidence}): {reason}", notifications, settings)
            elif action == "BUY_MORE" and qty > 0:
                print(f"[PORTFOLIO MONITOR] GPT suggests BUY_MORE, but skipping (position management mode)")
                # Optionally implement buy_more logic here
            else:
                print(f"[PORTFOLIO MONITOR] {item.symbol}: HOLD | {reason}")
        
        self.db.commit()

    def _evaluate_and_trade(self, stock_data, action, strategy, settings, notifications):
        symbol = stock_data["symbol"]
        price = float(stock_data["price"])
        
        if price <= 0: return

        # Dynamic Position Sizing based on Budget
        # Allocate max 10% of available budget per trade
        max_allocation = settings.ai_cash_balance * 0.10
        qty = int(max_allocation / price)
        
        if qty < 1: qty = 1 # Minimum 1 share
        
        cost = qty * price
        
        # Execute if we have enough cash
        if cost <= settings.ai_cash_balance:
            self.execute_trade(symbol, action, qty, price, strategy, notifications, settings)

    def execute_trade(self, symbol, action, quantity, price, reason, notifications, settings):
        """Executes a trade for the AI portfolio."""
        
        total_value = quantity * price
        
        if action == "BUY":
            if settings.ai_cash_balance < total_value:
                return # Insufficient funds
                
            # Deduct Cash
            settings.ai_cash_balance -= total_value
            
            # Add to Portfolio
            item = self.db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == symbol).first()
            if item:
                new_total_cost = item.total_cost + total_value
                new_qty = item.quantity + quantity
                item.avg_cost = new_total_cost / new_qty
                item.quantity = new_qty
                item.total_cost = new_total_cost
            else:
                new_item = AIPortfolioItem(
                    symbol=symbol,
                    quantity=quantity,
                    avg_cost=price,
                    total_cost=total_value,
                    current_price=price,
                    purchased_at=datetime.now()  # Track when position was opened
                )
                self.db.add(new_item)
            
            # Log History
            history = AITradeHistory(
                symbol=symbol, action="BUY", quantity=quantity, price=price, reason=reason
            )
            self.db.add(history)
            
            # Notification
            msg = f"Bought {quantity} {symbol} at {price:.2f}. Reason: {reason}"
            self._add_notification("AI Trade Executed", msg, "TRADE", notifications)
            
        elif action == "SELL":
            item = self.db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == symbol).first()
            if not item or item.quantity < quantity:
                return # Cannot sell
            
            # Calculate PnL
            pnl = (price - item.avg_cost) * quantity
            
            # Add Cash
            settings.ai_cash_balance += total_value
            
            # Update Portfolio
            if item.quantity == quantity:
                self.db.delete(item)
            else:
                item.quantity -= quantity
                item.total_cost -= (item.avg_cost * quantity)
            
            # Log History
            history = AITradeHistory(
                symbol=symbol, action="SELL", quantity=quantity, price=price, pnl=pnl, reason=reason
            )
            self.db.add(history)
            
            # Notification
            msg = f"Sold {quantity} {symbol} at {price:.2f}. PnL: {pnl:.2f}. Reason: {reason}"
            self._add_notification("AI Trade Executed", msg, "TRADE", notifications)
            
        self.db.commit()

    def _add_notification(self, title, message, type, notifications):
        note = AINotification(title=title, message=message, type=type)
        self.db.add(note)
        self.db.commit()
        notifications.append({"title": title, "message": message, "type": type})
