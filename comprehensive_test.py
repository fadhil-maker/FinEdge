import requests
import json
import hmac
import hashlib
import uuid

BASE = "https://finedge-iy0i.onrender.com"
results = []

def test(name, method, url, **kwargs):
    try:
        resp = getattr(requests, method)(url, timeout=30, **kwargs)
        results.append((name, resp.status_code, resp.text[:200]))
        print(f"{'PASS' if resp.status_code < 400 else 'FAIL'} [{resp.status_code}] {name}")
    except Exception as e:
        results.append((name, 'ERR', str(e)[:200]))
        print(f"FAIL [ERR] {name}: {e}")

# 1. Landing page (dev portal)
test("Landing Page", "get", f"{BASE}/")

# 2. Developer Admin Dashboard
test("Dev Admin Dashboard", "get", f"{BASE}/api/dashboard/admin/")

# 3. Officer Dashboard - Nexus
test("Officer Dashboard Nexus", "get", f"{BASE}/api/dashboard/officer/nexus/")

# 4. Officer Dashboard - Fed
test("Officer Dashboard Fed", "get", f"{BASE}/api/dashboard/officer/fed/")

# 5. Officer Dashboard - Aura
test("Officer Dashboard Aura", "get", f"{BASE}/api/dashboard/officer/aura/")

# 6. Contact form submit
test("Contact Form POST", "post", f"{BASE}/api/v1/contact/", json={"name": "Test", "email": "test@test.com", "message": "Hello"})

# 7. Submit edge metadata (without API key - should fail 401/403)
test("Edge Score No Auth", "post", f"{BASE}/api/v1/score/", json={"test": True})

# 8. Submit edge metadata WITH API key
payload_dict = {
    "device_hash_mask": f"device_{uuid.uuid4().hex[:8]}",
    "tracking_reference": f"REF-TEST-{uuid.uuid4().hex[:6].upper()}",
    "requested_amount": 2000,
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
payload_json = json.dumps(payload_dict)
secret = b'finedge_hmac_shared_secret_2026'
signature = hmac.new(secret, payload_json.encode('utf-8'), hashlib.sha256).hexdigest()

headers_nexus = {
    "Authorization": "Api-Key yJPJYfre.wYtJhJAJJkp6YzUd28yfEkAWVV3GvVbw",
    "Content-Type": "application/json",
    "X-FinEdge-Signature": signature
}
test("Edge Score Nexus Key", "post", f"{BASE}/api/v1/score/", headers=headers_nexus, data=payload_json)

# 9. Get application status (use a known ID)
# Use the application we just created
print("\n=== DONE ===")
for name, code, body in results:
    print(f"  {code:>4} | {name}: {body[:100]}")
