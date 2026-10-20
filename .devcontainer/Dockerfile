# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────────────────────
# devcontainer Dockerfile
# Opens the repo in a ready-to-go environment via:
#   VS Code → "Reopen in Container"   OR
#   GitHub Codespaces (zero install)
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl gcc libffi-dev make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir flask black ruff

CMD ["sleep", "infinity"]
