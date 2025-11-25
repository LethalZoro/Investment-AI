import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class MarketDataService:
    def __init__(self):
        self.base_url = "https://psxterminal.com/api" 
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Caches
        self.price_cache = {} # {symbol: (timestamp, price)}
        self.stats_cache = None # (timestamp, data)
        
        # Cache Durations
        self.price_ttl = timedelta(seconds=60) # 1 minute for prices
        self.stats_ttl = timedelta(minutes=5)  # 5 minutes for market stats
        
        self.last_request_time = 0
        self.min_interval = 0.6 # ~100 requests per minute = 0.6s per request

    def _rate_limit(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def get_live_price(self, symbol: str) -> float:
        # Check cache
        if symbol in self.price_cache:
            timestamp, price = self.price_cache[symbol]
            if datetime.now() - timestamp < self.price_ttl:
                return price

        self._rate_limit()
        try:
            # Try REG market first
            url = f"{self.base_url}/ticks/REG/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    price = float(data["data"]["price"])
                    self.price_cache[symbol] = (datetime.now(), price)
                    return price
            
            print(f"Warning: Could not fetch price for {symbol}. Status: {response.status_code}")
            return 0.0
            
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def get_market_summary(self) -> Dict[str, Any]:
        # Check cache
        if self.stats_cache:
            timestamp, data = self.stats_cache
            if datetime.now() - timestamp < self.stats_ttl:
                return data

        self._rate_limit()
        try:
            url = f"{self.base_url}/stats/REG"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    stats = data["data"]
                    
                    # Construct summary
                    summary = {
                        "status": "OPEN", # API doesn't explicitly give status in stats, assuming OPEN if we get data
                        "index": "KSE-100", # Placeholder, usually fetched from /ticks/IDX/KSE100
                        "volume": stats.get("totalVolume", 0),
                        "value": stats.get("totalValue", 0),
                        "gainers": stats.get("gainers", 0),
                        "losers": stats.get("losers", 0),
                        "top_gainers": stats.get("topGainers", [])[:5],
                        "top_losers": stats.get("topLosers", [])[:5]
                    }
                    
                    # Update cache
                    self.stats_cache = (datetime.now(), summary)
                    return summary
            
            return {"status": "UNKNOWN", "error": "Failed to fetch stats"}

        except Exception as e:
            print(f"Error fetching market stats: {e}")
            return {"status": "ERROR", "error": str(e)}

    def get_market_status(self):
        # Helper for legacy calls, extracts just the status/index info
        summary = self.get_market_summary()
        return {
            "status": summary.get("status", "UNKNOWN"),
            "index": summary.get("index", "KSE-100"),
            "value": summary.get("value", 0), # Using value as a proxy for index value if needed, or fetch separately
            "change": "N/A"
        }

    def get_klines(self, symbol: str, timeframe: str = "1d") -> list:
        self._rate_limit()
        try:
            url = f"{self.base_url}/klines/{symbol}/{timeframe}"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    return data["data"]
            return []
        except Exception as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return []

    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        self._rate_limit()
        try:
            url = f"{self.base_url}/companies/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    return data["data"]
            return {}
        except Exception as e:
            print(f"Error fetching company info for {symbol}: {e}")
            return {}

    def search_symbol(self, query: str) -> list:
        symbol = query.upper().strip()
        if not symbol:
            return []
            
        # Try to get live price
        price = self.get_live_price(symbol)
        if price > 0:
            # If price found, try to get more info or just return basic
            # We can try to get company info for name
            company_info = self.get_company_info(symbol)
            name = company_info.get("name", symbol)
            
            return [{
                "symbol": symbol,
                "name": name,
                "price": price,
                "change": 0.0, # We don't get change from get_live_price easily without history
                "changePercent": 0.0,
                "volume": 0 # We don't get volume from simple price check
            }]
        return []

market_data = MarketDataService()
