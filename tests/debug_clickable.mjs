import { spawn } from 'child_process';

const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const PORT = 9224;

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function getWsUrl() {
  for (let i = 0; i < 20; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (res.ok) {
        const json = await res.json();
        return json.webSocketDebuggerUrl;
      }
    } catch (e) {
      await delay(300);
    }
  }
  throw new Error("Could not connect to Edge DevTools port");
}

async function debugClicks() {
  const edge = spawn(EDGE_PATH, [
    `--remote-debugging-port=${PORT}`,
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    'about:blank'
  ]);

  try {
    const wsUrl = await getWsUrl();
    const ws = new WebSocket(wsUrl);
    let msgId = 1;
    const callbacks = new Map();

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && callbacks.has(msg.id)) {
        callbacks.get(msg.id)(msg);
        callbacks.delete(msg.id);
      }
      if (msg.method === "Runtime.consoleAPICalled") {
        console.log(`[BROWSER CONSOLE ${msg.params.type.toUpperCase()}]:`, msg.params.args.map(a => a.value || a.description).join(' '));
      }
      if (msg.method === "Runtime.exceptionThrown") {
        console.error(`[BROWSER EXCEPTION]:`, msg.params.exceptionDetails.text, msg.params.exceptionDetails.exception?.description);
      }
    };

    const send = (method, params = {}) => {
      const id = msgId++;
      return new Promise((resolve) => {
        callbacks.set(id, resolve);
        ws.send(JSON.stringify({ id, method, params }));
      });
    };

    await new Promise(r => ws.onopen = r);
    const { result: { targetId } } = await send("Target.createTarget", { url: "http://127.0.0.1:5000" });
    const { result: { sessionId } } = await send("Target.attachToTarget", { targetId, flatten: true });

    const sendPage = (method, params = {}) => {
      const id = msgId++;
      return new Promise((resolve) => {
        callbacks.set(id, resolve);
        ws.send(JSON.stringify({ id, sessionId, method, params }));
      });
    };

    await sendPage("Runtime.enable");
    await sendPage("Page.enable");
    await delay(1500);

    const evalInPage = async (expression) => {
      const res = await sendPage("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
      if (res.result?.exceptionDetails) {
        console.error("Eval Exception:", res.result.exceptionDetails);
      }
      return res.result?.result?.value;
    };

    console.log("=== INSPECTING HIT-TEST (ELEMENT FROM POINT) ===");
    // Test points where buttons are
    const hitPoints = [
      { name: "Top-left Brand", x: 100, y: 30 },
      { name: "Sound Toggle Button", x: 750, y: 30 },
      { name: "Navigation Tab 1 (Screening)", x: 100, y: 80 },
      { name: "Navigation Tab 2 (Ledger)", x: 250, y: 80 },
      { name: "Preset Chip 1", x: 100, y: 360 },
      { name: "Screening Button", x: 120, y: 480 },
    ];

    for (const pt of hitPoints) {
      const info = await evalInPage(`
        (() => {
          const el = document.elementFromPoint(${pt.x}, ${pt.y});
          if (!el) return 'NULL';
          return {
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: (el.textContent || '').trim().substring(0, 30),
            pointerEvents: window.getComputedStyle(el).pointerEvents,
            zIndex: window.getComputedStyle(el).zIndex
          };
        })()
      `);
      console.log(`Point (${pt.x}, ${pt.y}) [${pt.name}]:`, JSON.stringify(info));
    }

    console.log("\n=== INSPECTING MODALS STATE ===");
    const modalsState = await evalInPage(`
      Array.from(document.querySelectorAll('.modal-backdrop')).map(m => ({
        id: m.id,
        display: window.getComputedStyle(m).display,
        visibility: window.getComputedStyle(m).visibility,
        opacity: window.getComputedStyle(m).opacity,
        zIndex: window.getComputedStyle(m).zIndex,
        classes: m.className
      }))
    `);
    console.log("Modals:", JSON.stringify(modalsState, null, 2));

    console.log("\n=== TESTING DISPATCHING PHYSICAL MOUSE CLICK EVENTS ===");
    // Dispatch real mouse events (mousedown, mouseup, click) on Screening Button
    const clickResult = await evalInPage(`
      (() => {
        const btn = document.getElementById('runAnalysisBtn');
        if (!btn) return 'NO BUTTON';
        const rect = btn.getBoundingClientRect();
        
        // Check if disabled or styled pointer-events none
        const style = window.getComputedStyle(btn);
        
        let clicked = false;
        btn.addEventListener('click', () => { clicked = true; }, { once: true });
        
        btn.click();
        return {
          id: btn.id,
          disabled: btn.disabled,
          pointerEvents: style.pointerEvents,
          rect: { top: rect.top, left: rect.left, width: rect.width, height: rect.height },
          clickedTriggered: clicked
        };
      })()
    `);
    console.log("Run Analysis Button Click Test:", JSON.stringify(clickResult, null, 2));

    console.log("\n=== TESTING DISPATCHING CLICK ON TAB 'ledger' ===");
    const tabClickResult = await evalInPage(`
      (() => {
        const tabBtn = document.querySelector('button[data-tab=\"ledger\"]');
        if (!tabBtn) return 'NO TAB';
        let tabFired = false;
        tabBtn.addEventListener('click', () => { tabFired = true; }, { once: true });
        tabBtn.click();
        const ledgerActive = document.getElementById('tabView-ledger')?.classList.contains('active');
        return { tabFired, ledgerActive };
      })()
    `);
    console.log("Tab Click Result:", JSON.stringify(tabClickResult, null, 2));

  } finally {
    edge.kill();
  }
}

debugClicks().catch(e => {
  console.error(e);
  process.exit(1);
});
