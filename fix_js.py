with open('api_gateway/templates/api_gateway/officer_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_script = '''    <script>
      async function triggerTrustScore(appId) {
        if (!confirm("Running FinEdge TrustScore incurs a ?10 API fee. Proceed?")) return;
        
        try {
            const csrfToken = "{{ csrf_token }}";
            const response = await fetch(/api/v1/trigger_score//, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });
            const data = await response.json();
            if (response.ok) {
                window.location.reload();
            } else {
                alert("Error: " + (data.error || data.detail || "Unknown error"));
            }
        } catch (e) {
            alert("Network error");
        }
      }
    </script>'''

# We need to replace the old script
import re
content = re.sub(r'<script>\s*async function triggerTrustScore.*?</script>', new_script, content, flags=re.DOTALL)

with open('api_gateway/templates/api_gateway/officer_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated officer_dashboard.html with CSRF token!")
