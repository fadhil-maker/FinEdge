for file in ['simulator/nexus.html', 'simulator/fedmobile.html', 'simulator/aura.html']:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('engine.v2.js', 'engine.v2.js?v=4')
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Updated script references to bust cache!")
