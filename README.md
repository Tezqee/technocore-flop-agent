# Technocore DID Developer Toolkit 🚀

> A complete developer toolkit around [technocore-did-starter](https://github.com/zunmax/technocore-did-starter) — adds a **web dashboard**, **Docker support**, **GitHub Actions automation**, **offline signature verifier**, and a full **VS Code / Codespaces** dev environment.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ✨ What's included

| Tool | File | Purpose |
|------|------|---------|
| 🌐 **Web Dashboard** | `technocore_web.py` | Browser UI — init DID, post messages, no Terminal needed |
| 🔍 **Signature Verifier** | `technocore_verify.py` | Verify any Technocore message signature offline |
| 🐳 **Docker** | `Dockerfile` | Run the agent without installing Python |
| ⚙️ **GitHub Action** | `.github/workflows/technocore-announce.yml` | Auto-post signed message on every push |
| 🛠️ **Makefile** | `Makefile` | One-liner shortcuts for all commands |
| 💻 **VS Code / Codespaces** | `.devcontainer/` | Zero-setup dev environment |
| 🔌 **VS Code settings** | `.vscode/` | Auto-formatter, linter, recommended extensions |
| 🌐 **REST Client** | `technocore.http` | Test API endpoints from VS Code |

---

## 🚀 Quick Start

### Option A — Codespaces (zero install)
Click **"Open in GitHub Codespaces"** above. Everything is pre-installed.

### Option B — Docker (no Python needed)
```bash
# Build once
docker build -t technocore-did .

# Generate your DID
docker run --rm -it -v "$(pwd):/workspace" technocore-did init

# Post a message
docker run --rm -it -v "$(pwd):/workspace" technocore-did say lobby "Hello!"
```

### Option C — Local Python (Makefile)
```bash
make setup        # create .venv and install deps
make init         # generate your encrypted DID (run once!)
make did          # print your DID
make say ROOM=lobby MSG="Hello from Technocore!"
```

---

## 🌐 Web Dashboard

```bash
make setup-web    # install Flask (once)
make web          # opens http://localhost:7432
```

Features:
- Dark-mode GitHub-styled UI
- Generate DID, reveal DID, post signed messages
- Keys stay on **your machine** — never sent to a server

---

## 🔍 Offline Signature Verifier

Verify any Technocore message without a network connection:

```bash
python technocore_verify.py \
  --did   "did:key:z6Mk..." \
  --room  "lobby" \
  --nonce "1234567890" \
  --text  "Hello from Technocore!" \
  --sig   "86-char-base64url-signature"
```

Exit `0` = valid ✅, exit `1` = invalid ❌

---

## ⚙️ GitHub Action — Auto-announce on Push

Automatically posts a signed Technocore message every time you push to `main`.

**Setup (one-time):**
1. Generate your identity locally: `make init`
2. Encode the PEM: `base64 identity.pem` → copy output
3. Go to **Settings → Secrets → Actions**:
   - `TECHNOCORE_PEM` = base64 output
   - `TECHNOCORE_PASS` = your passphrase
4. Push to `main` — the Action fires automatically ✅

---

## 🔌 VS Code Setup

1. Open the folder in VS Code
2. Accept the prompt **"Install Recommended Extensions"**
3. Select the `.venv` Python interpreter when prompted

Included extensions: Python, Pylance, Black, Ruff, GitLens, REST Client, GitHub Actions, YAML.

---

## 🤝 Contributing to $FLOP Airdrop Eligibility

This toolkit itself is a **Path B** contribution — a reusable open-source tool that helps other developers participate in Technocore. To document your own contribution:

```bash
make say \
  ROOM=technocore \
  MSG="I published a Technocore developer toolkit: https://github.com/YOUR_USERNAME/YOUR_REPO. It helps developers set up DID identities with Docker, a web UI, and GitHub Actions."
```

---

## 📋 All Makefile commands

```
make help
```

| Command | Description |
|---------|-------------|
| `make setup` | Create `.venv` and install deps |
| `make setup-web` | Install Flask for web dashboard |
| `make init` | Generate encrypted DID (once!) |
| `make did` | Print public DID |
| `make say ROOM=X MSG=Y` | Post signed message |
| `make web` | Start web dashboard |
| `make verify DID=… ROOM=… NONCE=… TEXT=… SIG=…` | Verify a signature |
| `make docker-build` | Build Docker image |
| `make docker-init` | Init identity via Docker |
| `make lint` | Run Ruff linter |
| `make format` | Auto-format with Black |
| `make clean` | Remove `.venv` |

---

## License

MIT — see [LICENSE](LICENSE)
