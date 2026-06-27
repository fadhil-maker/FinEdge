import glob

html_files = glob.glob('simulator/*.html')
for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add apple-touch-icon if missing
    if 'apple-touch-icon' not in content:
        content = content.replace('<link rel="manifest" href="manifest.json">', '<link rel="manifest" href="manifest.json">\n    <link rel="apple-touch-icon" href="icon-192.png">')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print("Icons updated")
