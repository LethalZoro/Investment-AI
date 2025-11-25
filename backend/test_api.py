import requests

def test_endpoint(endpoint):
    url = f"https://psxterminal.com/api{endpoint}"
    try:
        print(f"Testing {url}...")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"Got list of {len(data)} items")
                print(f"Sample: {data[:3]}")
            elif isinstance(data, dict):
                print(f"Got dict keys: {list(data.keys())}")
                if "data" in data:
                    print(f"Data sample: {data['data'][:3] if isinstance(data['data'], list) else data['data']}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)

test_endpoint("/tickers")
test_endpoint("/companies")
test_endpoint("/ticks/REG")
