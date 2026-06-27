import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge.settings')
import django
django.setup()

from api_gateway.models import LoanApplication
from api_gateway.pipeline import evaluate_application

app = LoanApplication.objects.last()
print(f"Latest App ID: {app.id}")
try:
    res = evaluate_application(app.trust_score.mathematical_vector)
    print(f"Score: {res.trust_score}")
except Exception as e:
    print(f"Error evaluating: {e}")
