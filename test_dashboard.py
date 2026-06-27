import requests

try:
    resp = requests.get("https://finedge-iy0i.onrender.com/api/dashboard/officer/nexus/")
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("Success! Dashboard is rendering.")
except Exception as e:
    print(f"Error: {e}")
