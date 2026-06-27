with open('simulator/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('https://finedge-iy0i.onrender.com/admin/', 'https://finedge-iy0i.onrender.com/dashboard/officer/nexus/')

with open('simulator/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated officer dashboard link")
