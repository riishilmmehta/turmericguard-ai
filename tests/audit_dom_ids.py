import re
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open(os.path.join("templates", "index.html"), "r", encoding="utf-8") as f:
    html_content = f.read()

# Extract all IDs defined in HTML
html_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', html_content))
print(f"Total unique IDs defined in HTML: {len(html_ids)}")

# Extract all IDs looked up in JS via getElementById, querySelector('#...'), etc.
js_ids = set()
js_files = ["app.js", "audio.js", "particles.js", "gauge.js", "charts.js", "device_3d.js"]
for jf in js_files:
    jpath = os.path.join("static", "js", jf)
    if os.path.exists(jpath):
        with open(jpath, "r", encoding="utf-8") as f:
            jtext = f.read()
        
        # getElementById('...')
        matches = re.findall(r'getElementById\(["\']([^"\']+)["\']\)', jtext)
        js_ids.update(matches)
        
        # querySelector('#...')
        qs_matches = re.findall(r'querySelector\(["\']#([^"\'\s,>+]+)["\']\)', jtext)
        js_ids.update(qs_matches)

print(f"Total unique IDs referenced in JS: {len(js_ids)}")

missing_ids = []
for jid in sorted(js_ids):
    if jid not in html_ids:
        missing_ids.append(jid)
        print(f"MISSING ID in HTML: '{jid}'")
    else:
        print(f"OK: ID '{jid}' exists in HTML")

print(f"\nMissing IDs count: {len(missing_ids)}")
if not missing_ids:
    print("PERFECT: 100% of IDs referenced in JavaScript exist in the HTML template!")
