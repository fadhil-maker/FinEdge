with open('api_gateway/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'from django.views.decorators.csrf import csrf_exempt' not in content:
    content = content.replace('from rest_framework.decorators import api_view, permission_classes', 'from rest_framework.decorators import api_view, permission_classes\nfrom django.views.decorators.csrf import csrf_exempt')

content = content.replace('@api_view(["POST"])\n@permission_classes([AllowAny])\ndef trigger_trust_score', '@api_view(["POST"])\n@permission_classes([AllowAny])\n@csrf_exempt\ndef trigger_trust_score')

with open('api_gateway/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added csrf_exempt to trigger_trust_score")
