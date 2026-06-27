import requests

# Let's hit the trigger endpoint without CSRF
# We need an application ID
from api_gateway.models import LoanApplication
app_id = LoanApplication.objects.last().id

resp = requests.post(f"https://finedge-iy0i.onrender.com/api/v1/trigger_score/{app_id}/")
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")
