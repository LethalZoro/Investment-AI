from sqlalchemy.orm import Session
from models import StockUniverse, init_db, SessionLocal
import json

def seed_universe():
    db = SessionLocal()
    
    # User's Restricted "Forever Fund" List
    restricted_list = [
        {"symbol": "SYS", "tier": "CORE", "target_weight": 0.10, "fundamentals": {"pe": 12.0, "fair_value": 150, "growth": 20}},
        {"symbol": "PSX", "tier": "CORE", "target_weight": 0.10, "fundamentals": {"pe": 8.5, "fair_value": 45, "growth": 15}},
        {"symbol": "MEBL", "tier": "CORE", "target_weight": 0.10, "fundamentals": {"pe": 6.0, "fair_value": 200, "yield": 8}},
        {"symbol": "LUCK", "tier": "CORE", "target_weight": 0.08, "fundamentals": {"pe": 7.5, "fair_value": 750, "growth": 10}},
        {"symbol": "OGDC", "tier": "CORE", "target_weight": 0.08, "fundamentals": {"pe": 4.5, "fair_value": 150, "yield": 12}},
        
        {"symbol": "JSBL", "tier": "STABILITY", "target_weight": 0.05, "fundamentals": {"pe": 5.0, "fair_value": 20, "growth": 15}},
        {"symbol": "ZAL", "tier": "STABILITY", "target_weight": 0.05, "fundamentals": {"pe": 8.0, "fair_value": 50, "growth": 18}},
        {"symbol": "SAZEW", "tier": "STABILITY", "target_weight": 0.05, "fundamentals": {"pe": 7.0, "fair_value": 1600, "growth": 25}},
        {"symbol": "MARI", "tier": "STABILITY", "target_weight": 0.05, "fundamentals": {"pe": 5.5, "fair_value": 800, "yield": 10}},
        {"symbol": "BAFL", "tier": "STABILITY", "target_weight": 0.05, "fundamentals": {"pe": 4.0, "fair_value": 110, "yield": 11}},
        
        {"symbol": "FFC", "tier": "DYP", "target_weight": 0.05, "fundamentals": {"pe": 6.5, "fair_value": 500, "yield": 11}},
        {"symbol": "ENGROH", "tier": "DYP", "target_weight": 0.05, "fundamentals": {"pe": 7.0, "fair_value": 230, "yield": 9}},
        {"symbol": "EFERT", "tier": "DYP", "target_weight": 0.05, "fundamentals": {"pe": 6.8, "fair_value": 220, "yield": 10}},
        {"symbol": "TPLP", "tier": "OPTIONAL", "target_weight": 0.05, "fundamentals": {"pe": 15.0, "fair_value": 15, "growth": 30}},
        {"symbol": "DCR", "tier": "OPTIONAL", "target_weight": 0.05, "fundamentals": {"pe": 10.0, "fair_value": 40, "yield": 7}},
    ]

    print("--- Seeding Universe ---")
    
    # 1. Deactivate all existing first (optional, or just update)
    # db.query(StockUniverse).update({StockUniverse.active: False})
    
    for item in restricted_list:
        db_item = db.query(StockUniverse).filter(StockUniverse.symbol == item["symbol"]).first()
        if db_item:
            db_item.tier = item["tier"]
            db_item.target_weight = item["target_weight"]
            db_item.fundamentals_json = json.dumps(item["fundamentals"])
            db_item.active = True
            print(f"Updated {item['symbol']}")
        else:
            new_item = StockUniverse(
                symbol=item["symbol"],
                tier=item["tier"],
                target_weight=item["target_weight"],
                fundamentals_json=json.dumps(item["fundamentals"]),
                active=True
            )
            db.add(new_item)
            print(f"Created {item['symbol']}")
    
    db.commit()
    print("Seeding Complete.")

if __name__ == "__main__":
    init_db()
    seed_universe()
