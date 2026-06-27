from PIL import Image, ImageDraw

banks = [
    {
        'name': 'NexusBank',
        'short': 'Nexus',
        'file': 'nexus',
        'bg': (30, 58, 138),
        'accent': (245, 158, 11),
        'theme': '#1e3a8a'
    },
    {
        'name': 'FedMobile',
        'short': 'FedMobile',
        'file': 'fedmobile',
        'bg': (4, 120, 87),
        'accent': (16, 185, 129),
        'theme': '#047857'
    },
    {
        'name': 'Aura Capital',
        'short': 'Aura',
        'file': 'aura',
        'bg': (91, 33, 182),
        'accent': (139, 92, 246),
        'theme': '#5b21b6'
    }
]

import json

for bank in banks:
    # Generate icon
    for size in [192, 512]:
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Rounded rectangle background
        margin = int(size * 0.05)
        radius = int(size * 0.18)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=radius, fill=bank['bg'])
        
        # Lightning bolt
        cx, cy = size // 2, size // 2
        s = size / 512.0
        bolt = [
            (int(cx + 16*s), int(cy - 160*s)),
            (int(cx - 80*s), int(cy + 32*s)),
            (int(cx - 16*s), int(cy + 32*s)),
            (int(cx - 32*s), int(cy + 160*s)),
            (int(cx + 80*s), int(cy - 32*s)),
            (int(cx + 16*s), int(cy - 32*s)),
        ]
        draw.polygon(bolt, fill=bank['accent'])
        
        img.save(f'simulator/icon-{bank["file"]}-{size}.png')
    
    # Generate manifest
    manifest = {
        'name': bank['name'],
        'short_name': bank['short'],
        'start_url': f'./{bank["file"]}.html',
        'display': 'standalone',
        'background_color': bank['theme'],
        'theme_color': bank['theme'],
        'orientation': 'portrait',
        'icons': [
            {
                'src': f'./icon-{bank["file"]}-192.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any maskable'
            },
            {
                'src': f'./icon-{bank["file"]}-512.png',
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any maskable'
            }
        ]
    }
    
    with open(f'simulator/manifest-{bank["file"]}.json', 'w') as f:
        json.dump(manifest, f, indent=2)

print('All bank icons and manifests generated')
