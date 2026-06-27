for file in ['simulator/nexus.html', 'simulator/fedmobile.html', 'simulator/aura.html']:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('max="500"', 'max="5000"')
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Fixed slider max values!")
