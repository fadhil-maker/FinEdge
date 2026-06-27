import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge.settings')
django.setup()

from api_gateway.models import Bank, ApiCredential
from api_gateway.views import _hash_api_key

nexus = Bank.objects.get(tenant_code='nexus')
fed = Bank.objects.get(tenant_code='fed')
aura = Bank.objects.get(tenant_code='aura')

ApiCredential.objects.all().delete()

k1_raw = 'VgWTv8f0.wAQoI2ip4sNX1yk9ZaU1Z4UXJkGVjL6N'
k2_raw = 'SacLv7BE.Mux3G7ivugHwkJxUT8K4aiWCAQi30yZY'
k3_raw = 'btTYC3BO.pmbjlfcY3po5W8x821SB5MazTIudxwpx'

ApiCredential.objects.create(bank=nexus, hashed_key=_hash_api_key(k1_raw), label='nexus-key', is_active=True)
ApiCredential.objects.create(bank=fed, hashed_key=_hash_api_key(k2_raw), label='fed-key', is_active=True)
ApiCredential.objects.create(bank=aura, hashed_key=_hash_api_key(k3_raw), label='aura-key', is_active=True)

print("Properly hashed ApiCredentials created!")
