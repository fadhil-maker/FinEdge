import os
import django
import uuid
import random
from django.utils import timezone
from datetime import timedelta
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge_backend.settings')
django.setup()

from api_gateway.models import Bank, ApiCredential, SdkSession, LoanApplication, LoanApplicationStep, TrustScoreResult, BillingLedger
from api_gateway.views import _hash_api_key
from decimal import Decimal

def seed():
    nexus, _ = Bank.objects.get_or_create(tenant_code="nexus", defaults={"name": "NexusBank", "is_active": True})
    fed, _ = Bank.objects.get_or_create(tenant_code="fed", defaults={"name": "FedMobile", "is_active": True})
    aura, _ = Bank.objects.get_or_create(tenant_code="aura", defaults={"name": "Aura Capital", "is_active": True})
    
    nexus_hash = _hash_api_key("finedge_demo_api_key_2026")
    ApiCredential.objects.get_or_create(bank=nexus, hashed_key=nexus_hash, defaults={"label": "Simulator Key", "is_active": True})
    
    fed_hash = _hash_api_key("finedge_demo_fed")
    ApiCredential.objects.get_or_create(bank=fed, hashed_key=fed_hash, defaults={"label": "Fed Key", "is_active": True})
    
    for i in range(20):
        bank = random.choice([nexus, fed, aura])
        session = SdkSession.objects.create(
            bank=bank,
            device_hash_mask=f"device_{uuid.uuid4().hex[:8]}"
        )
        
        time_offset = timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 60))
        created = timezone.now() - time_offset
        
        app = LoanApplication.objects.create(
            bank=bank,
            sdk_session=session,
            tracking_reference=f"REF-{uuid.uuid4().hex[:8].upper()}",
            current_step=LoanApplicationStep.COMPLETED
        )
        LoanApplication.objects.filter(id=app.id).update(created_at=created)
        
        score = random.randint(450, 850)
        TrustScoreResult.objects.create(
            loan_application=app,
            calculated_score=score,
            mathematical_vector={"app_count": 10, "utility_sms": 5}
        )
        
        BillingLedger.objects.create(
            bank=bank,
            computed_charge=Decimal("10.0000"),
            processing_cycle_stamp=created.strftime("%Y-%m")
        )
    print('Dummy data successfully seeded!')

if __name__ == '__main__':
    seed()
