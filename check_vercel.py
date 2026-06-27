import requests

resp = requests.get("https://fin-edge-ten.vercel.app/fedmobile.html")
if "SacLv7BE" in resp.text:
    print("Vercel has the new API key!")
elif "finedge_demo_fed" in resp.text:
    print("Vercel has the old prefix key!")
else:
    print("Vercel has some other code!")

resp = requests.get("https://fin-edge-ten.vercel.app/engine.v2.js")
if resp.status_code == 200:
    print("Vercel has engine.v2.js")
else:
    print(f"Vercel missing engine.v2.js! Status: {resp.status_code}")

