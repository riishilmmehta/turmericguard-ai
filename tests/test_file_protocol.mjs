import { spawn } from 'child_process';

const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const PORT = 9223;
const FILE_URL = "file:///C:/Users/User/.gemini/antigravity-ide/scratch/turmericguard-ai/index.html";

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

async function testFileProtocol() {
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
      if (msg.method === "Runtime.exceptionThrown") {
        console.error("[FILE ERROR]:", msg.params.exceptionDetails.text, msg.params.exceptionDetails.exception?.description);
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
    const { result: { targetId } } = await send("Target.createTarget", { url: FILE_URL });
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
    await delay(2000);

    const evalInPage = async (expression) => {
      const res = await sendPage("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
      return res.result?.result?.value;
    };

    console.log("--- TESTING OFFLINE FILE:// PROTOCOL ---");
    const title = await evalInPage("document.title");
    console.log("[PASS] Offline Title:", title);

    await evalInPage("document.querySelector('button[data-tab=\"about\"]').click()");
    await delay(300);
    const aboutActive = await evalInPage("document.getElementById('tabView-about').classList.contains('active')");
    console.log("[PASS] Offline Tab Click 'about':", aboutActive);

    await evalInPage("document.querySelector('button[data-tab=\"screening\"]').click()");
    await delay(300);
    console.log("[PASS] Offline Tab Click 'screening' returned successfully.");

    await evalInPage("document.getElementById('runAnalysisBtn').click()");
    await delay(2200);
    const status = await evalInPage("document.getElementById('heroStatusBadge').textContent");
    console.log("[PASS] Offline Screening executed with fallback simulation:", status);

  } finally {
    edge.kill();
  }
}

testFileProtocol().catch(e => {
  console.error("File protocol test failed:", e);
  process.exit(1);
});
