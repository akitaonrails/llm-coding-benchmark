#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const args = parseArgs(process.argv.slice(2));
if (!args.url || !args.outDir) {
  console.error("usage: browser_probe.mjs --url URL --out-dir DIR [--message TEXT] [--timeout-seconds N]");
  process.exit(2);
}

const timeoutMs = Number(args.timeoutSeconds || 90) * 1000;
const message = args.message || "hello world";
const outDir = path.resolve(args.outDir);
fs.mkdirSync(outDir, { recursive: true });

const homePath = path.join(outDir, "home.png");
const chatPath = path.join(outDir, "chat.png");
const jsonPath = path.join(outDir, "browser_probe.json");
const logPath = path.join(outDir, "browser_probe.log");

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "llm-benchmark-browser-"));
const logStream = fs.createWriteStream(logPath, { flags: "w" });

const chrome = spawn("chromium", [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  "--disable-dev-shm-usage",
  "--window-size=1440,1600",
  "--user-data-dir=" + tempDir,
  "--remote-debugging-port=0",
  "about:blank",
], {
  stdio: ["ignore", "pipe", "pipe"],
});

let browserKilled = false;

function cleanup() {
  if (!browserKilled) {
    browserKilled = true;
    chrome.kill("SIGTERM");
  }
  logStream.end();
}

function writeLog(prefix, chunk) {
  const text = chunk.toString();
  logStream.write(`[${prefix}] ${text}`);
}

chrome.stdout.on("data", (chunk) => writeLog("stdout", chunk));
chrome.stderr.on("data", (chunk) => writeLog("stderr", chunk));

process.on("exit", cleanup);
process.on("SIGINT", () => {
  cleanup();
  process.exit(130);
});

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith("--")) continue;
    const value = argv[i + 1];
    const normalized = key.slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    out[normalized] = value;
    i += 1;
  }
  return out;
}

function waitForDebuggerUrl() {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timed out waiting for Chromium debugger URL")), 15000);
    const matcher = /DevTools listening on (ws:\/\/[^\s]+)/;

    function onData(chunk) {
      const text = chunk.toString();
      const match = text.match(matcher);
      if (match) {
        clearTimeout(timer);
        chrome.stderr.off("data", onData);
        resolve(match[1]);
      }
    }

    chrome.stderr.on("data", onData);
    chrome.on("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`Chromium exited before debugger became available (code=${code})`));
    });
  });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function fetchJson(url, options = {}) {
  return fetch(url, options).then(async (response) => {
    if (!response.ok) {
      const body = await response.text();
      throw new Error(`HTTP ${response.status} from ${url}: ${body.slice(0, 500)}`);
    }
    return response.json();
  });
}

class CDPClient {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    this.events = [];
    ws.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      if (typeof data.id === "number") {
        const pending = this.pending.get(data.id);
        if (!pending) return;
        this.pending.delete(data.id);
        if (data.error) {
          pending.reject(new Error(JSON.stringify(data.error)));
        } else {
          pending.resolve(data.result || {});
        }
        return;
      }
      this.events.push(data);
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  async waitForEvent(method, timeout = 15000) {
    const started = Date.now();
    for (;;) {
      const index = this.events.findIndex((event) => event.method === method);
      if (index >= 0) {
        const [event] = this.events.splice(index, 1);
        return event.params || {};
      }
      if (Date.now() - started > timeout) {
        throw new Error(`timed out waiting for event ${method}`);
      }
      await delay(100);
    }
  }
}

async function captureScreenshot(client, filePath) {
  const result = await client.send("Page.captureScreenshot", { format: "png", fromSurface: true });
  fs.writeFileSync(filePath, Buffer.from(result.data, "base64"));
}

async function evalJson(client, expression) {
  const result = await client.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
  return result.result?.value;
}

async function bodyText(client) {
  const value = await evalJson(
    client,
    `(() => ({ text: document.body ? document.body.innerText : "", htmlLength: document.body ? document.body.innerHTML.length : 0 }))()`,
  );
  return value || { text: "", htmlLength: 0 };
}

async function main() {
  const debuggerWs = await waitForDebuggerUrl();
  const portMatch = debuggerWs.match(/ws:\/\/127\.0\.0\.1:(\d+)\//);
  if (!portMatch) {
    throw new Error(`unable to parse debugger port from ${debuggerWs}`);
  }
  const port = portMatch[1];
  const target = await fetchJson(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(args.url)}`, { method: "PUT" }).catch(
    async () => fetchJson(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(args.url)}`),
  );
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timed out opening page websocket")), 10000);
    ws.addEventListener("open", () => {
      clearTimeout(timer);
      resolve();
    });
    ws.addEventListener("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
  });
  const client = new CDPClient(ws);
  await client.send("Page.enable");
  await client.send("Runtime.enable");
  await client.send("DOM.enable");
  await client.send("Network.enable");
  await client.send("Page.bringToFront");
  await client.waitForEvent("Page.loadEventFired", 30000).catch(() => ({}));
  await delay(1500);

  const before = await bodyText(client);
  await captureScreenshot(client, homePath);

  const escapedMessage = JSON.stringify(message);
  const sendResult = await evalJson(
    client,
    `(() => {
      const probe = ${escapedMessage};
      const input = document.querySelector('textarea, input[type="text"], input:not([type]), [contenteditable="true"]');
      if (!input) return { ok: false, error: 'no input field found' };
      const dispatch = (el, type) => el.dispatchEvent(new Event(type, { bubbles: true }));
      if (input.isContentEditable) {
        input.focus();
        input.textContent = probe;
        dispatch(input, 'input');
      } else {
        input.focus();
        input.value = probe;
        dispatch(input, 'input');
        dispatch(input, 'change');
      }
      const submit =
        (input.form && input.form.querySelector('button[type="submit"], input[type="submit"], button:not([disabled])')) ||
        document.querySelector('button[type="submit"], input[type="submit"], form button:not([disabled])');
      if (submit) {
        submit.click();
        return { ok: true, action: 'click', element: submit.tagName };
      }
      if (input.form) {
        input.form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        return { ok: true, action: 'submit-event' };
      }
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
      input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
      return { ok: true, action: 'enter-key' };
    })()`,
  );

  let responseObserved = false;
  let responseSummary = null;
  let errorText = null;
  let afterSubmit = await bodyText(client);
  const sendSnapshot = afterSubmit;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    await delay(2000);
    const current = await bodyText(client);
    const lower = (current.text || "").toLowerCase();
    if (!errorText && (lower.includes("error") || lower.includes("exception") || lower.includes("something went wrong"))) {
      errorText = current.text.slice(0, 5000);
    }
    if (
      current.htmlLength > sendSnapshot.htmlLength + 40 ||
      current.text.length > sendSnapshot.text.length + 40
    ) {
      responseObserved = true;
      responseSummary = {
        deltaText: current.text.length - sendSnapshot.text.length,
        deltaHtml: current.htmlLength - sendSnapshot.htmlLength,
      };
      afterSubmit = current;
      break;
    }
    afterSubmit = current;
  }

  await captureScreenshot(client, chatPath);

  const result = {
    ok: true,
    url: args.url,
    message,
    sendResult,
    responseObserved,
    responseSummary,
    errorText,
    beforeTextLength: before.text.length,
    afterTextLength: afterSubmit.text.length,
    homeScreenshot: path.basename(homePath),
    chatScreenshot: path.basename(chatPath),
  };
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
  ws.close();
  cleanup();
}

main().catch((error) => {
  const result = {
    ok: false,
    url: args.url,
    message,
    error: error && error.stack ? error.stack : String(error),
    homeScreenshot: fs.existsSync(homePath) ? path.basename(homePath) : null,
    chatScreenshot: fs.existsSync(chatPath) ? path.basename(chatPath) : null,
  };
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
  cleanup();
  process.exit(1);
});
