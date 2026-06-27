import requests
import json
import hmac
import hashlib
import uuid
import time

BASE = 'https://finedge-iy0i.onrender.com'

# Correct API keys from the HTML files
KEYS = {
    'nexus': 'VgWTv8f0.wAQoI2ip4sNX1yk9ZaU1Z4UXJkGVjL6N',
    'fed': 'SacLv7BE.Mux3G7ivugHwkJxUT8K4aiWCAQi30yZY',
    'aura': 'btTYC3BO.pmbjlfcY3po5W8x821SB5MazTIudxwpx',
}

HMAC_SECRET = b'finedge_hmac_shared_secret_2026'

def submit_loan(bank_name, api_key):
    payload_dict = {
        'device_hash_mask': f'device_{uuid.uuid4().hex[:8]}',
        'tracking_reference': f'TEST-{bank_name.upper()}-{uuid.uuid4().hex[:6].upper()}',
        'requested_amount': 3000,
        'mathematical_vector': {
            'device_age_days': 400,
            'utility_sms_count': 18,
            'battery_deaths_weekly': 1,
            'saved_contacts_ratio': 0.65,
            'financial_apps_count': 5,
            'average_monthly_balance': 22000.0,
            'lifetime_emi_bounces': 0
        }
    }
    payload_json = json.dumps(payload_dict)
    signature = hmac.new(HMAC_SECRET, payload_json.encode('utf-8'), hashlib.sha256).hexdigest()

    headers = {
        'Authorization': f'Api-Key {api_key}',
        'Content-Type': 'application/json',
        'X-FinEdge-Signature': signature
    }

    resp = requests.post(f'{BASE}/api/v1/score/', headers=headers, data=payload_json, timeout=30)
    return resp.status_code, resp.json() if resp.status_code != 500 else resp.text

print('=' * 60)
print('FINEDGE COMPREHENSIVE END-TO-END TEST')
print('=' * 60)

# Test 1: Health Check
print('\n--- Test 1: Health Check ---')
r = requests.get(f'{BASE}/api/health/', timeout=30)
print(f'  Status: {r.status_code} {"PASS" if r.status_code == 200 else "FAIL"}')

# Test 2: Landing Page
print('\n--- Test 2: Landing Page ---')
r = requests.get(f'{BASE}/', timeout=30, allow_redirects=False)
print(f'  Status: {r.status_code} {"PASS" if r.status_code in (200, 301, 302) else "FAIL"}')

# Test 3: Admin Dashboard
print('\n--- Test 3: Admin Dashboard ---')
r = requests.get(f'{BASE}/api/dashboard/admin/', timeout=30)
print(f'  Status: {r.status_code} {"PASS" if r.status_code == 200 else "FAIL"}')

# Test 4-6: Officer Dashboards
for tc in ['nexus', 'fed', 'aura']:
    print(f'\n--- Test: Officer Dashboard {tc} ---')
    r = requests.get(f'{BASE}/api/dashboard/officer/{tc}/', timeout=30)
    print(f'  Status: {r.status_code} {"PASS" if r.status_code == 200 else "FAIL"}')

# Test 7: Contact Form
print('\n--- Test 7: Contact Form ---')
r = requests.post(f'{BASE}/api/contact/', json={
    'first_name': 'E2E', 'last_name': 'Test',
    'email': 'e2e@test.com', 'message': 'Automated test'
}, timeout=30)
print(f'  Status: {r.status_code} {"PASS" if r.status_code == 201 else "FAIL"}')

# Test 8-10: Submit Loans for each bank
app_ids = {}
for bank_name, api_key in KEYS.items():
    print(f'\n--- Test: Submit Loan ({bank_name}) ---')
    code, data = submit_loan(bank_name, api_key)
    print(f'  Status: {code} {"PASS" if code == 201 else "FAIL"}')
    if code == 201:
        app_ids[bank_name] = data['application_id']
        print(f'  App ID: {data["application_id"]}')
        print(f'  Ref: {data["tracking_reference"]}')
    else:
        print(f'  Response: {data}')

# Test 11-13: Application Status Check
for bank_name, app_id in app_ids.items():
    print(f'\n--- Test: Status Check ({bank_name}) ---')
    r = requests.get(f'{BASE}/api/v1/application/{app_id}/status/', timeout=30)
    print(f'  Status: {r.status_code} {"PASS" if r.status_code == 200 else "FAIL"}')
    if r.status_code == 200:
        print(f'  Data: {r.json()}')

# Test 14-16: Trigger TrustScore for each app
for bank_name, app_id in app_ids.items():
    print(f'\n--- Test: Trigger TrustScore ({bank_name}) ---')
    r = requests.post(f'{BASE}/api/v1/trigger_score/{app_id}/', timeout=30)
    print(f'  Status: {r.status_code} {"PASS" if r.status_code == 200 else "FAIL"}')
    if r.status_code == 200:
        print(f'  Data: {r.json()}')
    else:
        print(f'  Response: {r.text[:200]}')

print('\n' + '=' * 60)
print('ALL TESTS COMPLETE')
print('=' * 60)
