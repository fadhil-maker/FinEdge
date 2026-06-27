from api_gateway.models import Bank, ApiCredential
from rest_framework_api_key.models import APIKey

nexus = Bank.objects.get(tenant_code='nexus')
fed = Bank.objects.get(tenant_code='fed')
aura = Bank.objects.get(tenant_code='aura')

ApiCredential.objects.all().delete()
APIKey.objects.all().delete()

k1, raw1 = APIKey.objects.create_key(name='nexus-demo')
ApiCredential.objects.create(bank=nexus, api_key=k1, hashed_key=k1.hashed_key)

k2, raw2 = APIKey.objects.create_key(name='fed-demo')
ApiCredential.objects.create(bank=fed, api_key=k2, hashed_key=k2.hashed_key)

k3, raw3 = APIKey.objects.create_key(name='aura-demo')
ApiCredential.objects.create(bank=aura, api_key=k3, hashed_key=k3.hashed_key)

import json
print(json.dumps({"nexus": raw1, "fed": raw2, "aura": raw3}))
