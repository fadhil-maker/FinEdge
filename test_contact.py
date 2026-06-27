import requests

# The contact form URL should be /api/contact/ not /api/v1/contact/
resp = requests.post('https://finedge-iy0i.onrender.com/api/contact/', json={'first_name': 'Test', 'last_name': 'User', 'email': 'test@test.com', 'message': 'Hello'})
print(f'Status: {resp.status_code}')
print(f'Content: {resp.text}')
