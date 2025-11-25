import requests

url = "https://psxterminal.com/api/stats/REG"
print(f"Testing {url}...")
try:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "data" in data:
            stats = data["data"]
            gainers = stats.get("topGainers", [])
            losers = stats.get("topLosers", [])
            print(f"Top Gainers Count: {len(gainers)}")
            print(f"Top Losers Count: {len(losers)}")
            print(f"Sample Gainer: {gainers[0] if gainers else 'None'}")
    else:
        print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
