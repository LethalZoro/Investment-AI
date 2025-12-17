import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load Env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

from models import SessionLocal, StockUniverse, init_db

def seed_universe():
    print("Initializing Database...")
    init_db() # Creates the table if it doesn't exist
    
    db = SessionLocal()
    
    # Define Universe
    # Tier 1: Conviction (1 stock, 30-40%)
    # Tier 2: Stability (4 stocks, ~10% each)
    # Tier 3: Optionality (10-11 stocks, 2-5% each)
    
    universe = [
        # TIER 1
        {"symbol": "SYS", "tier": "CORE", "target_weight": 0.40, "fundamentals": {"pe": 18.5, "fair_value": 600, "growth": 15}},
        
        # TIER 2
        {"symbol": "OGDC", "tier": "STABILITY", "target_weight": 0.10, "fundamentals": {"pe": 4.5, "fair_value": 180, "yield": 12}},
        {"symbol": "PPL", "tier": "STABILITY", "target_weight": 0.10, "fundamentals": {"pe": 4.2, "fair_value": 150, "yield": 10}},
        {"symbol": "LUCK", "tier": "STABILITY", "target_weight": 0.10, "fundamentals": {"pe": 6.8, "fair_value": 900, "growth": 8}},
        {"symbol": "ENGRO", "tier": "STABILITY", "target_weight": 0.10, "fundamentals": {"pe": 7.5, "fair_value": 350, "yield": 9}},
        
        # TIER 3
        {"symbol": "TRG", "tier": "OPTIONAL", "target_weight": 0.03, "fundamentals": {"pe": 12.0, "fair_value": 85, "growth": 20}},
        {"symbol": "AVN", "tier": "OPTIONAL", "target_weight": 0.02, "fundamentals": {"pe": 9.5, "fair_value": 70, "growth": 15}},
        {"symbol": "NETSOL", "tier": "OPTIONAL", "target_weight": 0.02, "fundamentals": {"pe": 10.0, "fair_value": 120, "growth": 18}},
        {"symbol": "AIRLINK", "tier": "OPTIONAL", "target_weight": 0.02, "fundamentals": {"pe": 8.5, "fair_value": 60, "growth": 25}},
        {"symbol": "SAZEW", "tier": "OPTIONAL", "target_weight": 0.02, "fundamentals": {"pe": 7.0, "fair_value": 1500, "growth": 12}},
        {"symbol": "MARI", "tier": "OPTIONAL", "target_weight": 0.03, "fundamentals": {"pe": 5.5, "fair_value": 3000, "yield": 8}},
        {"symbol": "MEBL", "tier": "OPTIONAL", "target_weight": 0.02, "fundamentals": {"pe": 6.0, "fair_value": 200, "yield": 5}},
        {"symbol": "UBL", "tier": "OPTIONAL", "target_weight": 0.02, "fundamentals": {"pe": 4.8, "fair_value": 180, "yield": 15}},
        {"symbol": "MCB", "tier": "OPTIONAL", "target_weight": 0.02, "fundamentals": {"pe": 5.2, "fair_value": 190, "yield": 14}},
    ]
    
    print(f"Seeding {len(universe)} stocks into Universe...")
    
    for item in universe:
        existing = db.query(StockUniverse).filter(StockUniverse.symbol == item["symbol"]).first()
        if not existing:
            new_stock = StockUniverse(
                symbol=item["symbol"],
                tier=item["tier"],
                target_weight=item["target_weight"],
                active=True,
                fundamentals_json=json.dumps(item["fundamentals"]),
                last_updated=datetime.utcnow()
            )
            db.add(new_stock)
            print(f"Added {item['symbol']} ({item['tier']})")
        else:
            # Update existing if needed
            existing.tier = item["tier"]
            existing.target_weight = item["target_weight"]
            existing.fundamentals_json = json.dumps(item["fundamentals"])
            print(f"Updated {item['symbol']}")
            
    db.commit()
    print("Seed Complete.")
    db.close()

if __name__ == "__main__":
    seed_universe()
