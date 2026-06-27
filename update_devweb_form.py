with open('simulator/devweb/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

contact_section = '''
    <!-- Contact Section -->
    <section id="contact" class="py-24 bg-slate-900 border-t border-slate-800">
        <div class="container mx-auto px-6 max-w-4xl text-center">
            <h2 class="text-3xl md:text-5xl font-extrabold mb-6">Ready to Build?</h2>
            <p class="text-slate-400 mb-10 text-lg">Join the world's most innovative banks building privacy-first financial products. Request an API key to access our sandbox.</p>
            <form id="contactForm" onsubmit="event.preventDefault(); submitContactForm();" class="flex flex-col gap-4 justify-center max-w-lg mx-auto text-left">
                <input type="text" id="contactFirstName" placeholder="First Name" required class="px-6 py-4 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-primary">
                <input type="text" id="contactLastName" placeholder="Last Name" required class="px-6 py-4 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-primary">
                <input type="email" id="contactEmail" placeholder="work@bank.com" required class="px-6 py-4 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-primary">
                <textarea id="contactMessage" placeholder="How do you plan to use FinEdge?" required class="px-6 py-4 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-primary h-32"></textarea>
                <button type="submit" id="contactSubmitBtn" class="bg-primary hover:bg-blue-800 text-white px-8 py-4 rounded-xl font-bold transition-all shadow-lg shadow-blue-900/50 mt-2">Request API Key</button>
            </form>
            <script>
                async function submitContactForm() {
                    const btn = document.getElementById('contactSubmitBtn');
                    btn.innerText = 'Sending...';
                    btn.disabled = true;
                    try {
                        const res = await fetch('https://finedge-iy0i.onrender.com/api/contact/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                first_name: document.getElementById('contactFirstName').value,
                                last_name: document.getElementById('contactLastName').value,
                                email: document.getElementById('contactEmail').value,
                                message: document.getElementById('contactMessage').value
                            })
                        });
                        if(res.ok) {
                            alert('Thank you! Our sales team will review your request and send your sandbox API Key shortly.');
                            document.getElementById('contactForm').reset();
                        } else {
                            alert('Failed to send message.');
                        }
                    } catch(e) {
                        alert('Network error.');
                    }
                    btn.innerText = 'Request API Key';
                    btn.disabled = false;
                }
            </script>
        </div>
    </section>
'''

import re
content = re.sub(r'<!-- Contact Section -->.*?</section>', contact_section, content, flags=re.DOTALL)

with open('simulator/devweb/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated devweb contact form")
