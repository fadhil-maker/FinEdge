import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge_backend.settings')
django.setup()

from api_gateway.models import ApiCredential
import hmac, hashlib

secret = b'finedge_hmac_shared_secret_2026'

# Try the key stored in nexus.html
import re
with open('simulator/nexus.html', 'r', encoding='utf-8') as f:
    content = f.read()

keys = re.findall(r'\"([A-Za-z0-9]{8}\.[A-Za-z0-9]{32,})\"', content)
print(f'Keys found in nexus.html: {keys}')

for k in keys:
    h = hmac.new(secret, k.encode('utf-8'), hashlib.sha256).hexdigest()
    m = ApiCredential.objects.filter(hashed_key=h).count()
    print(f'  Key: {k[:16]}... -> hash: {h[:20]}... matches: {m}')

# Also check aura.html
with open('simulator/aura.html', 'r', encoding='utf-8') as f:
    content = f.read()

keys = re.findall(r'\"([A-Za-z0-9]{8}\.[A-Za-z0-9]{32,})\"', content)
print(f'Keys found in aura.html: {keys}')

for k in keys:
    h = hmac.new(secret, k.encode('utf-8'), hashlib.sha256).hexdigest()
    m = ApiCredential.objects.filter(hashed_key=h).count()
    print(f'  Key: {k[:16]}... -> hash: {h[:20]}... matches: {m}')
