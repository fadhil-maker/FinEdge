import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finedge_backend.settings')
django.setup()

from api_gateway.models import ApiCredential, Bank
import hmac, hashlib

secret = b'finedge_hmac_shared_secret_2026'

for cred in ApiCredential.objects.select_related('bank').all():
    print(f'Bank: {cred.bank.name} ({cred.bank.tenant_code})')
    print(f'  is_active: {cred.is_active}')
    print(f'  hashed_key (first 20): {cred.hashed_key[:20]}...')
    print(f'  bank.is_active: {cred.bank.is_active}')
    print()

# Now test what hash the Nexus key produces
test_key = 'yJPJYfre.wYtJhJAJJkp6YzUd28yfEkAWVV3GvVbw'
computed = hmac.new(secret, test_key.encode('utf-8'), hashlib.sha256).hexdigest()
print(f'Nexus key hash: {computed[:20]}...')

matching = ApiCredential.objects.filter(hashed_key=computed)
print(f'Matching credentials: {matching.count()}')

# Test Fed key
test_key2 = 'SacLv7BE.Mux3G7ivugHwkJxUT8K4aiWCAQi30yZY'
computed2 = hmac.new(secret, test_key2.encode('utf-8'), hashlib.sha256).hexdigest()
print(f'Fed key hash: {computed2[:20]}...')
matching2 = ApiCredential.objects.filter(hashed_key=computed2)
print(f'Matching credentials: {matching2.count()}')
