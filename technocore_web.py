#!/usr/bin/env python3
"""
technocore_web.py – Local web dashboard for the Technocore DID agent.

Run:
    python technocore_web.py

Then open http://localhost:7432 in your browser.

Dependencies (beyond the base requirements.txt):
    pip install flask
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

# ── Lazy Flask import with friendly error ─────────────────────────────────────
try:
    from flask import Flask, jsonify, render_template_string, request
except ImportError:
    sys.exit(
        "Flask is not installed.\n"
        "Run: pip install flask\n"
        "Then restart this script."
    )

PORT = int(os.environ.get("TECHNOCORE_PORT", 7432))
AGENT = Path(__file__).parent / "technocore_agent.py"
KEY_PATH = Path(__file__).parent / "identity.pem"

app = Flask(__name__)
_lock = threading.Lock()  # serialise concurrent CLI calls


# ── Helper: call the agent CLI ────────────────────────────────────────────────

def run_agent(*args: str, passphrase: str = "") -> dict[str, Any]:
    """Run technocore_agent.py with the given arguments and return a result dict."""
    cmd = [sys.executable, str(AGENT), *args]
    env = os.environ.copy()

    try:
        with _lock:
            result = subprocess.run(
                cmd,
                input=passphrase + "\n" if passphrase else None,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        ok = result.returncode == 0

        # Try to parse JSON output from the agent
        data: Any = None
        if stdout:
            try:
                data = json.loads(stdout)
            except json.JSONDecodeError:
                data = stdout

        return {"ok": ok, "data": data, "error": stderr if not ok else None}
    except subprocess.TimeoutExpired:
        return {"ok": False, "data": None, "error": "Agent timed out after 30 s"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "data": None, "error": str(exc)}


# ── HTML UI (single-file, no templates directory needed) ──────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Technocore DID Dashboard</title>
<style>
  :root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --accent: #58a6ff; --accent2: #3fb950; --warn: #f78166;
    --text: #e6edf3; --muted: #8b949e;
    --radius: 8px; --font: "Segoe UI", system-ui, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font);
         min-height: 100vh; padding: 24px; }
  h1 { font-size: 1.6rem; font-weight: 700; color: var(--accent);
       margin-bottom: 4px; }
  .subtitle { color: var(--muted); font-size: 0.9rem; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px,1fr));
           gap: 16px; }
  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: var(--radius); padding: 20px; }
  .card h2 { font-size: 1rem; margin-bottom: 12px; display: flex; align-items:center;
              gap: 8px; }
  label { display: block; font-size: 0.82rem; color: var(--muted);
          margin-bottom: 4px; margin-top: 10px; }
  input, textarea, select {
    width: 100%; background: var(--bg); border: 1px solid var(--border);
    border-radius: 6px; color: var(--text); padding: 8px 10px;
    font-size: 0.9rem; font-family: inherit; resize: vertical; }
  input:focus, textarea:focus { outline: none; border-color: var(--accent); }
  button {
    margin-top: 14px; padding: 9px 18px; border: none; border-radius: 6px;
    background: var(--accent); color: #000; font-weight: 600; cursor: pointer;
    font-size: 0.9rem; width: 100%; transition: opacity 0.15s; }
  button:hover { opacity: 0.85; }
  button.danger { background: var(--warn); }
  button.success { background: var(--accent2); }
  .output {
    margin-top: 12px; background: var(--bg); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px; font-family: monospace; font-size: 0.8rem;
    white-space: pre-wrap; word-break: break-all; min-height: 48px;
    max-height: 260px; overflow-y: auto; color: var(--accent2); }
  .output.error { color: var(--warn); }
  .output.idle { color: var(--muted); }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 20px;
           font-size: 0.72rem; font-weight: 600; }
  .badge-green { background: #1f3d2b; color: var(--accent2); }
  .badge-red   { background: #3d1f1f; color: var(--warn); }
  .did-display { font-family: monospace; font-size: 0.78rem; word-break: break-all;
                 color: var(--accent); margin-top: 8px; }
  .spinner { display: none; margin-left: 8px; }
  .loading .spinner { display: inline; }
  footer { margin-top: 32px; color: var(--muted); font-size: 0.78rem; text-align:center; }
  a { color: var(--accent); }
</style>
</head>
<body>
<h1>⚡ Technocore DID Dashboard</h1>
<p class="subtitle">Local web UI for <a href="https://github.com/zunmax/technocore-did-starter" target="_blank">technocore-did-starter</a> — generate identity, sign messages, verify contributions.</p>

<div class="grid">

  <!-- ── Status Card ── -->
  <div class="card">
    <h2>🔍 Agent Status</h2>
    <button onclick="checkStatus()" class="success">Check Version &amp; Identity</button>
    <div id="status-out" class="output idle">Click to check…</div>
  </div>

  <!-- ── Init Card ── -->
  <div class="card">
    <h2>🪪 Create DID (init)</h2>
    <label>Passphrase (≥ 12 chars)</label>
    <input type="password" id="init-pass" placeholder="your-secure-passphrase-here"/>
    <label>Confirm Passphrase</label>
    <input type="password" id="init-pass2" placeholder="repeat passphrase"/>
    <button onclick="initDid()" class="danger">Generate Identity</button>
    <div id="init-out" class="output idle">⚠️ Only run once. This creates identity.pem.</div>
  </div>

  <!-- ── Show DID Card ── -->
  <div class="card">
    <h2>🔑 Show DID</h2>
    <label>Passphrase</label>
    <input type="password" id="did-pass" placeholder="identity.pem passphrase"/>
    <button onclick="showDid()">Reveal Public DID</button>
    <div id="did-out" class="output idle">DID will appear here…</div>
  </div>

  <!-- ── Say Card ── -->
  <div class="card" style="grid-column: span 2;">
    <h2>💬 Post Signed Message (say)</h2>
    <label>Room</label>
    <input type="text" id="say-room" value="lobby" placeholder="lobby | technocore | …"/>
    <label>Message</label>
    <textarea id="say-text" rows="3" placeholder="Hello from Technocore!"></textarea>
    <label>Passphrase</label>
    <input type="password" id="say-pass" placeholder="identity.pem passphrase"/>
    <button onclick="postMessage()">Sign &amp; Post</button>
    <div id="say-out" class="output idle">Response JSON will appear here…</div>
  </div>

</div>

<footer>
  Running locally on port {{ port }} &nbsp;|&nbsp;
  Keys never leave your machine &nbsp;|&nbsp;
  <a href="https://github.com/zunmax/technocore-did-starter" target="_blank">Source on GitHub</a>
</footer>

<script>
async function api(endpoint, body={}) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
  return res.json();
}

function setOut(id, data, isError=false) {
  const el = document.getElementById(id);
  el.className = "output" + (isError ? " error" : "");
  el.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

async function checkStatus() {
  setOut("status-out", "Checking…");
  const r = await api("/api/status");
  setOut("status-out", r.data || r.error, !r.ok);
}

async function initDid() {
  const p1 = document.getElementById("init-pass").value;
  const p2 = document.getElementById("init-pass2").value;
  if (!p1 || p1 !== p2) { setOut("init-out","Passphrases do not match.",true); return; }
  if (p1.length < 12)   { setOut("init-out","Passphrase must be ≥ 12 characters.",true); return; }
  setOut("init-out","Generating identity… (this may take a moment)");
  const r = await api("/api/init", {passphrase: p1});
  setOut("init-out", r.data || r.error, !r.ok);
}

async function showDid() {
  const p = document.getElementById("did-pass").value;
  if (!p) { setOut("did-out","Enter passphrase.",true); return; }
  setOut("did-out","Loading DID…");
  const r = await api("/api/did", {passphrase: p});
  setOut("did-out", r.data || r.error, !r.ok);
}

async function postMessage() {
  const room = document.getElementById("say-room").value.trim();
  const text = document.getElementById("say-text").value.trim();
  const p    = document.getElementById("say-pass").value;
  if (!room || !text || !p) {
    setOut("say-out","Fill in room, message, and passphrase.",true); return;
  }
  setOut("say-out","Signing and posting…");
  const r = await api("/api/say", {room, text, passphrase: p});
  setOut("say-out", r.data || r.error, !r.ok);
}
</script>
</body>
</html>
"""


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return render_template_string(HTML, port=PORT)


@app.post("/api/status")
def api_status():
    ver = run_agent("--version")
    return jsonify(ver)


@app.post("/api/init")
def api_init():
    body = request.get_json(force=True, silent=True) or {}
    passphrase: str = body.get("passphrase", "")
    if not passphrase or len(passphrase) < 12:
        return jsonify({"ok": False, "data": None,
                        "error": "Passphrase must be at least 12 characters."})
    # Pass passphrase via stdin (agent reads it with getpass on --passphrase-stdin)
    result = run_agent("init", passphrase=passphrase)
    return jsonify(result)


@app.post("/api/did")
def api_did():
    body = request.get_json(force=True, silent=True) or {}
    passphrase: str = body.get("passphrase", "")
    result = run_agent("did", passphrase=passphrase)
    return jsonify(result)


@app.post("/api/say")
def api_say():
    body = request.get_json(force=True, silent=True) or {}
    room: str = body.get("room", "")
    text: str = body.get("text", "")
    passphrase: str = body.get("passphrase", "")
    if not room or not text:
        return jsonify({"ok": False, "data": None,
                        "error": "room and text are required."})
    result = run_agent("say", room, text, passphrase=passphrase)
    return jsonify(result)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import webbrowser

    url = f"http://localhost:{PORT}"
    print(f"\n  Technocore DID Dashboard")
    print(f"  >>  {url}")
    print(f"\n  Press CTRL+C to stop.\n")

    # Open browser after a short delay so Flask is ready
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host="127.0.0.1", port=PORT, debug=False)
