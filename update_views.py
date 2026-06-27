import re

with open('api_gateway/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_view = '''from django.shortcuts import redirect

def landing_page(request):
    return redirect('https://fin-edge-ten.vercel.app/devweb/index.html')
'''

# Use regex to replace the landing_page function
# The original might be something like:
# def landing_page(request: HttpRequest) -> HttpResponse:
#     return render(request, "api_gateway/landing.html")

content = re.sub(r'def landing_page\(.*?\).*?:.*?(?=def |\Z)', new_view, content, flags=re.DOTALL)

with open('api_gateway/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Redirect applied")
