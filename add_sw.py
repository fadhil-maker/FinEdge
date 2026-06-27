import glob

# Add service worker registration script to all HTML files
html_files = glob.glob('simulator/*.html')

sw_script = '''
  <script>
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js');
    }
  </script>
'''

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'serviceWorker' not in content:
        content = content.replace('</head>', sw_script + '</head>')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print('Service worker registered in all HTML files')
