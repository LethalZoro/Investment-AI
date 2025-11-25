import requests

url = "https://psxterminal.com/api/ticks/REG"
print(f"Testing {url}...")
try:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and "data" in data:
             print(f"Got data list of length: {len(data['data'])}")
             print(f"Sample: {data['data'][:2]}")
        elif isinstance(data, list):
             print(f"Got list of length: {len(data)}")
        else:
             print("Unknown format")
except Exception as e:
    print(f"Error: {e}")
