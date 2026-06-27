with open('simulator/devweb/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('href="../index.html"', 'href="#contact"')

# Now append a contact section before the footer
contact_section = '''
    <!-- Contact Section -->
    <section id="contact" class="py-24 bg-slate-900 border-t border-slate-800">
        <div class="container mx-auto px-6 max-w-4xl text-center">
            <h2 class="text-3xl md:text-5xl font-extrabold mb-6">Ready to Build?</h2>
            <p class="text-slate-400 mb-10 text-lg">Join the world's most innovative banks building privacy-first financial products. Request an API key to access our sandbox.</p>
            <form onsubmit="event.preventDefault(); alert('Thank you! Our sales team will email your sandbox API Key shortly.');" class="flex flex-col md:flex-row gap-4 justify-center max-w-2xl mx-auto">
                <input type="email" placeholder="work@bank.com" required class="px-6 py-4 rounded-full bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-primary flex-grow">
                <button type="submit" class="bg-primary hover:bg-blue-800 text-white px-8 py-4 rounded-full font-bold transition-all shadow-lg shadow-blue-900/50 whitespace-nowrap">Request API Key</button>
            </form>
        </div>
    </section>
'''

content = content.replace('<!-- Footer -->', contact_section + '\n    <!-- Footer -->')

with open('simulator/devweb/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Contact section added to devweb")
