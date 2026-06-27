# Update nexus.html
with open('simulator/nexus.html', 'r', encoding='utf-8') as f:
    nexus = f.read()
nexus = nexus.replace('"finedge_demo_nexus"', '"VgWTv8f0.wAQoI2ip4sNX1yk9ZaU1Z4UXJkGVjL6N"')
with open('simulator/nexus.html', 'w', encoding='utf-8') as f:
    f.write(nexus)

# Update fedmobile.html
with open('simulator/fedmobile.html', 'r', encoding='utf-8') as f:
    fed = f.read()
fed = fed.replace('"finedge_demo_fed"', '"SacLv7BE.Mux3G7ivugHwkJxUT8K4aiWCAQi30yZY"')
with open('simulator/fedmobile.html', 'w', encoding='utf-8') as f:
    f.write(fed)

# Update aura.html
with open('simulator/aura.html', 'r', encoding='utf-8') as f:
    aura = f.read()
aura = aura.replace('"finedge_demo_aura"', '"btTYC3BO.pmbjlfcY3po5W8x821SB5MazTIudxwpx"')
with open('simulator/aura.html', 'w', encoding='utf-8') as f:
    f.write(aura)

print("Updated with correct API Keys!")
