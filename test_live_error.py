import requests

url = "https://finedge-iy0i.onrender.com/api/v1/trigger_score/29d1bfc8-d069-4c17-aec2-841ddab60f22/"
resp = requests.post(url)
print(f"Status: {resp.status_code}")
print(f"Content: {resp.text}")
