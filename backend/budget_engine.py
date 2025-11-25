from sqlalchemy.orm import Session
from datetime import datetime
from models import UserSettings

class BudgetEngine:
    def __init__(self, db: Session):
        self.db = db
        self.settings = self._get_or_create_settings()

    def _get_or_create_settings(self):
        settings = self.db.query(UserSettings).first()
        if not settings:
            settings = UserSettings()
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def get_daily_budget(self) -> float:
        """
        Calculates available budget for today:
        Daily Limit + (Previous Unused * Rollover %)
        """
        today = datetime.utcnow().date()
        last_run = self.settings.last_run_date.date() if self.settings.last_run_date else None

        # If running for the first time today
        if last_run != today:
            # Calculate rollover from carryover
            rollover_amount = self.settings.unused_budget_carryover * self.settings.rollover_percent
            
            # Reset carryover for the new day (it will be recalculated at end of day)
            # Actually, carryover is set at the END of the previous day.
            # So we just use it now.
            
            total_budget = self.settings.daily_trade_budget + rollover_amount
            
            # Update last run date
            self.settings.last_run_date = datetime.utcnow()
            self.db.commit()
            
            return total_budget
        else:
            # If already ran today, return the budget (logic might need to check if plan already exists)
            # For simplicity, we assume this is called to generate the plan.
            rollover_amount = self.settings.unused_budget_carryover * self.settings.rollover_percent
            return self.settings.daily_trade_budget + rollover_amount

    def update_end_of_day(self, used_amount: float):
        """
        Updates the unused budget to be carried over to tomorrow.
        """
        daily_limit = self.get_daily_budget()
        unused = max(0, daily_limit - used_amount)
        
        self.settings.unused_budget_carryover = unused
        self.db.commit()
