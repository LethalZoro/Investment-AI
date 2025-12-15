from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

# Explicitly load .env from the backend directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

from models import SessionLocal, init_db, PortfolioItem, UserSettings, Transaction, PortfolioHistory, AIAlert, AIPortfolioItem, AINotification, AITradeHistory, AIRecommendation
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
    # Check Trading Hours (PKT)
    settings = db.query(UserSettings).first()
    if settings:
        pkt_tz = pytz.timezone('Asia/Karachi')
        now_pkt = datetime.now(pkt_tz)
        current_time_str = now_pkt.strftime("%H:%M")
        
        start_time = settings.trading_start_time or "09:30"
        end_time = settings.trading_end_time or "15:30"
        
        if not (start_time <= current_time_str <= end_time):
            print(f"[NEWS ANALYSIS] Skipping: Current time {current_time_str} (PKT) is outside trading hours ({start_time} - {end_time})")
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



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()

def start_scheduler():
    """Starts the background scheduler for autonomous trading."""
    scheduler = BackgroundScheduler()
    # Run every 1 minute to check if we need to trade
    scheduler.add_job(run_scheduled_trading_cycle, 'interval', minutes=1)
    
    # Run Daily Budget Injection at 9:00 AM PKT
    scheduler.add_job(run_daily_budget_injection, 'cron', hour=9, minute=0, timezone='Asia/Karachi')
    
    scheduler.start()
    print("DEBUG: Background Scheduler Started")

def run_scheduled_trading_cycle():
    """
    Checks if it's time to run the trading cycle based on user settings.
    This runs every minute but only executes the trade logic if the polling interval has passed.
    """
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).first()
        if not settings or not settings.autonomous_mode:
            return # Auto mode disabled

        # 1. Check Trading Hours (PKT)
        pkt_tz = pytz.timezone('Asia/Karachi')
        now_pkt = datetime.now(pkt_tz)
        current_time_str = now_pkt.strftime("%H:%M")
        
        start_time = settings.trading_start_time or "09:30"
        end_time = settings.trading_end_time or "15:30"
        
        if not (start_time <= current_time_str <= end_time):
            # print(f"[AUTO] Outside trading hours: {current_time_str}")
            return

        # 2. Check Polling Interval
        # If last_run_date is None, run immediately
        # Else, check if enough minutes have passed
        should_run = False
        if not settings.last_run_date:
            should_run = True
        else:
            # Ensure last_run_date is timezone aware or handle naive comparison
            # We'll assume last_run_date is stored as UTC in DB (default), so we compare with UTC now
            # OR simpler: just check total seconds difference
            last_run = settings.last_run_date
            if last_run.tzinfo is None:
                last_run = pytz.utc.localize(last_run)
            
            now_utc = datetime.now(pytz.utc)
            minutes_diff = (now_utc - last_run).total_seconds() / 60
            
            if minutes_diff >= settings.polling_interval:
                should_run = True
        
        if should_run:
            print(f"[AUTO] Triggering Trading Cycle at {current_time_str} PKT")
            agent = AutonomousAgent(db)
            agent.run_trading_cycle()
            
            # Update last run time
            settings.last_run_date = datetime.now(pytz.utc)
            db.commit()
            
    except Exception as e:
        print(f"[AUTO] Scheduler Error: {e}")
    finally:
        db.close()

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
    portfolio_data = engine.get_portfolio_summary()
    summary = portfolio_data["summary"]
    
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

# --- Recommendation Routes ---
@app.get("/autonomous/recommendations")
def get_recommendations(db: Session = Depends(get_db)):
    """Fetch pending recommendations."""
    return db.query(AIRecommendation).filter(AIRecommendation.status == "PENDING").all()

@app.post("/autonomous/recommendations/{rec_id}/{action}")
def handle_recommendation(rec_id: int, action: str, db: Session = Depends(get_db)):
    """Approve or Deny a recommendation."""
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    if action == "approve":
        settings = db.query(UserSettings).first()
        agent = AutonomousAgent(db)
        
        # Execute Trade
        # Create empty notifications list for the function to populate
        notifications = [] 
        agent.execute_trade(
            rec.symbol, 
            rec.action, 
            rec.quantity, 
            rec.price, 
            rec.reason, 
            notifications, 
            settings, 
            recommendation_id=rec.id
        )
        rec.status = "APPROVED" # execute_trade will set to EXECUTED, but safe to update here too
        
    elif action == "deny":
        rec.status = "DENIED"
        db.commit()
    
    return {"message": f"Recommendation {action}d"}

class ManualStockAdd(BaseModel):
    symbol: str
    quantity: int
    price: float
    date: datetime # User provided date
    reasoning: str

@app.post("/autonomous/holdings/add")
def manual_add_stock(item: ManualStockAdd, db: Session = Depends(get_db)):
    """Manually add a stock to AI portfolio."""
    
    # Update AI Cost Basis / Cash? 
    # If user says "I bought this", should we deduct cash? 
    # Usually manual add implies existing holding. Let's ask or assume.
    # The user said: "it asks for the stock, how many shares i have, what price i bought them at and also at what date I bought them"
    # It complicates 'AI Cash Balance'. If we deduct cash, it might go negative if it was a past buy.
    # Let's assume we just track it and DONT touch cash, OR we deduct if it fits. 
    # Safest is to NOT touch cash if it's a "migrate" action, but if it's "I just bought this", we might want to.
    # Given requirements "I bought them at" (past tense), let's NOT deduct cash for now, or maybe create a "Correction" transaction.
    # User didn't specify cash handling for manual adds. Let's just add to portfolio.
    
    new_item = AIPortfolioItem(
        symbol=item.symbol,
        quantity=item.quantity,
        avg_cost=item.price,
        total_cost=item.quantity * item.price,
        current_price=item.price, # Will update on next refresh
        purchased_at=item.date,
        user_reasoning=item.reasoning
    )
    db.add(new_item)
    db.commit()
    return {"message": "Stock added manually"}

class ManualStockSell(BaseModel):
    symbol: str
    quantity: int
    price: float
    reason: str

@app.post("/autonomous/holdings/sell")
def manual_sell_stock(item: ManualStockSell, db: Session = Depends(get_db)):
    """Manually sell a stock from AI portfolio."""
    # Find item
    db_item = db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == item.symbol).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found in AI portfolio")
        
    if db_item.quantity < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient quantity")
        
    # Use Agent's logic to execute trade (handles Cash, History, Notification)
    # We create a dummy settings/notification list just for this call context or fetch real ones
    settings = db.query(UserSettings).first()
    agent = AutonomousAgent(db)
    notifications = []
    
    agent.execute_trade(
        item.symbol,
        "SELL",
        item.quantity,
        item.price,
        f"Manual Sell: {item.reason}",
        notifications,
        settings
    )
    
    return {"message": "Stock sold manually", "notifications": notifications}

class NotesUpdate(BaseModel):
    symbol: str
    notes: str

@app.post("/autonomous/holdings/update-notes")
def update_stock_notes(update: NotesUpdate, db: Session = Depends(get_db)):
    """Update user reasoning/notes for an AI holding."""
    item = db.query(AIPortfolioItem).filter(AIPortfolioItem.symbol == update.symbol).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.user_reasoning = update.notes
    db.commit()
    return {"message": "Notes updated"}

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
            "pnl_percent": pnl_percent,
            "purchased_at": item.purchased_at.isoformat() if item.purchased_at else None,
            "user_reasoning": item.user_reasoning,
            "last_decision": item.last_decision,
            "last_reason": item.last_reason,
            "last_confidence": item.last_confidence,
            "last_analyzed": item.last_analyzed.isoformat() if item.last_analyzed else None
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
            "overall_pnl_percent": overall_pnl_percent,
            "realized_pnl": total_realized_pnl
        }
    }

@app.get("/autonomous/portfolio")
def get_ai_portfolio(db: Session = Depends(get_db)):
    """Returns the AI's current portfolio holdings with overall PnL metrics."""
    return get_ai_portfolio_data(db)

def run_daily_budget_injection():
    """Standalone function to inject daily budget."""
    db = SessionLocal()
    try:
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
            # total_value removed as it doesn't exist in model
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
            [] 
        )
        
        db.commit()
        print(f"[DAILY JOB] Injected Rs. {budget_to_add}")
        return {"added_budget": budget_to_add, "new_balance": settings.ai_cash_balance}
    except Exception as e:
        print(f"[DAILY JOB ERROR] {e}")
        return None
    finally:
        db.close()

@app.post("/autonomous/new-day")
def simulate_new_day(db: Session = Depends(get_db)):
    """Simulates a new day: Adds daily budget to AI cash balance."""
    # We can just call the standalone function, but we need to handle the DB session carefully.
    # Since run_daily_budget_injection creates its own session, we can just call it.
    # However, to reuse the dependency session if we wanted, we'd need to refactor further.
    # For simplicity and safety with the scheduler, we'll let it use its own session logic 
    # or just replicate the fix here if we want to keep using the dependency.
    
    # Actually, let's just use the logic directly here to avoid session conflicts if we were passing db,
    # but since the scheduler needs it standalone, let's call the standalone function.
    result = run_daily_budget_injection()
    if result:
        return {"message": "New day simulated", **result}
    else:
        raise HTTPException(status_code=500, detail="Failed to simulate new day")

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
