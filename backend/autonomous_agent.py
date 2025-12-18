import json
import os
import pytz
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict
import math

# Updated Imports
from models import UserSettings, StockUniverse, AIPortfolioItem, AINotification, AITradeHistory, AIRecommendation, StockUniverse
from market_data import market_data
# from news_agent import news_agent # Disabled for now to focus on allocation logic
from portfolio_engine import PortfolioEngine

class AutonomousAgent:
    def __init__(self, db: Session):
        self.db = db
        # We don't need news_agent for the core allocation engine right now, 
        # but can re-enable for "Regime Detection" later.

    def run_trading_cycle(self):
        """
        Executes the 'Forever Fund' Daily Allocation Cycle.
        1. Inject Daily Budget (if new day).
        2. Score the Universe (Opportunity Score).
        3. Allocate Capital to Top Ideas.
        4. Execute Buys.
        """
        notifications = []
        print("[FOREVER FUND] Starting Daily Cycle...")

        # 1. Get Settings & Check Trading Hours
        settings = self.db.query(UserSettings).first()
        if not settings:
            settings = UserSettings()
            self.db.add(settings)
            self.db.commit()
            
        # Check Trading Hours (PKT)
        pkt_tz = pytz.timezone('Asia/Karachi')
        now_pkt = datetime.now(pkt_tz)
        current_time_str = now_pkt.strftime("%H:%M")
        
        start_time = settings.trading_start_time or "09:30"
        end_time = settings.trading_end_time or "15:30"
        
        if not (start_time <= current_time_str <= end_time):
             print(f"[CYCLE] Skipping: Time {current_time_str} outside {start_time}-{end_time}")
             return []

        # 2. Daily Budget Injection
        # We check if we have already "run" today by looking at the last 'DEPOSIT' with 'Daily Budget' reason
        # Or simpler: rely on the external scheduler calling 'run_daily_budget_injection' in main.py
        # But to be safe, let's verify cash balance is sufficient to trade.
        
        if settings.ai_cash_balance < 1000:
            print("[CYCLE] Low Cash (<1000). Waiting for deposit.")
            return []

        # 3. Allocation Engine
        allocation_plan = self._allocate_capital(settings.ai_cash_balance, settings)
        
        print(f"[DEBUG] Allocation Plan returned {len(allocation_plan)} items.")
        
        # 4. Execute Plan -> CREATE RECOMMENDATIONS (Approvals Required)
        for trade in allocation_plan:
            print(f"[DEBUG] Processing allocation for {trade['symbol']}")
            self.create_recommendation(
                trade["symbol"],
                "BUY",
                trade["quantity"],
                trade["price"],
                f"Forever Fund Allocation: Score {trade['score']} (Tier: {trade['tier']}). {trade.get('news_reason', '')}",
                notifications
            )
            
        return notifications

    def create_recommendation(self, symbol, action, quantity, price, reason, notifications):
        """Creates a trade recommendation for user approval."""
        print(f"[RECOMMENDATION] Proposed {action} {quantity} {symbol} @ {price}")
        
        # Check if pending recommendation exists to avoid duplicates
        existing = self.db.query(AIRecommendation).filter(
            AIRecommendation.symbol == symbol, 
            AIRecommendation.action == action,
            AIRecommendation.status == "PENDING"
        ).first()
        
        if existing:
            print(f"[RECOMMENDATION] Duplicate found for {symbol}, updating.")
            # Update quantity/reason if strategy changed mind? 
            # Better to skip or update only if significant. Let's skip for now.
            return

        rec = AIRecommendation(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            reason=reason,
            status="PENDING"
        )
        self.db.add(rec)
        
        # Notify
        msg = f"Proposed {action} of {quantity} {symbol}. Waiting for approval."
        self._add_notification("Action Required", msg, "ACTION_REQUIRED", notifications)
        self.db.commit()

    def _allocate_capital(self, available_cash: float, settings: UserSettings) -> List[Dict]:
        """
        Core Logic: Distributes cash to the best opportunities in the Universe.
        Includes AI News Sentiment Analysis.
        """
        from news_agent import news_agent
        
        universe = self.db.query(StockUniverse).filter(StockUniverse.active == True).all()
        
        # --- RESTRICTION: Only Recommend Held Stocks ---
        holdings = self.db.query(AIPortfolioItem).all()
        held_symbols = {h.symbol for h in holdings}
        
        # Filter Universe
        # We only keep stocks that are currently in the portfolio
        universe = [s for s in universe if s.symbol in held_symbols]
        
        if not universe:
            print("[ALLOCATION] Restricted Mode: No held stocks found in Universe. Skipping analysis.")
            return []
        # -----------------------------------------------

        if not universe:
            print("[ALLOCATION] Universe is empty!")
            return []

        # A. Market Regime Check (Macro)
        regime_data = news_agent.get_sentiment_score("Pakistan Stock Exchange KSE100 Market Outlook")
        regime_score = regime_data.get("score", 0.0)
        regime_summary = regime_data.get("summary", "")
        
        regime_multiplier = 1.0
        if regime_score < -0.3: 
            regime_multiplier = 0.7 # Defensive
            print(f"[REGIME] Defensive Mode ({regime_score}): {regime_summary}")
        elif regime_score > 0.3: 
            regime_multiplier = 1.2 # Aggressive
            print(f"[REGIME] Aggressive Mode ({regime_score}): {regime_summary}")
        else:
            print(f"[REGIME] Neutral Mode ({regime_score})")

        # B. Technical/Fundamental Scoring
        scored_stocks = []
        market_summary = market_data.get_market_summary()
        
        for stock in universe:
            market_price = market_data.get_live_price(stock.symbol)
            if market_price <= 0: continue
            
            score_details = self._calculate_opportunity_score(stock, market_price, market_summary)
            score = score_details["total_score"]
            
            scored_stocks.append({
                "symbol": stock.symbol,
                "tier": stock.tier,
                "score": score, # Base Score
                "price": market_price,
            })

        # C. Filter Top Candidates for Deep AI Analysis
        # We only check news for the top 7 to save time/tokens
        scored_stocks.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = scored_stocks[:7]
        
        final_candidates = []
        print(f"\n[AI ANALYSIS] Analyzying news for top {len(top_candidates)} candidates...")
        
        for cand in top_candidates:
            # Fetch Stock Specific News
            news_data = news_agent.get_sentiment_score(f"{cand['symbol']} stock financial news")
            n_score = news_data.get("score", 0.0)
            n_reason = news_data.get("summary", "")
            
            # Adjust Score based on News (-1 to +1 -> -20% to +20%)
            # Base Score 80 + (Sentiment 1.0 * 20) = 100
            # Base Score 80 + (Sentiment -1.0 * 20) = 60
            sentiment_impact = n_score * 20
            final_score = cand["score"] + sentiment_impact
            final_score = min(100, max(0, final_score)) # Clamp 0-100
            
            print(f" > {cand['symbol']}: Base {cand['score']} + News {sentiment_impact:.1f} = {final_score:.1f} ({n_reason})")
            
            cand["final_score"] = final_score
            cand["news_reason"] = f"News Sentiment: {n_score} ({n_reason})"
            
            if final_score > 40: # Viability Threshold
                final_candidates.append(cand)

        # D. Final Sort & Distribute
        final_candidates.sort(key=lambda x: x["final_score"], reverse=True)
        top_picks = final_candidates[:5]
        
        if not top_picks:
            print("[ALLOCATION] No viable candidates found after news analysis.")
            return []

        # Formula: Allocation_i = (Score_i / Sum_Scores) * Deployable_Capital
        total_score = sum(c["final_score"] for c in top_picks)
        deployable_capital = available_cash * regime_multiplier # Adjust budget by Regime
        deployable_capital = min(deployable_capital, available_cash) # Can't spend more than we have
        
        allocations = []
        
        print(f"\n[ALLOCATION] Distributing Rs. {deployable_capital:,.2f} among top {len(top_picks)} stocks.")
        
        for cand in top_picks:
            raw_allocation = (cand["final_score"] / total_score) * deployable_capital
            
            # Apply Tier Limits
            max_limit = 0
            if cand["tier"] == "CORE": max_limit = deployable_capital * 0.80
            elif cand["tier"] == "STABILITY": max_limit = deployable_capital * 0.30
            else: max_limit = deployable_capital * 0.20
            
            final_amt = min(raw_allocation, max_limit)
            
            # Guardrail
            if final_amt < 1000: continue
                
            qty = int(final_amt / cand["price"])
            if qty > 0:
                allocations.append({
                    "symbol": cand["symbol"],
                    "quantity": qty,
                    "price": cand["price"],
                    "score": int(cand["final_score"]),
                    "tier": cand["tier"],
                    "news_reason": cand["news_reason"]
                })
                print(f" -> {cand['symbol']} ({cand['tier']}): {qty} shares @ {cand['price']}")
                
        return allocations

    def _calculate_opportunity_score(self, stock: StockUniverse, current_price: float, market_stats: Dict) -> Dict:
        """
        Scoring Engine (0-100)
        """
        fundamentals = json.loads(stock.fundamentals_json)
        
        # A. Valuation Score (0-30)
        # Using Fundamentals vs Price
        val_score = 15 # Default neutral
        fair_value = fundamentals.get("fair_value", 0)
        pe_ratio = fundamentals.get("pe", 0) # Target PE? or Current? Assuming static 'fair' PE for now
        
        if fair_value > 0:
            upside = (fair_value - current_price) / current_price
            # If upside > 20% -> High Score
            if upside > 0.20: val_score = 30
            elif upside > 0.10: val_score = 25
            elif upside > 0: val_score = 20
            elif upside > -0.10: val_score = 10
            else: val_score = 5
        
        # B. Momentum Score (0-30)
        # Simplified using simple Moving Average logic or RSI if available.
        # Since we only have KLines on demand, we'll try to deduce from market_data if possible, 
        # or use a simplified "Active vs Previous" check if we had history.
        # For now, let's use a placeholder based on market sentiment for the stock?
        # Actually, let's fetch KLines for the specific stock to verify trend.
        mom_score = 15
        try:
            # We can't fetch klines for EVERY stock in the loop efficiently without rate limits.
            # Workaround: Use Daily Change from market_stats if present
            # Or assume neutral if data missing.
            pass
        except:
            pass
            
        # C. Position Context (0-15)
        # Underweight = Higher Score
        p_score = 7
        existing = self.db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == stock.symbol).first()
        
        # Calculate current weight
        # This is expensive to do for all, so maybe estimate?
        # Let's Skip complex portfolio weight calc for MVP and prioritize "Don't have it? Buy it"
        if not existing:
            p_score = 15 # High priority if missing
        else:
            # If we have it, check if we are below target weight?
            # Requires Total Portfolio Value. 
            pass

        # D. Fundamental (0-25)
        # Static from Universe for now
        fun_score = 20 # Assume good fundamentals if in Universe
        
        total = val_score + mom_score + fun_score + p_score
        return {"total_score": min(100, total), "val": val_score, "mom": mom_score}

    def execute_trade(self, symbol, action, quantity, price, reason, notifications, settings, recommendation_id=None):
        """Executes a trade and logs it definitively."""
        
        total_val = quantity * price
        
        if action == "BUY":
            # Double check cash
            if settings.ai_cash_balance < total_val:
                print(f"[EXECUTE] Fail: Insufficient Cash for {symbol}")
                return

            print(f"[EXECUTE] Buying {quantity} {symbol} @ {price}")
            
            # 1. Update Cash
            settings.ai_cash_balance -= total_val
            
            # 2. Update/Create Portfolio Item
            item = self.db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == symbol).first()
            if item:
                # Avg Cost Logic
                new_cost = item.total_cost + total_val
                new_qty = item.quantity + quantity
                item.avg_cost = new_cost / new_qty
                item.quantity = new_qty
                item.total_cost = new_cost
                item.current_price = price 
            else:
                new_item = AIPortfolioItem(
                    symbol=symbol,
                    quantity=quantity,
                    avg_cost=price,
                    total_cost=total_val,
                    current_price=price,
                    purchased_at=datetime.now(pytz.utc),
                    user_reasoning=reason
                )
                self.db.add(new_item)
                
            # 3. Log Trade History
            history = AITradeHistory(
                symbol=symbol,
                action="BUY",
                quantity=quantity,
                price=price,
                pnl=None,
                timestamp=datetime.now(pytz.utc),
                reason=reason
            )
            self.db.add(history)
            
            # 4. Notify
            self._add_notification(
                f"Bought {symbol}",
                f"Allocated {quantity} shares @ Rs. {price:.2f}. {reason}",
                "TRADE",
                notifications
            )
            
        elif action == "SELL":
            print(f"[EXECUTE] Selling {quantity} {symbol} @ {price}")
            
            item = self.db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == symbol).first()
            if not item or item.quantity < quantity:
                print(f"[EXECUTE] Fail: Insufficient Quantity for {symbol}")
                return

            # 1. Update Cash
            settings.ai_cash_balance += total_val
            
            # 2. Update Portfolio Item
            # PnL Calculation
            # Cost Basis of sold portion = avg_cost * quantity
            cost_basis_sold = item.avg_cost * quantity
            pnl = total_val - cost_basis_sold
            
            # Update Item
            item.quantity -= quantity
            item.total_cost -= cost_basis_sold 
            item.current_price = price
            
            if item.quantity == 0:
                self.db.delete(item)
            
            # 3. Log Trade History
            history = AITradeHistory(
                symbol=symbol,
                action="SELL",
                quantity=quantity,
                price=price,
                pnl=pnl,
                timestamp=datetime.now(pytz.utc),
                reason=reason
            )
            self.db.add(history)
            
            # 4. Notify
            self._add_notification(
                f"Sold {symbol}",
                f"Sold {quantity} shares @ Rs. {price:.2f}. PnL: {pnl:.2f}. {reason}",
                "TRADE",
                notifications
            )

        # 5. Commit
        self.db.commit()

    def _add_notification(self, title, message, type, notifications):
        note = AINotification(title=title, message=message, type=type)
        self.db.add(note)
        # self.db.commit() # Commit done in caller
        notifications.append({"title": title, "message": message, "type": type})


