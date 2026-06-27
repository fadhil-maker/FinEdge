import requests

resp = requests.get("https://finedge-iy0i.onrender.com/api/dashboard/officer/nexus/")
if "triggerTrustScore(" in resp.text:
    idx = resp.text.find("triggerTrustScore('")
    if idx != -1:
        appId = resp.text[idx+19:idx+55]
        print(f"Found appId: {appId}")
        r2 = requests.post(f"https://finedge-iy0i.onrender.com/api/v1/trigger_score/{appId}/")
        print(f"Trigger Status: {r2.status_code}")
        print(f"Trigger Response: {r2.text}")
    else:
        print("No appId found in HTML")
else:
    print("No triggerTrustScore found")
