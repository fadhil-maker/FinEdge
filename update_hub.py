with open('simulator/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add a new section below the App Grid for Dashboards
old_footer = '<!-- Footer -->'

new_dashboards = '''<!-- Dashboards -->
    <div class="w-full max-w-sm mb-12">
        <h2 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 pl-2">Portals</h2>
        <div class="grid grid-cols-2 gap-4">
            <a href="devweb/index.html" class="flex items-center gap-3 bg-slate-800/80 border border-slate-700/50 p-4 rounded-2xl hover:bg-slate-700 transition-colors">
                <div class="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center text-blue-400">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-white">Developer</h3>
                    <p class="text-[10px] text-slate-400">B2B SaaS Portal</p>
                </div>
            </a>
            
            <a href="https://finedge-iy0i.onrender.com/admin/" target="_blank" class="flex items-center gap-3 bg-slate-800/80 border border-slate-700/50 p-4 rounded-2xl hover:bg-slate-700 transition-colors">
                <div class="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-white">Officer</h3>
                    <p class="text-[10px] text-slate-400">Review Dashboard</p>
                </div>
            </a>
        </div>
    </div>
    
    <!-- Footer -->'''

if '<!-- Dashboards -->' not in content:
    content = content.replace(old_footer, new_dashboards)

with open('simulator/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Dashboards linked to Hub")
