import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge_backend.settings')
django.setup()

from api_gateway.models import Bank, ApiCredential
from api_gateway.views import _hash_api_key

def seed():
    nexus, _ = Bank.objects.get_or_create(tenant_code="nexus", defaults={"name": "NexusBank", "is_active": True})
    fed, _ = Bank.objects.get_or_create(tenant_code="fed", defaults={"name": "FedMobile", "is_active": True})
    aura, _ = Bank.objects.get_or_create(tenant_code="aura", defaults={"name": "Aura Capital", "is_active": True})
    
    nexus_hash = _hash_api_key("finedge_demo_api_key_2026")
    ApiCredential.objects.get_or_create(bank=nexus, hashed_key=nexus_hash, defaults={"label": "Simulator Key", "is_active": True})
    
    print('Clean banks and credentials successfully seeded!')

if __name__ == '__main__':
    seed()
