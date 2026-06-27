import requests
import json
import hmac

payload = json.dumps({"data_hash": "testhash123", "score": 850, "features": {"test": 1}})
secret = b'finedge_hmac_shared_secret_2026'
signature = hmac.new(secret, payload.encode('utf-8'), "sha256").hexdigest()

headers = {
    "Authorization": "Api-Key finedge_demo_api_key_2026",
    "Content-Type": "application/json",
    "X-FinEdge-Signature": signature
}

print('Sending payload...')
resp = requests.post("https://finedge-iy0i.onrender.com/api/v1/score/", headers=headers, data=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
