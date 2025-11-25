"""
Database migration script to add new columns to existing tables.
Run this once to update the schema without losing data.
"""
import sqlite3

DB_PATH = "./psx_copilot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add initial_ai_capital to user_settings if it doesn't exist
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'initial_ai_capital' not in columns:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN initial_ai_capital REAL DEFAULT 10000.0")
            print("✓ Added initial_ai_capital to user_settings")
        else:
            print("- initial_ai_capital already exists in user_settings")
            
        # Add purchased_at to ai_portfolio_items if it doesn't exist
        cursor.execute("PRAGMA table_info(ai_portfolio_items)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'purchased_at' not in columns:
            cursor.execute("ALTER TABLE ai_portfolio_items ADD COLUMN purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✓ Added purchased_at to ai_portfolio_items")
        else:
            print("- purchased_at already exists in ai_portfolio_items")

        # Add trading_start_time to user_settings
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'trading_start_time' not in columns:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN trading_start_time TEXT DEFAULT '09:30'")
            print("✓ Added trading_start_time to user_settings")
        else:
            print("- trading_start_time already exists in user_settings")

        if 'trading_end_time' not in columns:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN trading_end_time TEXT DEFAULT '15:30'")
            print("✓ Added trading_end_time to user_settings")
        else:
            print("- trading_end_time already exists in user_settings")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
