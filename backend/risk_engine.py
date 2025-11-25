from typing import List, Dict
from models import PortfolioItem

class RiskEngine:
    def __init__(self, portfolio_items: List[PortfolioItem], total_portfolio_value: float):
        self.items = portfolio_items
        self.total_value = total_portfolio_value
        
        # Hard Constraints
        self.MAX_STOCK_ALLOCATION = 0.15 # 15%
        self.MAX_SECTOR_ALLOCATION = 0.40 # 40%
        self.MAX_LOSS_PER_TRADE = 0.02 # 2% of total portfolio

    def check_trade(self, symbol: str, quantity: int, price: float, sector: str = "Unknown") -> Dict:
        """
        Evaluates if a proposed trade violates any risk controls.
        Returns: {"allowed": bool, "reason": str}
        """
        trade_value = quantity * price
        
        # 1. Check Stock Allocation
        current_holding = next((item for item in self.items if item.symbol == symbol), None)
        current_val = (current_holding.quantity * current_holding.avg_cost) if current_holding else 0
        current_val = (current_holding.quantity * current_holding.avg_cost) if current_holding else 0
        new_total_stock_val = current_val + trade_value
        
        if self.total_value <= 0:
            return {
                "allowed": False,
                "reason": "Total portfolio value is zero. Cannot calculate risk metrics."
            }

        if new_total_stock_val / self.total_value > self.MAX_STOCK_ALLOCATION:
            return {
                "allowed": False, 
                "reason": f"Exceeds max allocation (15%) for {symbol}. Current: {((new_total_stock_val/self.total_value)*100):.1f}%"
            }

        # 2. Check Sector Allocation (Mocking sector for now as we don't have it in DB yet)
        # In a real app, we'd sum up all stocks in the same sector.
        # For now, we'll skip or assume safe.
        
        # 3. Check Max Trade Size (Proxy for volatility risk)
        # If a single trade is > 10% of portfolio, flag it.
        if trade_value / self.total_value > 0.10:
             return {
                "allowed": False, 
                "reason": f"Trade size too large ({((trade_value/self.total_value)*100):.1f}%). Max single trade 10% recommended."
            }

        return {"allowed": True, "reason": "Trade within risk limits"}
