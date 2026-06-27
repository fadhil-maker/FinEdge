with open('api_gateway/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'from rest_framework.decorators import authentication_classes' not in content:
    content = content.replace('from rest_framework.decorators import api_view, permission_classes', 'from rest_framework.decorators import api_view, permission_classes, authentication_classes')

old_deco = '''@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt'''

new_deco = '''@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt'''

content = content.replace(old_deco, new_deco)

with open('api_gateway/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added authentication_classes([]) to trigger_trust_score")
