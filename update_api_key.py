with open('simulator/engine.js', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('finedge_demo_api_key_2026', 'DqpYnf78.QPJum6C5BWiWtEJFq66fpN1Ayhul14Cm')

with open('simulator/engine.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("engine.js updated with new API key")
