import re

with open('simulator/engine.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace generateSyntheticSMS
new_generate = '''function generateSyntheticSMS(profile = "average", count = 40) {
  const good_templates = [
    { sender: "HDFCBK", body: "INR 85,000.00 credited to your a/c XX5678 by NEFT. Balance is INR 1,23,450.00" },
    { sender: "SBIINB", body: "Dear Customer, your EMI of INR 8,500 has been debited from a/c XX1234. Avl Bal: INR 1,14,950.00" },
    { sender: "ICICIB", body: "Your a/c XX9012 debited Rs.1,200 for electricity bill payment. Avl Bal Rs.1,13,750.00" },
    { sender: "AXISBK", body: "Rs.5,000.00 credited to your Axis Bank a/c XX3456 via UPI. Bal: Rs.1,18,750.00" },
    { sender: "GPAY", body: "You paid ?1,500.00 to BigBasket using Google Pay. UPI ref GPY123" }
  ];

  const average_templates = [
    { sender: "SBIINB", body: "INR 25,000.00 credited to your a/c XX5678. Balance is INR 35,450.00" },
    { sender: "HDFCBK", body: "Dear Customer, your EMI of INR 4,500 has been debited. Avl Bal: INR 30,950.00" },
    { sender: "AXISBK", body: "EMI bounce alert: Your EMI of INR 4,500 has failed due to insufficient balance" },
    { sender: "AXISBK", body: "Rs.5,000.00 credited to your Axis Bank a/c XX3456. Bal: Rs.35,950.00" },
    { sender: "PAYTMB", body: "?350.00 paid to Zomato via Paytm UPI. Balance: ?35,600.00" }
  ];

  const bad_templates = [
    { sender: "HDFCBK", body: "EMI bounce alert: Your EMI of INR 2,000 has failed due to insufficient balance" },
    { sender: "SBIINB", body: "URGENT: EMI instalment overdue for Loan XX6543. Amount: Rs.5,200." },
    { sender: "ICICIB", body: "Your a/c XX9012 debited Rs.100. Avl Bal Rs.450.00" },
    { sender: "AXISBK", body: "EMI bounce alert: Your EMI of INR 1,500 has failed due to insufficient balance" },
    { sender: "PHONEPE", body: "You paid ?50.00 to Tea Stall via PhonePe. Avl Bal: Rs.400.00" }
  ];

  let templates = average_templates;
  if (profile === "good") templates = good_templates;
  if (profile === "bad") templates = bad_templates;

  const messages = [];
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const tmpl = templates[i % templates.length];
    messages.push({
      sender: tmpl.sender,
      body: tmpl.body,
      timestamp: new Date(now - i * 3600000).toISOString(),
    });
  }

  return messages;
}'''

# Replace the old generateSyntheticSMS function using regex
content = re.sub(r'function generateSyntheticSMS\(count = 40\) \{.*?\n\}', new_generate, content, flags=re.DOTALL)

# Update runEdgePipeline signature
content = content.replace('async function runEdgePipeline(terminal, apiUrl, requestedAmount, callbacks) {', 'async function runEdgePipeline(terminal, apiUrl, requestedAmount, profile, callbacks) {')

# Update generateSyntheticSMS call inside runEdgePipeline
content = content.replace('let rawMessages = generateSyntheticSMS(40);', 'let rawMessages = generateSyntheticSMS(profile, 40);')

with open('simulator/engine.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("engine.js updated")
