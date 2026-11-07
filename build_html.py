import os
import re

BASE_DIR = r"C:\Users\User\.gemini\antigravity-ide\scratch\turmericguard-ai"
CSS_FILE = os.path.join(BASE_DIR, "static", "css", "main.css")
TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "index.html")
ROOT_INDEX = os.path.join(BASE_DIR, "index.html")

with open(CSS_FILE, "r", encoding="utf-8") as f:
    css_content = f.read()

with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Replace nav tab SVGs that lack width/height
html = html.replace(
    '<button class="nav-tab-btn active" data-tab="screening">\n      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">',
    '<button class="nav-tab-btn active" data-tab="screening">\n      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
)
html = html.replace(
    '<button class="nav-tab-btn" data-tab="ledger">\n      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">',
    '<button class="nav-tab-btn" data-tab="ledger">\n      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
)
html = html.replace(
    '<button class="nav-tab-btn" data-tab="fleet">\n      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">',
    '<button class="nav-tab-btn" data-tab="fleet">\n      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
)
html = html.replace(
    '<button class="nav-tab-btn" data-tab="compliance">\n      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">',
    '<button class="nav-tab-btn" data-tab="compliance">\n      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
)
html = html.replace(
    '<button class="nav-tab-btn" data-tab="api">\n      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">',
    '<button class="nav-tab-btn" data-tab="api">\n      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
)
html = html.replace(
    '<div class="brand-logo-icon">\n        <svg viewBox="0 0 24 24">',
    '<div class="brand-logo-icon">\n        <svg width="22" height="22" viewBox="0 0 24 24">'
)

# 2. Add local file preview notice banner right after <body>
file_notice_banner = """
  <!-- Protocol Detection Notice (Local File vs Live Server) -->
  <div id="fileModeNotice" style="display:none; background: linear-gradient(90deg, #131a29, #1e293b); border-bottom: 1px solid #e8a33d; padding: 10px 20px; font-size: 0.82rem; color: #f1f5f9; text-align: center; z-index: 9999;">
    <span style="color:#e8a33d; font-weight:700;">🌐 Local File Preview:</span>
    CSS and UI components are fully embedded. For live hardware camera streaming and real-time backend API, open:
    <a href="http://127.0.0.1:5000" target="_blank" style="color: #38bdf8; font-weight: 700; text-decoration: underline; margin-left: 8px;">
      http://127.0.0.1:5000 (Click to Launch Live Server)
    </a>
  </div>
"""

if '<div id="fileModeNotice"' not in html:
    html = html.replace('<body>', '<body>' + file_notice_banner)

# 3. Add image onerror fallback
html = html.replace(
    '<img id="samplePreviewImg" class="sample-preview-img" src="/static/samples/pure_alleppey.jpg" alt="Turmeric Sample In Chamber">',
    '<img id="samplePreviewImg" class="sample-preview-img" src="/static/samples/pure_alleppey.jpg" alt="Turmeric Sample In Chamber" onerror="this.onerror=null; if(window.location.protocol===\'file:\'){this.src=\'../static/samples/pure_alleppey.jpg\';}">'
)

# 4. Inline the full CSS into <style id="inlinedMainCss">
style_block = f"""
  <!-- Inlined Consolidated Production CSS (Guarantees 100% styling on both http:// and file://) -->
  <style id="inlinedMainCss">
{css_content}
  </style>
"""

# Replace existing css links with inlined CSS + fallback links
target_css_regex = r'<link rel="stylesheet" href="/static/css/tokens\.css">[\s\S]*?<link rel="stylesheet" href="/static/css/main\.css">'
html = re.sub(target_css_regex, style_block.strip(), html)

# Also ensure relative link fallback exists
html = html.replace(
    '</style>',
    '</style>\n  <link rel="stylesheet" href="../static/css/main.css" onerror="this.onerror=null;">\n  <link rel="stylesheet" href="static/css/main.css" onerror="this.onerror=null;">'
)

# 5. Make script loading resilient with dynamic loader
script_loader = """
  <!-- Application Scripts with Multi-Path Fallback -->
  <script>
    (function() {
      const isFile = window.location.protocol === 'file:';
      const inTemplates = window.location.pathname.includes('/templates/') || window.location.pathname.includes('\\\\templates\\\\');
      const prefix = isFile ? (inTemplates ? '../static/js/' : 'static/js/') : '/static/js/';
      
      const scripts = ['gauge.js', 'charts.js', 'device_3d.js', 'app.js'];
      
      function loadNext(index) {
        if (index >= scripts.length) return;
        const s = document.createElement('script');
        s.src = prefix + scripts[index];
        s.onload = () => loadNext(index + 1);
        s.onerror = () => {
          // Fallback to absolute /static/js/ if relative fails
          const fb = document.createElement('script');
          fb.src = '/static/js/' + scripts[index];
          fb.onload = () => loadNext(index + 1);
          document.body.appendChild(fb);
        };
        document.body.appendChild(s);
      }
      loadNext(0);
    })();
  </script>
"""

target_scripts_regex = r'<!-- Application Scripts -->[\s\S]*?<script src="/static/js/app\.js"></script>'
html_with_loader = re.sub(target_scripts_regex, script_loader.strip(), html)

# Save templates/index.html
with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
    f.write(html_with_loader)
print(f"Successfully updated {TEMPLATE_FILE} with inlined CSS ({len(css_content)} bytes) and resilient scripts.")

# Also generate root index.html (for users who click index.html at root of project folder)
root_html = html_with_loader.replace('src="../static/samples/', 'src="static/samples/')
with open(ROOT_INDEX, "w", encoding="utf-8") as f:
    f.write(root_html)
print(f"Successfully created root {ROOT_INDEX}")

# In addition, inline CSS into public_verify.html
VERIFY_FILE = os.path.join(BASE_DIR, "templates", "public_verify.html")
with open(VERIFY_FILE, "r", encoding="utf-8") as f:
    verify_html = f.read()

verify_html = re.sub(
    r'<link rel="stylesheet" href="/static/css/tokens\.css">\s*<link rel="stylesheet" href="/static/css/main\.css">',
    f'<style id="inlinedMainCss">\n{css_content}\n  </style>',
    verify_html
)
with open(VERIFY_FILE, "w", encoding="utf-8") as f:
    f.write(verify_html)
print(f"Successfully inlined CSS into {VERIFY_FILE}")

