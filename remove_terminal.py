import glob

for filepath in glob.glob('simulator/*.html'):
    if 'index' in filepath:
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '<div class="flex items-center gap-2 mb-2">\n          <svg class="w-4 h-4 text-finedge animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /></svg>\n          <span class="text-xs font-bold text-slate-700">Secured by FinEdge SDK</span>\n        </div>\n        <div class="secure-terminal" id="terminalOutput"></div>'
    
    new = '<div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 text-center">\n          <div class="w-14 h-14 mx-auto mb-4 rounded-full bg-bank-light flex items-center justify-center">\n            <svg class="w-7 h-7 text-bank animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>\n          </div>\n          <h4 class="text-sm font-bold text-slate-800 mb-1">Verifying your profile...</h4>\n          <p class="text-xs text-slate-500">This usually takes a few seconds</p>\n          <div class="flex items-center justify-center gap-1.5 mt-3">\n            <span class="text-[10px] text-slate-400">Secured by FinEdge</span>\n          </div>\n        </div>\n        <div class="hidden"><div id="terminalOutput"></div></div>'
    
    content = content.replace(old, new)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print('Done')