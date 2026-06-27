with open('simulator/engine.v2.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Update signature
content = content.replace('async function runEdgePipeline(terminal, apiUrl, requestedAmount, profile, uiCallbacks = {})', 'async function runEdgePipeline(terminal, apiUrl, apiKey, requestedAmount, profile, uiCallbacks = {})')

# Update fetch Authorization header
content = content.replace('"Authorization": "Api-Key finedge_demo_api_key_2026"', '"Authorization": "Api-Key " + apiKey')

with open('simulator/engine.v2.js', 'w', encoding='utf-8') as f:
    f.write(content)

# Update nexus.html
with open('simulator/nexus.html', 'r', encoding='utf-8') as f:
    nexus = f.read()
nexus = nexus.replace('await window.FinEdge.runEdgePipeline(terminal, apiUrl, requestedAmount, "good",', 'await window.FinEdge.runEdgePipeline(terminal, apiUrl, "finedge_demo_nexus", requestedAmount, "good",')
with open('simulator/nexus.html', 'w', encoding='utf-8') as f:
    f.write(nexus)

# Update fedmobile.html
with open('simulator/fedmobile.html', 'r', encoding='utf-8') as f:
    fed = f.read()
fed = fed.replace('await window.FinEdge.runEdgePipeline(terminal, apiUrl, requestedAmount, "average",', 'await window.FinEdge.runEdgePipeline(terminal, apiUrl, "finedge_demo_fed", requestedAmount, "average",')
with open('simulator/fedmobile.html', 'w', encoding='utf-8') as f:
    f.write(fed)

# Update aura.html
with open('simulator/aura.html', 'r', encoding='utf-8') as f:
    aura = f.read()
aura = aura.replace('await window.FinEdge.runEdgePipeline(terminal, apiUrl, requestedAmount, "bad",', 'await window.FinEdge.runEdgePipeline(terminal, apiUrl, "finedge_demo_aura", requestedAmount, "bad",')
with open('simulator/aura.html', 'w', encoding='utf-8') as f:
    f.write(aura)

print("Updated API Keys in frontend!")
