with open('simulator/nexus.html', 'r', encoding='utf-8') as f:
    nexus = f.read()

# ===== FEDMOBILE =====
fed = nexus
fed = fed.replace("NexusBank", "FedMobile")
fed = fed.replace("manifest-nexus.json", "manifest-fedmobile.json")
fed = fed.replace("icon-nexus-192.png", "icon-fedmobile-192.png")
fed = fed.replace("'bank': '#1e3a8a'", "'bank': '#047857'")
fed = fed.replace("'bank-dark': '#1e2d5e'", "'bank-dark': '#065f46'")
fed = fed.replace("'bank-light': '#eff6ff'", "'bank-light': '#ecfdf5'")
fed = fed.replace("'bank-accent': '#f59e0b'", "'bank-accent': '#10b981'")
fed = fed.replace("shadow-blue-900/30", "shadow-emerald-900/30")
fed = fed.replace("shadow-amber-500/25", "shadow-emerald-500/25")
fed = fed.replace("from-bank to-blue-700", "from-bank to-emerald-700")
fed = fed.replace("text-blue-200", "text-emerald-200")
fed = fed.replace("John Doe", "Priya Sharma")
fed = fed.replace(">JD<", ">PS<")
fed = fed.replace("?1,24,500", "?2,18,350")
fed = fed.replace("Good Morning", "Welcome back")

with open('simulator/fedmobile.html', 'w', encoding='utf-8') as f:
    f.write(fed)

# ===== AURA CAPITAL =====
aura = nexus
aura = aura.replace("NexusBank", "Aura Capital")
aura = aura.replace("manifest-nexus.json", "manifest-aura.json")
aura = aura.replace("icon-nexus-192.png", "icon-aura-192.png")
aura = aura.replace("'bank': '#1e3a8a'", "'bank': '#5b21b6'")
aura = aura.replace("'bank-dark': '#1e2d5e'", "'bank-dark': '#4c1d95'")
aura = aura.replace("'bank-light': '#eff6ff'", "'bank-light': '#f5f3ff'")
aura = aura.replace("'bank-accent': '#f59e0b'", "'bank-accent': '#8b5cf6'")
aura = aura.replace("shadow-blue-900/30", "shadow-violet-900/30")
aura = aura.replace("shadow-amber-500/25", "shadow-violet-500/25")
aura = aura.replace("from-bank to-blue-700", "from-bank to-violet-700")
aura = aura.replace("text-blue-200", "text-violet-200")
aura = aura.replace("John Doe", "Rahul Mehta")
aura = aura.replace(">JD<", ">RM<")
aura = aura.replace("?1,24,500", "?3,45,800")
aura = aura.replace("Good Morning", "Hello")

with open('simulator/aura.html', 'w', encoding='utf-8') as f:
    f.write(aura)

print('All 3 banks rebuilt!')
