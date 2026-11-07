import re
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

html_path = os.path.join("templates", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find all buttons
buttons = re.findall(r'<button\b([^>]*)>(.*?)</button>', content, re.DOTALL | re.IGNORECASE)
print(f"Total buttons found: {len(buttons)}\n")

button_list = []
for i, (attrs, inner) in enumerate(buttons, 1):
    id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
    onclick_m = re.search(r'onclick=["\']([^"\']+)["\']', attrs)
    datatab_m = re.search(r'data-tab=["\']([^"\']+)["\']', attrs)
    datasubtab_m = re.search(r'data-subtab=["\']([^"\']+)["\']', attrs)
    class_m = re.search(r'class=["\']([^"\']+)["\']', attrs)
    clean_text = re.sub(r'<[^>]+>', ' ', inner).strip()
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    bid = id_m.group(1) if id_m else ""
    bonclick = onclick_m.group(1) if onclick_m else ""
    bdatatab = datatab_m.group(1) if datatab_m else ""
    bdatasubtab = datasubtab_m.group(1) if datasubtab_m else ""
    bclass = class_m.group(1) if class_m else ""
    
    item = {
        "index": i,
        "id": bid,
        "onclick": bonclick,
        "datatab": bdatatab,
        "datasubtab": bdatasubtab,
        "class": bclass,
        "text": clean_text[:40]
    }
    button_list.append(item)
    print(f"{i:02d}. ID=[{bid:20s}] | OnClick=[{bonclick:28s}] | DataTab=[{bdatatab:12s}] | Text=[{clean_text[:30]}]")

# Check all JS files for functions and listeners
js_files = ["app.js", "audio.js", "particles.js", "gauge.js", "charts.js", "device_3d.js"]
js_content = ""
for jf in js_files:
    jpath = os.path.join("static", "js", jf)
    if os.path.exists(jpath):
        with open(jpath, "r", encoding="utf-8") as f:
            js_content += f"\n/* --- {jf} --- */\n" + f.read()

print(f"\nTotal JS bundle length analyzed: {len(js_content)} chars")

# Check each button's handler
print("\n--- BUTTON HANDLER VERIFICATION ---")
missing_handlers = []
for b in button_list:
    target = b['id'] or b['onclick'] or b['datatab']
    has_handler = False
    
    # 1. Has onclick attribute
    if b['onclick']:
        func_name = re.match(r'([a-zA-Z0-9_]+)\(', b['onclick'])
        if func_name:
            fn = func_name.group(1)
            if re.search(rf'\bfunction\s+{fn}\b|\bwindow\.{fn}\b|\bconst\s+{fn}\s*=\b|\blet\s+{fn}\s*=', js_content):
                has_handler = True
                handler_info = f"Calls JS function '{fn}()'"
            else:
                handler_info = f"MISSING JS FUNCTION '{fn}()'!"
                missing_handlers.append((b, handler_info))
        else:
            has_handler = True
            handler_info = f"Inline JS: {b['onclick']}"
            
    # 2. Has data-tab (tab switcher)
    elif b['datatab']:
        if "data-tab" in js_content or "navTabBtns" in js_content or "switchTab" in js_content:
            has_handler = True
            handler_info = f"Handled by Tab Switcher Listener (tab='{b['datatab']}')"
        else:
            handler_info = "MISSING TAB SWITCHER LISTENER!"
            missing_handlers.append((b, handler_info))
            
    # 2b. Has data-subtab (subtab switcher)
    elif b['datasubtab']:
        if "data-subtab" in js_content or "subBtns" in js_content or "initSubtabs" in js_content:
            has_handler = True
            handler_info = f"Handled by Subtab Switcher Listener (subtab='{b['datasubtab']}')"
        else:
            handler_info = "MISSING SUBTAB SWITCHER LISTENER!"
            missing_handlers.append((b, handler_info))
            
    # 3. Has ID with addEventListener or getElementById
    elif b['id']:
        if f"'{b['id']}'" in js_content or f'"{b["id"]}"' in js_content:
            has_handler = True
            handler_info = f"Bound via JS ID '{b['id']}'"
        else:
            handler_info = f"ID '{b['id']}' NOT REFERENCED IN JS!"
            missing_handlers.append((b, handler_info))
    else:
        handler_info = "No ID, OnClick, or DataTab found!"
        missing_handlers.append((b, handler_info))
        
    print(f"Btn #{b['index']:02d} [{b['text'][:22]}]: {'[OK]' if has_handler else '[FAIL]'} -> {handler_info}")

if missing_handlers:
    print(f"\nWARNING: {len(missing_handlers)} buttons need attention!")
else:
    print("\nALL BUTTONS HAVE VERIFIED WORKING HANDLERS!")
