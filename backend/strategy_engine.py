from typing import List, Dict
from models import PortfolioItem
from market_data import market_data

class StrategyEngine:
    def __init__(self):
        pass

    def generate_dca_plan(self, item: PortfolioItem) -> Dict:
        # Logic to generate DCA plan
        current_price = market_data.get_live_price(item.symbol)
        # Simple logic: if price is below avg cost, buy more
        action = "HOLD"
        if current_price < item.avg_cost:
            action = "BUY"
        
        return {
            "symbol": item.symbol,
            "strategy": "DCA",
            "action": action,
            "reason": f"Price {current_price} vs Avg Cost {item.avg_cost}"
        }

    def generate_forever_advice(self, item: PortfolioItem) -> Dict:
        # Logic for long-term holding
        return {
            "symbol": item.symbol,
            "strategy": "FOREVER",
            "advice": "Hold for long term. Check quarterly."
        }

    def generate_trading_signal(self, symbol: str) -> Dict:
        # Logic for short-term trading
        price = market_data.get_live_price(symbol)
        # Mock signal
        return {
            "symbol": symbol,
            "strategy": "TRADING",
            "signal": "NEUTRAL",
            "entry_zone": f"{price * 0.98}-{price * 0.99}",
            "stop_loss": price * 0.95
        }
