import re

def update_html(filename, balance, profile):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update balance display - we need to replace whatever the current balance is
    # The current balances are: Nexus ?1,24,500, FedMobile ?2,18,350, Aura ?3,45,800
    # Let's just use regex to replace the h2 tag content
    content = re.sub(r'<h2 class="text-2xl font-black tracking-tight">?.*?<span', f'<h2 class="text-2xl font-black tracking-tight">?{balance}<span', content)

    # Update runEdgePipeline call
    # Old: await window.FinEdge.runEdgePipeline(terminal, apiUrl, requestedAmount, {
    # New: await window.FinEdge.runEdgePipeline(terminal, apiUrl, requestedAmount, "profile", {
    content = content.replace('await window.FinEdge.runEdgePipeline(terminal, apiUrl, requestedAmount, {', f'await window.FinEdge.runEdgePipeline(terminal, apiUrl, requestedAmount, "{profile}", {{')
    
    # Also update the promo banner to show realistic amounts based on balance
    if profile == "bad":
        content = content.replace('Get up to ?5,000 in seconds', 'Get up to ?500 in seconds')
        content = content.replace('max="5000"', 'max="500"')
        content = content.replace('value="2000"', 'value="500"')
        content = content.replace('<span>?5,000</span>', '<span>?500</span>')
        content = content.replace('>2000<', '>500<')
    elif profile == "average":
        content = content.replace('Get up to ?5,000 in seconds', 'Get up to ?2,000 in seconds')
        content = content.replace('max="5000"', 'max="2000"')
        content = content.replace('<span>?5,000</span>', '<span>?2,000</span>')

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

update_html('simulator/nexus.html', '400', 'good')
update_html('simulator/fedmobile.html', '150', 'average')
update_html('simulator/aura.html', '10', 'bad')

print("All HTML files updated")
