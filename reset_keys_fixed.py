from api_gateway.models import Bank, ApiCredential
import hashlib

nexus = Bank.objects.get(tenant_code='nexus')
fed = Bank.objects.get(tenant_code='fed')
aura = Bank.objects.get(tenant_code='aura')

ApiCredential.objects.all().delete()

k1_raw = 'finedge_demo_nexus'
k2_raw = 'finedge_demo_fed'
k3_raw = 'finedge_demo_aura'

ApiCredential.objects.create(bank=nexus, hashed_key=hashlib.sha256(k1_raw.encode()).hexdigest(), label='nexus-key', is_active=True)
ApiCredential.objects.create(bank=fed, hashed_key=hashlib.sha256(k2_raw.encode()).hexdigest(), label='fed-key', is_active=True)
ApiCredential.objects.create(bank=aura, hashed_key=hashlib.sha256(k3_raw.encode()).hexdigest(), label='aura-key', is_active=True)

print("Created ApiCredentials for the 3 keys!")
