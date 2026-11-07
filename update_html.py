"""Updates templates/index.html to add the Android APK download button and showcase card."""
import os

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Action Toolbar APK Button
target_btn = '<button class="btn btn-secondary sound-toggle-btn active" id="soundToggleBtn"'
replacement_btn = """<a href="/download/app.apk" class="btn btn-secondary" id="btnDownloadApk" title="Download Pure Android APK (Offline Mobile Scanner v2.0)" style="background:rgba(245, 196, 0, 0.12); border:1px solid #F5C400; color:#F5C400; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
          <span>Download Android APK</span>
        </a>
        <button class="btn btn-secondary sound-toggle-btn active" id="soundToggleBtn" """

if target_btn in text:
    text = text.replace(target_btn, replacement_btn, 1)
    print("Action toolbar APK button injected.")
else:
    print("Target toolbar button not found!")

# 2. Add an Android APK Showcase banner right inside the Quick Tour Bar
target_guide = '<!-- Guided Quick-Start Tour Bar -->'
replacement_guide = """<!-- Guided Quick-Start Tour Bar -->
      <div style="background: linear-gradient(135deg, rgba(245, 196, 0, 0.08), rgba(15, 23, 42, 0.6)); border: 1px solid rgba(245, 196, 0, 0.35); border-radius: 12px; padding: 12px 18px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 36px; height: 36px; border-radius: 18px; background: #000000; display: flex; align-items: center; justify-content: center; font-size: 18px;">
            📱
          </div>
          <div>
            <div style="font-size: 0.88rem; font-weight: 800; color: #FFFFFF;">
              Pure Mobile App (Android APK v2.0 Available)
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8;">
              Standalone offline screening with 8-bit quantized NPU matrix (2.8ms kernel latency) & tactile micro-interactions.
            </div>
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <a href="/download/app.apk" class="btn btn-primary" style="background: #F5C400; color: #000000; font-weight: 800; text-decoration: none; padding: 6px 14px; font-size: 0.78rem;" download="Pure-TurmericGuard-v2.0.apk">
            ⬇ Direct APK Download (0.88 MB)
          </a>
        </div>
      </div>"""

if target_guide in text:
    text = text.replace(target_guide, replacement_guide, 1)
    print("Quick tour APK banner injected.")
else:
    print("Target quick guide not found!")

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("templates/index.html updated successfully.")

