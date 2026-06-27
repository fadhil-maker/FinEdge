import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge.settings')
django.setup()

from api_gateway.models import LoanApplication

apps = LoanApplication.objects.all().order_by('-created_at')[:5]
print(f"Total apps in DB: {LoanApplication.objects.count()}")
for app in apps:
    print(f"ID: {app.id}, Bank: {app.bank.tenant_code}, Step: {app.current_step}")
