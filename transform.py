import re

files = [
    ('simulator/nexus.html', 'nexus-blue', 'nexus-light', 'nexus-accent'),
    ('simulator/fedmobile.html', 'fed-primary', 'fed-light', 'fed-accent'),
    ('simulator/aura.html', 'aura-primary', 'aura-light', 'aura-accent')
]

for filepath, primary, light, accent in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. PWA Meta Tags
    pwa_tags = '''<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="manifest" href="manifest.json">'''
    
    content = content.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', pwa_tags)

    # 2. Extract Loan Offer Card, Processing Section, and Result Card
    # We will wrap the existing main content into two screens
    
    # Let's find the start of <!-- Main Content -->
    main_content_marker = '<!-- Main Content -->\n    <div class="px-5 -mt-6 flex-1 flex flex-col">'
    
    # We want to replace it with a container for the screens
    new_main_container = f'''<!-- Main Content -->
    <div class="px-5 -mt-6 flex-1 flex flex-col relative overflow-hidden" id="screenContainer">
      <!-- Hidden Config for API -->
      <input type="hidden" id="apiUrlInput" value="https://finedge-iy0i.onrender.com/api/v1/score/" />

      <!-- HOME SCREEN -->
      <div id="homeScreen" class="w-full flex-1 flex flex-col transition-transform duration-300 transform translate-x-0">
        
        <!-- Services Grid -->
        <div class="bg-white rounded-2xl shadow-lg border border-slate-100 p-4 mb-5">
            <h4 class="text-xs font-bold text-slate-800 mb-3">Quick Actions</h4>
            <div class="grid grid-cols-4 gap-2 text-center">
                <div id="openLoanScreenBtn" class="flex flex-col items-center gap-1 cursor-pointer">
                    <div class="w-12 h-12 rounded-full bg-{light} flex items-center justify-center text-{primary}">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    </div>
                    <span class="text-[9px] font-bold text-slate-600">Mini Loan</span>
                </div>
                <div class="flex flex-col items-center gap-1 opacity-50">
                    <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                    </div>
                    <span class="text-[9px] font-bold text-slate-600">Gold Loan</span>
                </div>
                <div class="flex flex-col items-center gap-1 opacity-50">
                    <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>
                    </div>
                    <span class="text-[9px] font-bold text-slate-600">Utility</span>
                </div>
                <div class="flex flex-col items-center gap-1 opacity-50">
                    <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                    </div>
                    <span class="text-[9px] font-bold text-slate-600">Transfer</span>
                </div>
            </div>
        </div>

        <!-- Recent Transactions Mock -->
        <div class="mt-auto pb-6">
          <h4 class="text-xs font-bold text-slate-800 mb-3">Recent Transactions</h4>
          <div class="space-y-3">
            <div class="flex justify-between items-center bg-white p-3 rounded-xl border border-slate-100">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center text-orange-600"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg></div>
                <div><p class="text-xs font-bold text-slate-800">Electricity Bill</p><p class="text-[10px] text-slate-400">Today</p></div>
              </div>
              <div class="text-xs font-bold text-slate-800">-?1,240</div>
            </div>
            <div class="flex justify-between items-center bg-white p-3 rounded-xl border border-slate-100">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg></div>
                <div><p class="text-xs font-bold text-slate-800">Salary Credit</p><p class="text-[10px] text-slate-400">Yesterday</p></div>
              </div>
              <div class="text-xs font-bold text-green-600">+?85,000</div>
            </div>
          </div>
        </div>
      </div>

      <!-- LOAN SCREEN -->
      <div id="loanScreen" class="w-full flex-1 flex flex-col absolute top-0 left-0 transition-transform duration-300 transform translate-x-full bg-[#f8fafc] px-5 pt-1 h-full z-10">
        
        <div class="flex items-center gap-3 mb-4 -mx-2 cursor-pointer" id="backToHomeBtn">
            <svg class="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            <span class="text-sm font-bold text-slate-600">Back to Dashboard</span>
        </div>
'''
    
    # We replace the original main_content_marker
    content = content.replace(main_content_marker, new_main_container)
    
    # We need to remove the original <input type="hidden" id="apiUrlInput"...> because we moved it up.
    content = re.sub(r'<!-- Hidden Config for API -->\s*<input type="hidden" id="apiUrlInput".*?/>', '', content)
    
    # We need to remove the original Recent Transactions Mock from the bottom of the file
    original_transactions = r'<!-- Recent Transactions Mock -->\s*<div class="mt-auto">.*?</div>\s*</div>\s*</div>\s*</div>'
    # Wait, regex dotall is tricky here. I will just do string slicing.
    
    start_idx = content.find('<!-- Recent Transactions Mock -->')
    if start_idx != -1:
        # Find the closing tag of the Recent Transactions div. 
        # Actually, it's easier to just find the end of the loanScreen and close the divs properly.
        # The original file had the Recent transactions at the bottom.
        
        # Let's use regex to remove the original Recent Transactions block
        # It's roughly 20 lines.
        content = re.sub(r'<!-- Recent Transactions Mock -->.*?</div>\s*</div>\s*</div>', '</div>\n      </div>', content, flags=re.DOTALL)
        
    # We need to add JS to handle navigation
    nav_js = '''
    const homeScreen = #homeScreen;
    const loanScreen = #loanScreen;
    const openLoanScreenBtn = #openLoanScreenBtn;
    const backToHomeBtn = #backToHomeBtn;
    
    openLoanScreenBtn.addEventListener("click", () => {
        homeScreen.classList.add("-translate-x-full");
        loanScreen.classList.remove("translate-x-full");
    });
    
    backToHomeBtn.addEventListener("click", () => {
        homeScreen.classList.remove("-translate-x-full");
        loanScreen.classList.add("translate-x-full");
    });
'''
    
    content = content.replace('const consentModal = #consentModal;', nav_js + '\n    const consentModal = #consentModal;')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Files transformed!")
