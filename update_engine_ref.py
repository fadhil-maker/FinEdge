import os

files = ['simulator/nexus.html', 'simulator/fedmobile.html', 'simulator/aura.html']
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('engine.js', 'engine.v2.js')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Updated references to engine.v2.js")
