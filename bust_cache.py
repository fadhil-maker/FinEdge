with open('simulator/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('nexus.html', 'nexus.html?v=3')
content = content.replace('fedmobile.html', 'fedmobile.html?v=3')
content = content.replace('aura.html', 'aura.html?v=3')

with open('simulator/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated index.html to bust cache!")
