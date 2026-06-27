with open('simulator/devweb/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('href="#contact"', 'href="../index.html"')

with open('simulator/devweb/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated devweb buttons")
