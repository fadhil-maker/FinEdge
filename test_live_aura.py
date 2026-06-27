import requests

url = "https://finedge-iy0i.onrender.com/api/v1/trigger_score/51dfd6fa-c659-4b1e-b280-ae20a5246491/"
resp = requests.post(url)
print(f"Status: {resp.status_code}")
print(f"Content: {resp.text}")
