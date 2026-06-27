import re

files = ['simulator/nexus.html', 'simulator/fedmobile.html', 'simulator/aura.html']

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Hide consent modal by default
    content = content.replace('id="consentModal" class="fixed inset-0', 'id="consentModal" class="hidden fixed inset-0')
    
    # 2. Show app by default (remove opacity-0)
    content = content.replace('id="app" class="mobile-frame opacity-0', 'id="app" class="mobile-frame')
    
    # 3. Rewrite JS logic
    old_js = '''    // Consent
    consentCheckbox.addEventListener("change", () => {
      consentAcceptBtn.disabled = !consentCheckbox.checked;
    });
    consentAcceptBtn.addEventListener("click", () => {
      consentModal.classList.add("hidden");
      app.style.opacity = "1";
    });'''
    
    new_js = '''    // Consent
    consentCheckbox.addEventListener("change", () => {
      consentAcceptBtn.disabled = !consentCheckbox.checked;
    });
    
    // Launch button just shows the modal
    launchBtn.addEventListener("click", () => {
      consentModal.classList.remove("hidden");
    });'''
    
    content = content.replace(old_js, new_js)
    
    old_launch = '''    // Launch
    launchBtn.addEventListener("click", async () => {
      launchBtn.classList.add("hidden");'''
      
    new_launch = '''    // Consent Accept button triggers SDK
    consentAcceptBtn.addEventListener("click", async () => {
      consentModal.classList.add("hidden");
      launchBtn.classList.add("hidden");'''
      
    content = content.replace(old_launch, new_launch)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Files updated successfully")
