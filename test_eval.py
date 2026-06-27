import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge_backend.settings')
django.setup()
from api_gateway.models import LoanApplication
from api_gateway.pipeline import evaluate_application
app = LoanApplication.objects.get(tracking_reference='REF-5541CF61')
print(f"Vector: {app.trust_score.mathematical_vector}")
try:
    res = evaluate_application(app.trust_score.mathematical_vector)
    print(f"Success: {res.trust_score}")
except Exception as e:
    print(f"Exception: {repr(e)}")
