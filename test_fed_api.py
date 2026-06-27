import requests
import json
import hmac
import uuid

# Define a complete payload with the exact keys required
payload_dict = {
    "device_hash_mask": f"device_{uuid.uuid4().hex[:8]}",
    "tracking_reference": f"REF-{uuid.uuid4().hex[:8].upper()}",
    "mathematical_vector": {
        "device_age_days": 400,
        "utility_sms_count": 15,
        "battery_deaths_weekly": 1,
        "saved_contacts_ratio": 0.85,
        "financial_apps_count": 4,
        "average_monthly_balance": 15000.50,
        "lifetime_emi_bounces": 0
    }
}
payload = json.dumps(payload_dict)

secret = b'finedge_hmac_shared_secret_2026'
signature = hmac.new(secret, payload.encode('utf-8'), "sha256").hexdigest()

headers = {
    "Authorization": "Api-Key SacLv7BE.Mux3G7ivugHwkJxUT8K4aiWCAQi30yZY",
    "Content-Type": "application/json",
    "X-FinEdge-Signature": signature
}

print('Sending payload with FED API key...')
resp = requests.post("https://finedge-iy0i.onrender.com/api/v1/score/", headers=headers, data=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
