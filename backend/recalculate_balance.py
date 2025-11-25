from sqlalchemy.orm import Session
from models import UserSettings, AITradeHistory, SessionLocal, init_db

def recalculate_ai_balance():
    db: Session = SessionLocal()
    try:
        # Get Settings
        settings = db.query(UserSettings).first()
        if not settings:
            print("No UserSettings found. Creating default...")
            settings = UserSettings()
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        initial_capital = settings.initial_ai_capital
        print(f"Initial Capital: {initial_capital}")
        
        # Get all trades
        trades = db.query(AITradeHistory).all()
        
        calculated_balance = initial_capital
        
        print("\n--- Trade History ---")
        for trade in trades:
            total_value = trade.quantity * trade.price
            if trade.action == "BUY":
                calculated_balance -= total_value
                print(f"BUY  {trade.quantity} {trade.symbol} @ {trade.price:.2f} | -{total_value:.2f}")
            elif trade.action == "SELL":
                calculated_balance += total_value
                print(f"SELL {trade.quantity} {trade.symbol} @ {trade.price:.2f} | +{total_value:.2f}")
            elif trade.action == "DEPOSIT":
                calculated_balance += trade.price # Using price field for amount
                print(f"DEPOSIT | +{trade.price:.2f}")
            elif trade.action == "WITHDRAW":
                calculated_balance -= trade.price
                print(f"WITHDRAW | -{trade.price:.2f}")
                
        print("---------------------")
        
        print(f"\nCurrent DB Balance: {settings.ai_cash_balance:.2f}")
        print(f"Calculated Balance: {calculated_balance:.2f}")
        
        # Update DB
        if abs(settings.ai_cash_balance - calculated_balance) > 0.01:
            print("\nUpdating database with calculated balance...")
            settings.ai_cash_balance = calculated_balance
            db.commit()
            print("Database updated successfully.")
        else:
            print("\nBalance is already correct.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    recalculate_ai_balance()
