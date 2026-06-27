import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge.settings')
django.setup()

from api_gateway.models import Bank
from rest_framework_api_key.models import APIKey

nexus = Bank.objects.get(tenant_code='nexus')
fed = Bank.objects.get(tenant_code='fed')
aura = Bank.objects.get(tenant_code='aura')

APIKey.objects.all().delete()

k1, _ = APIKey.objects.create_key(name='nexus-demo-key')
k1.prefix = 'finedge_demo_nexus'
k1.save()
print(f"Nexus Key: {k1.prefix}")

k2, _ = APIKey.objects.create_key(name='fed-demo-key')
k2.prefix = 'finedge_demo_fed'
k2.save()
print(f"Fed Key: {k2.prefix}")

k3, _ = APIKey.objects.create_key(name='aura-demo-key')
k3.prefix = 'finedge_demo_aura'
k3.save()
print(f"Aura Key: {k3.prefix}")
