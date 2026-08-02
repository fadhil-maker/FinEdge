import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge_backend.settings')
django.setup()

from api_gateway.models import LoanApplication, TrustScoreResult, SdkSession, BillingLedger

print("Deleting BillingLedger...")
BillingLedger.objects.all().delete()

print("Deleting TrustScoreResult...")
TrustScoreResult.objects.all().delete()

print("Deleting LoanApplication...")
LoanApplication.objects.all().delete()

print("Deleting SdkSession...")
SdkSession.objects.all().delete()

print("Done wiping data.")
