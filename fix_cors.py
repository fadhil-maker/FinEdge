with open('finedge_backend/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the dynamic CORS check with a hardcoded True
old_cors = '''_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
if _cors_origins:
    CORS_ALLOWED_ORIGINS = _cors_origins.split(",")
    CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOWED_ORIGINS = []
    CORS_ALLOW_ALL_ORIGINS = True'''

new_cors = '''CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True'''

if old_cors in content:
    content = content.replace(old_cors, new_cors)
else:
    content += "\nCORS_ALLOW_ALL_ORIGINS = True\nCORS_ALLOW_CREDENTIALS = True\n"

with open('finedge_backend/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Forced CORS_ALLOW_ALL_ORIGINS in settings.py")
