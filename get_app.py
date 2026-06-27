import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge_backend.settings')
django.setup()
from api_gateway.models import LoanApplication
try:
    app = LoanApplication.objects.get(tracking_reference='REF-5541CF61')
    print(app.id)
except Exception as e:
    print(e)
