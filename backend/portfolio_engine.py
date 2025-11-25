from sqlalchemy.orm import Session
from models import PortfolioItem, UserSettings
from market_data import market_data

class PortfolioEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_portfolio_summary(self):
        items = self.db.query(PortfolioItem).all()
        settings = self.db.query(UserSettings).first()
        
        if not settings:
            settings = UserSettings()
            self.db.add(settings)
            self.db.commit()

        total_value = settings.cash_balance
        holdings_value = 0.0
        holdings_summary = []

        for item in items:
            current_price = market_data.get_live_price(item.symbol)
            market_value = item.quantity * current_price
            holdings_value += market_value
            
            holdings_summary.append({
                "symbol": item.symbol,
                "quantity": item.quantity,
                "avg_cost": item.avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "pnl": market_value - (item.quantity * item.avg_cost),
                "strategy": item.strategy_tag
            })

        total_value += holdings_value

        return {
            "total_value": total_value,
            "cash_balance": settings.cash_balance,
            "holdings_value": holdings_value,
            "holdings": holdings_summary
        }

    def check_risk_exposure(self):
        # Implement risk checks (e.g., sector allocation, single stock concentration)
        pass
