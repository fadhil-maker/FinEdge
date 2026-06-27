banks = [
    ('simulator/nexus.html', 'manifest-nexus.json', 'icon-nexus-192.png', 'NexusBank'),
    ('simulator/fedmobile.html', 'manifest-fedmobile.json', 'icon-fedmobile-192.png', 'FedMobile'),
    ('simulator/aura.html', 'manifest-aura.json', 'icon-aura-192.png', 'Aura Capital'),
]

for filepath, manifest, icon, name in banks:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace shared manifest with bank-specific manifest
    content = content.replace('href=\"manifest.json\"', f'href=\"{manifest}\"')
    
    # Replace shared icon with bank-specific icon
    content = content.replace('href=\"icon-192.png\"', f'href=\"{icon}\"')
    
    # Add apple-mobile-web-app-title for correct name on iOS home screen
    if 'apple-mobile-web-app-title' not in content:
        content = content.replace(
            '<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">',
            f'<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n    <meta name=\"apple-mobile-web-app-title\" content=\"{name}\">'
        )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print('All bank HTML files updated with individual manifests')
