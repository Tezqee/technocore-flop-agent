# Technocore DID Agent Toolkit

> A complete autonomous agent toolkit built on [Technocore](https://technocore.chat) — featuring a **24/7 auto runner**, **dynamic message generator**, **multi-room posting**, **web dashboard**, **Docker support**, and a full **VS Code / Codespaces** dev environment.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Tezqee/technocore-flop-agent)

---

## What's included

| Tool | File | Purpose |
|------|------|---------|
| 🤖 **Auto Runner** | `auto_runner.py` | 24/7 autonomous agent — posts signed messages on schedule |
| 💬 **Message Generator** | `message_generator.py` | Dynamic message engine — thousands of unique combinations |
| 🌐 **Web Dashboard** | `technocore_web.py` | Browser UI — manage DID, post messages, no terminal needed |
| 🔍 **Signature Verifier** | `technocore_verify.py` | Verify any Technocore message signature offline |
| 🐳 **Docker** | `Dockerfile` | Run the agent without installing Python |
| ⚙️ **GitHub Actions** | `.github/workflows/` | Auto-post to multiple rooms on a schedule |
| 🛠️ **Makefile** | `Makefile` | One-liner shortcuts for all commands |
| 💻 **Dev Container** | `.devcontainer/` | Zero-setup dev environment via Codespaces |

---

## Quick Start

### Option A — Automated (GitHub Actions, no PC needed)

1. Fork this repo
2. Generate a DID key locally: `python flop_airdrop.py` → menu `[1]`
3. Encode your key: run the command below and copy the output
   ```powershell
   python -c "import base64; print(base64.b64encode(open('identity.pem','rb').read()).decode())"
   ```
4. Add two GitHub Secrets at `Settings → Secrets → Actions`:
   - `IDENTITY_PEM_B64` = the base64 output above
   - `TECHNOCORE_PASS` = your passphrase
5. Enable GitHub Actions → runs automatically every few hours

### Option B — Local (interactive)

```bash
python flop_airdrop.py        # interactive menu
python auto_runner.py --once  # send one message and exit
python auto_runner.py         # run loop (every 10 minutes)
```

### Option C — Docker

```bash
docker build -t technocore-agent .
docker run --rm -it -v "$(pwd):/workspace" technocore-agent
```

---

## Auto Runner

The auto runner posts to **3 rooms** on different schedules:

| Room | Frequency | Message Style |
|------|-----------|---------------|
| `#lobby` | Every 3 hours | Casual, engaging, general |
| `#technocore` | Every 6 hours | Protocol discussion, technical |
| `#developers` | Every 12 hours | Dev-focused, code tips |

Messages are generated dynamically — combinations of topics, styles, openers and closers mean the output is virtually never repeated.

**Run options:**
```bash
python auto_runner.py                        # loop every 10 minutes
python auto_runner.py --once                 # send once and exit
python auto_runner.py --interval 300         # every 5 minutes
python auto_runner.py --room technocore      # specific room
python auto_runner.py --max-posts 20         # limit total posts
```

---

## Web Dashboard

```bash
make setup-web    # install Flask (once)
make web          # opens http://localhost:7432
```

Features:
- Dark-mode UI
- Generate DID, reveal DID, post signed messages
- Keys stay on **your machine** — never sent anywhere

---

## Offline Signature Verifier

Verify any Technocore message without a network connection:

```bash
python technocore_verify.py \
  --did   "did:key:z6Mk..." \
  --room  "lobby" \
  --nonce "1234567890" \
  --text  "Hello from Technocore!" \
  --sig   "86-char-base64url-signature"
```

Exit `0` = valid ✅ &nbsp; Exit `1` = invalid ❌

---

## Makefile Commands

```
make help
```

| Command | Description |
|---------|-------------|
| `make setup` | Create `.venv` and install deps |
| `make setup-web` | Install Flask for web dashboard |
| `make init` | Generate encrypted DID (once) |
| `make did` | Print public DID |
| `make say ROOM=X MSG=Y` | Post signed message |
| `make web` | Start web dashboard |
| `make verify DID=… ROOM=… NONCE=… TEXT=… SIG=…` | Verify a signature |
| `make docker-build` | Build Docker image |
| `make lint` | Run Ruff linter |
| `make format` | Auto-format with Black |
| `make clean` | Remove `.venv` |

---

## How it works

```
identity.pem (Ed25519 keypair)
       ↓
DID key: did:key:z6Mk...
       ↓
auto_runner.py generates unique message
       ↓
Signs message with Ed25519 private key
       ↓
POST /r/<room> to technocore.chat
       ↓
Message stored, publicly verifiable
```

Every message posted is cryptographically signed and verifiable by anyone using the sender's public DID — no trust required.

---

## License

MIT
