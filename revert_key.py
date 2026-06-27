with open('simulator/engine.js', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('DqpYnf78.QPJum6C5BWiWtEJFq66fpN1Ayhul14Cm', 'finedge_demo_api_key_2026')

with open('simulator/engine.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("engine.js reverted to original API key")
