from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./psx_copilot.db")

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Integer)
    avg_cost = Column(Float)
    strategy_tag = Column(String, default="UNASSIGNED") # DCA, FOREVER, TRADING, UNASSIGNED
    target_allocation = Column(Float, nullable=True)
    entry_notes = Column(String, nullable=True)
    risk_tolerance = Column(String, default="MEDIUM") # LOW, MEDIUM, HIGH

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    action = Column(String) # BUY, SELL
    quantity = Column(Integer)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    cash_balance = Column(Float, default=0.0)
    monthly_investment = Column(Float, default=0.0)
    daily_trade_budget = Column(Float, default=5000.0)
    ai_cash_balance = Column(Float, default=10000.0) # Separate budget for AI
    initial_ai_capital = Column(Float, default=10000.0) # Track starting capital for PnL calculation
    autonomous_mode = Column(Boolean, default=False)
    rollover_percent = Column(Float, default=0.30)
    risk_profile = Column(String, default="MEDIUM")
    last_run_date = Column(DateTime, nullable=True)
    unused_budget_carryover = Column(Float, default=0.0)
    polling_interval = Column(Integer, default=5) # Minutes
    trading_start_time = Column(String, default="09:30")
    trading_end_time = Column(String, default="15:30")

class DailyPlan(Base):
    __tablename__ = "daily_plans"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    plan_json = Column(String) # JSON string of the plan
    executed = Column(Boolean, default=False)
    budget_allocated = Column(Float, default=0.0)
    budget_used = Column(Float, default=0.0)
    rationale = Column(String, nullable=True)

class AIAlert(Base):
    __tablename__ = "ai_alerts"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    signal = Column(String) # BUY, SELL, HOLD
    reason = Column(String)
    url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    total_value = Column(Float)
    cash_balance = Column(Float)
    holdings_value = Column(Float)

# --- AI Autonomous Models ---

class AIPortfolioItem(Base):
    __tablename__ = "ai_portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Integer)
    avg_cost = Column(Float)
    current_price = Column(Float, default=0.0) # Cached price for quick PnL
    total_cost = Column(Float) # quantity * avg_cost
    purchased_at = Column(DateTime, default=datetime.utcnow) # Track when position was opened
    user_reasoning = Column(String, nullable=True) # User's notes/reasoning for this position
    
    # AI Decision Tracking
    last_decision = Column(String, default="HOLD") # HOLD, SELL, BUY_MORE
    last_reason = Column(String, nullable=True)
    last_confidence = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    last_analyzed = Column(DateTime, nullable=True)

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    action = Column(String) # BUY, SELL
    quantity = Column(Integer)
    price = Column(Float)
    reason = Column(String, nullable=True)
    status = Column(String, default="PENDING") # PENDING, APPROVED, DENIED, EXECUTED
    timestamp = Column(DateTime, default=datetime.utcnow)
    
class AITradeHistory(Base):
    __tablename__ = "ai_trade_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    action = Column(String) # BUY, SELL
    quantity = Column(Integer)
    price = Column(Float)
    pnl = Column(Float, nullable=True) # Only for SELL
    timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(String, nullable=True)

class AINotification(Base):
    __tablename__ = "ai_notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    message = Column(String)
    type = Column(String) # TRADE, ALERT, INFO, ACTION_REQUIRED
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)



def init_db():
    Base.metadata.create_all(bind=engine)
