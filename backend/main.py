from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
from datetime import datetime

# Explicitly load .env from the backend directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

from models import SessionLocal, init_db, PortfolioItem, UserSettings, Transaction, PortfolioHistory, AIAlert, AIPortfolioItem, AINotification, AITradeHistory
from portfolio_engine import PortfolioEngine
from market_data import market_data
from autonomous_agent import AutonomousAgent
from llm_agent import llm_agent
from news_agent import news_agent
from fastapi.responses import JSONResponse

# Initialize Database
init_db()

app = FastAPI(title="PSX Investment Co-Pilot")

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://investment-ai-production.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ... (existing code) ...

@app.post("/autonomous/analyze-news")
def analyze_news(db: Session = Depends(get_db)):
    """Triggers the AI News Analysis cycle."""
    # Check Trading Hours
    settings = db.query(UserSettings).first()
    if settings:
        now = datetime.now().strftime("%H:%M")
        start_time = settings.trading_start_time or "09:30"
        end_time = settings.trading_end_time or "15:30"
        
        if not (start_time <= now <= end_time):
            print(f"[NEWS ANALYSIS] Skipping: Current time {now} is outside trading hours ({start_time} - {end_time})")
            return {"message": "Skipped: Outside trading hours", "alerts_generated": 0}

    print("DEBUG: Starting News Analysis...")
    
    # 1. Fetch News
    news = news_agent.fetch_market_news()
    print(f"DEBUG: Fetched {len(news)} news items.")
    
    # 2. Analyze with LLM
    alerts_data = news_agent.analyze_news(news)
    print(f"DEBUG: Generated {len(alerts_data)} alerts.")
    
    new_alerts = []
    for alert in alerts_data:
        # Check if duplicate (same symbol and signal today)
        # For simplicity, just adding for now
        db_alert = AIAlert(
            symbol=alert.get('symbol'),
            signal=alert.get('signal'),
            reason=alert.get('reason'),
            url=alert.get('url'),
            timestamp=datetime.now()
        )
        db.add(db_alert)
        new_alerts.append(db_alert)
        
    db.commit()
    return {"message": "Analysis complete", "alerts_generated": len(new_alerts)}

@app.get("/autonomous/alerts")
def get_alerts(db: Session = Depends(get_db)):
    return db.query(AIAlert).order_by(AIAlert.timestamp.desc()).limit(20).all()

@app.post("/settings/autonomous")

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "PSX Investment Co-Pilot API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

def record_daily_snapshot(db: Session):
    """Records the portfolio value for today if not already recorded."""
    from datetime import date
    today = date.today()
    
    # Check if we already have a record for today
    last_record = db.query(PortfolioHistory).order_by(PortfolioHistory.date.desc()).first()
    
    if last_record and last_record.date.date() == today:
        return # Already recorded today

    # Calculate current values
    engine = PortfolioEngine(db)
    summary = engine.get_portfolio_summary()
    
    new_record = PortfolioHistory(
        total_value=summary["total_value"],
        cash_balance=summary["cash_balance"],
        holdings_value=summary["holdings_value"],
        date=datetime.now()
    )
    db.add(new_record)
    db.commit()

# --- Portfolio Routes ---
@app.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    # Record history snapshot whenever dashboard is loaded (simulating daily tracking)
    try:
        record_daily_snapshot(db)
    except Exception as e:
        print(f"Failed to record history: {e}")
        
    engine = PortfolioEngine(db)
    return engine.get_portfolio_summary()

class PortfolioItemCreate(BaseModel):
    symbol: str
    quantity: int
    avg_cost: float
    strategy_tag: str = "UNASSIGNED"

@app.post("/portfolio/add")
def add_portfolio_item(item: PortfolioItemCreate, db: Session = Depends(get_db)):
    db_item = PortfolioItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    db.refresh(db_item)
    return db_item

class PortfolioSell(BaseModel):
    symbol: str
    quantity: int
    price: float

@app.post("/portfolio/sell")
def sell_portfolio_item(sell: PortfolioSell, db: Session = Depends(get_db)):
    # 1. Find the portfolio item
    item = db.query(PortfolioItem).filter(PortfolioItem.symbol == sell.symbol).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in portfolio")
    
    if item.quantity < sell.quantity:
        raise HTTPException(status_code=400, detail="Insufficient quantity")
    
    # 2. Update Cash Balance
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
    
    total_sale_value = sell.quantity * sell.price
    settings.cash_balance += total_sale_value
    
    # 3. Record Transaction
    transaction = Transaction(
        symbol=sell.symbol,
        action="SELL",
        quantity=sell.quantity,
        price=sell.price,
        timestamp=datetime.now(),
        notes=f"Manual Sell. PnL: {(sell.price - item.avg_cost) * sell.quantity:.2f}"
    )
    db.add(transaction)
    
    # 4. Update or Remove Portfolio Item
    print(f"DEBUG: Selling {sell.quantity} of {item.symbol}. Current Qty: {item.quantity}")
    
    if item.quantity == sell.quantity:
        print("DEBUG: Deleting item")
        db.delete(item)
    else:
        item.quantity -= sell.quantity
        print(f"DEBUG: Updated Qty to {item.quantity}")
        
    db.commit()
    print("DEBUG: Commit successful")
    return {"message": "Sold successfully", "new_cash_balance": settings.cash_balance}

class CashUpdate(BaseModel):
    amount: float
    type: str # DEPOSIT, WITHDRAW

@app.post("/portfolio/cash")
def update_cash(update: CashUpdate, db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
    
    if update.type == "DEPOSIT":
        settings.cash_balance += update.amount
    elif update.type == "WITHDRAW":
        if settings.cash_balance >= update.amount:
            settings.cash_balance -= update.amount
        else:
            raise HTTPException(status_code=400, detail="Insufficient funds")
            
    db.commit()
    return {"cash_balance": settings.cash_balance}

@app.get("/portfolio/history")
def get_portfolio_history(db: Session = Depends(get_db)):
    """Returns the portfolio value history for the chart."""
    history = db.query(PortfolioHistory).order_by(PortfolioHistory.date.asc()).all()
    
    if not history:
        # If no history, return current state as a single point so chart isn't empty
        engine = PortfolioEngine(db)
        summary = engine.get_portfolio_summary()
        return [{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "value": summary["total_value"]
        }]
        
    return [{"date": h.date.strftime("%Y-%m-%d"), "value": h.total_value} for h in history]

# --- Market Data Routes ---
@app.get("/market-data/{symbol}")
def get_market_data(symbol: str):
    price = market_data.get_live_price(symbol)
    return {"symbol": symbol, "price": price}

@app.get("/market/summary")
def get_market_summary():
    return market_data.get_market_summary()

@app.get("/market/klines/{symbol}")
def get_klines(symbol: str, timeframe: str = "1d"):
    return market_data.get_klines(symbol, timeframe)

@app.get("/market/company/{symbol}")
def get_company_info(symbol: str):
    return market_data.get_company_info(symbol)

@app.get("/market/search")
def search_market(q: str):
    return market_data.search_symbol(q)

# --- Chat Route ---
class ChatRequest(BaseModel):
    message: str
    data_source: str = "ai" # "ai" or "personal"

@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # Gather context
    engine = PortfolioEngine(db)
    
    # Always fetch ALL data for both portfolios to allow comparison/roasting
    user_portfolio = engine.get_portfolio_summary()
    ai_portfolio = get_ai_portfolio_data(db)
    
    # Fetch recent history for both
    user_history = [
        {
            "symbol": t.symbol,
            "action": t.action,
            "price": t.price,
            "qty": t.quantity,
            "date": t.timestamp.strftime("%Y-%m-%d"),
            "notes": t.notes
        }
        for t in db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(10).all()
    ]
    
    ai_history = [
        {
            "symbol": t.symbol, 
            "action": t.action, 
            "price": t.price, 
            "qty": t.quantity, 
            "date": t.timestamp.strftime("%Y-%m-%d"),
            "reason": t.reason
        } 
        for t in db.query(AITradeHistory).order_by(AITradeHistory.timestamp.desc()).limit(10).all()
    ]

    context = {
        "market_status": market_data.get_market_status(),
        "data_source": request.data_source,
        "portfolio": user_portfolio,
        "ai_portfolio": ai_portfolio,
        "user_trade_history": user_history,
        "ai_trade_history": ai_history
    }
    
    response = llm_agent.get_response(request.message, context)
    return response

# --- Autonomous Agent Routes ---
@app.get("/autonomous/plan")
def get_daily_plan(db: Session = Depends(get_db)):
    """Deprecated: Returns latest AI notifications instead of a plan."""
    return db.query(AINotification).order_by(AINotification.timestamp.desc()).limit(5).all()

@app.get("/autonomous/alerts")
def get_alerts(db: Session = Depends(get_db)):
    """Returns all AI alerts (News + Intraday) sorted by time."""
    return db.query(AIAlert).order_by(AIAlert.timestamp.desc()).all()

class SettingsUpdate(BaseModel):
    daily_trade_budget: Optional[float] = None
    ai_cash_balance: Optional[float] = None
    autonomous_mode: Optional[bool] = None
    rollover_percent: Optional[float] = None
    rollover_percent: Optional[float] = None
    polling_interval: Optional[int] = None
    trading_start_time: Optional[str] = None
    trading_end_time: Optional[str] = None

@app.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.post("/settings")
def update_settings(update: SettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
    
    if update.daily_trade_budget is not None:
        settings.daily_trade_budget = update.daily_trade_budget
    if update.ai_cash_balance is not None:
        settings.ai_cash_balance = update.ai_cash_balance
    if update.autonomous_mode is not None:
        settings.autonomous_mode = update.autonomous_mode
    if update.rollover_percent is not None:
        settings.rollover_percent = update.rollover_percent
    if update.polling_interval is not None:
        settings.polling_interval = update.polling_interval
    if update.trading_start_time is not None:
        settings.trading_start_time = update.trading_start_time
    if update.trading_end_time is not None:
        settings.trading_end_time = update.trading_end_time
        
    db.commit()
    db.refresh(settings)
    return settings

@app.post("/autonomous/trade")
def trigger_trading_cycle(db: Session = Depends(get_db)):
    """Manually triggers the AI trading cycle."""
    agent = AutonomousAgent(db)
    notifications = agent.run_trading_cycle()
    return {"message": "Trading cycle completed", "notifications": notifications}

def get_ai_portfolio_data(db: Session):
    """Helper to calculate AI portfolio metrics."""
    items = db.query(AIPortfolioItem).all()
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
        db.commit()
    
    # Calculate current value and PnL dynamically
    portfolio_data = []
    total_value = 0
    total_pnl = 0
    
    for item in items:
        current_price = market_data.get_live_price(item.symbol)
        market_value = current_price * item.quantity
        pnl = market_value - item.total_cost
        pnl_percent = (pnl / item.total_cost) * 100 if item.total_cost > 0 else 0
        
        portfolio_data.append({
            "symbol": item.symbol,
            "quantity": item.quantity,
            "avg_cost": item.avg_cost,
            "current_price": current_price,
            "market_value": market_value,
            "pnl": pnl,
            "pnl_percent": pnl_percent
        })
        
        total_value += market_value
        total_pnl += pnl
    
    # Calculate overall PnL metrics
    current_net_worth = total_value + settings.ai_cash_balance
    initial_capital = settings.initial_ai_capital
    
    # Calculate Total Realized P&L from History
    from models import AITradeHistory
    total_realized_pnl = db.query(func.sum(AITradeHistory.pnl)).filter(
        AITradeHistory.pnl.isnot(None)
    ).scalar() or 0.0
    
    # Overall PnL = Realized PnL (History) + Unrealized PnL (Current Holdings)
    # Note: total_pnl calculated above is the Unrealized PnL of current holdings
    overall_pnl = total_realized_pnl + total_pnl
    
    # Calculate Total Invested Capital (Initial + Deposits) for percentage calculation
    total_deposits = db.query(func.sum(AITradeHistory.price)).filter(
        AITradeHistory.action == "DEPOSIT"
    ).scalar() or 0.0
    
    total_invested_capital = initial_capital + total_deposits
    
    overall_pnl_percent = (overall_pnl / total_invested_capital * 100) if total_invested_capital > 0 else 0
        
    return {
        "holdings": portfolio_data,
        "summary": {
            "total_value": current_net_worth,
            "holdings_value": total_value,
            "cash_balance": settings.ai_cash_balance,
            "total_pnl": total_pnl,
            "initial_capital": initial_capital,
            "overall_pnl": overall_pnl,
            "overall_pnl_percent": overall_pnl_percent
        }
    }

@app.get("/autonomous/portfolio")
def get_ai_portfolio(db: Session = Depends(get_db)):
    """Returns the AI's current portfolio holdings with overall PnL metrics."""
    return get_ai_portfolio_data(db)

@app.post("/autonomous/new-day")
def simulate_new_day(db: Session = Depends(get_db)):
    """Simulates a new day: Adds daily budget to AI cash balance."""
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
    
    # Add daily budget
    budget_to_add = settings.daily_trade_budget
    settings.ai_cash_balance += budget_to_add
    
    # Track deposit in trade history for P&L calculation
    from models import AITradeHistory
    deposit_record = AITradeHistory(
        symbol="DEPOSIT",
        action="DEPOSIT",
        quantity=0,
        price=budget_to_add,
        total_value=budget_to_add,
        pnl=None,
        reason=f"Daily budget injection: Rs. {budget_to_add:,.2f}"
    )
    db.add(deposit_record)
    
    # Log notification
    agent = AutonomousAgent(db)
    agent._add_notification(
        "New Day: Budget Injected", 
        f"Added Rs. {budget_to_add:,.2f} to AI Cash Balance. New Balance: Rs. {settings.ai_cash_balance:,.2f}", 
        "SYSTEM", 
        [] # No live list needed here, just DB
    )
    
    db.commit()
    return {"message": "New day simulated", "added_budget": budget_to_add, "new_balance": settings.ai_cash_balance}

@app.get("/autonomous/notifications")
def get_ai_notifications(db: Session = Depends(get_db)):
    """Returns the AI's action log."""
    return db.query(AINotification).order_by(AINotification.timestamp.desc()).limit(50).all()

@app.get("/autonomous/trade-history")
def get_trade_history(db: Session = Depends(get_db)):
    """Returns the AI's complete trade history with P&L breakdown."""
    from models import AITradeHistory
    trades = db.query(AITradeHistory).order_by(AITradeHistory.timestamp.desc()).all()
    return trades

@app.get("/autonomous/intraday")
def run_intraday_check(db: Session = Depends(get_db)):
    # Deprecated or can be merged into trading cycle
    agent = AutonomousAgent(db)
    # reusing trading cycle for now as it covers monitoring
    notifications = agent.run_trading_cycle()
    return {"notifications": notifications}
