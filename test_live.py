import requests
try:
    resp = requests.get("https://finedge.vercel.app/aura.html")
    print(f"Status Code Vercel: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")

try:
    resp2 = requests.get("https://finedge-iy0i.onrender.com/aura.html")
    print(f"Status Code Render: {resp2.status_code}")
except Exception as e:
    pass
