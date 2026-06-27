with open('simulator/engine.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the signature
content = content.replace('async function runEdgePipeline(terminal, apiUrl, requestedAmount, uiCallbacks = {}) {', 'async function runEdgePipeline(terminal, apiUrl, requestedAmount, profile, uiCallbacks = {}) {')

# Fix the generateSyntheticSMS call inside it
content = content.replace('let rawMessages = generateSyntheticSMS(40);', 'let rawMessages = generateSyntheticSMS(profile, 40);')
# Actually wait, in my previous replacement attempt I might have replaced it already.
# Let's check if 'generateSyntheticSMS(profile, 40)' is there.
# If not, replace the generic one.
if 'generateSyntheticSMS(profile, 40)' not in content:
    content = content.replace('generateSyntheticSMS(40)', 'generateSyntheticSMS(profile, 40)')

with open('simulator/engine.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("engine.js updated")
