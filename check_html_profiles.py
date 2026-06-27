for file in ['simulator/nexus.html', 'simulator/fedmobile.html', 'simulator/aura.html']:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    import re
    m = re.search(r'runEdgePipeline\(.*?\)', content)
    if m:
        print(f"{file}: {m.group(0)}")
