with open('simulator/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the single Officer link with a button that opens a modal
old_button = '''<a href="https://finedge-iy0i.onrender.com/api/dashboard/officer/nexus/" target="_blank" class="flex items-center gap-3 bg-slate-800/80 border border-slate-700/50 p-4 rounded-2xl hover:bg-slate-700 transition-colors">
                <div class="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-white">Officer</h3>
                    <p class="text-[10px] text-slate-400">Review Dashboard</p>
                </div>
            </a>'''

new_button = '''<button onclick="document.getElementById('bankModal').classList.remove('hidden')" class="flex items-center gap-3 bg-slate-800/80 border border-slate-700/50 p-4 rounded-2xl hover:bg-slate-700 transition-colors text-left w-full">
                <div class="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-white">Officer</h3>
                    <p class="text-[10px] text-slate-400">Review Dashboard</p>
                </div>
            </button>'''

modal_html = '''
    <!-- Bank Selection Modal -->
    <div id="bankModal" class="fixed inset-0 bg-slate-900/80 z-50 hidden flex items-center justify-center px-4 backdrop-blur-sm transition-all duration-300">
        <div class="bg-slate-800 rounded-3xl w-full max-w-sm p-6 border border-slate-700 shadow-2xl">
            <h3 class="text-lg font-bold text-white mb-4">Select Bank Dashboard</h3>
            <div class="space-y-3">
                <a href="https://finedge-iy0i.onrender.com/api/dashboard/officer/nexus/" target="_blank" onclick="document.getElementById('bankModal').classList.add('hidden')" class="flex items-center gap-4 p-4 rounded-2xl bg-slate-700/50 hover:bg-slate-700 transition-colors">
                    <img src="icon-nexus-192.png" class="w-10 h-10 rounded-xl" alt="Nexus">
                    <span class="font-semibold text-white">NexusBank</span>
                </a>
                <a href="https://finedge-iy0i.onrender.com/api/dashboard/officer/fed/" target="_blank" onclick="document.getElementById('bankModal').classList.add('hidden')" class="flex items-center gap-4 p-4 rounded-2xl bg-slate-700/50 hover:bg-slate-700 transition-colors">
                    <img src="icon-fedmobile-192.png" class="w-10 h-10 rounded-xl" alt="Fed">
                    <span class="font-semibold text-white">FedMobile</span>
                </a>
                <a href="https://finedge-iy0i.onrender.com/api/dashboard/officer/aura/" target="_blank" onclick="document.getElementById('bankModal').classList.add('hidden')" class="flex items-center gap-4 p-4 rounded-2xl bg-slate-700/50 hover:bg-slate-700 transition-colors">
                    <img src="icon-aura-192.png" class="w-10 h-10 rounded-xl" alt="Aura">
                    <span class="font-semibold text-white">Aura Capital</span>
                </a>
            </div>
            <button onclick="document.getElementById('bankModal').classList.add('hidden')" class="mt-6 w-full py-3 rounded-full bg-slate-700 text-white font-semibold text-sm hover:bg-slate-600 transition-colors">Cancel</button>
        </div>
    </div>
</body>
'''

content = content.replace(old_button, new_button)
content = content.replace('</body>', modal_html)

with open('simulator/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated officer dashboard modal logic")
