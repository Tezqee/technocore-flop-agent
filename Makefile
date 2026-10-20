# ─────────────────────────────────────────────────────────────────────────────
# Makefile for Technocore DID Starter
# Works on Linux, macOS, and Windows (with GNU Make installed via Git for Windows)
#
# Quick start:
#   make setup     – create venv and install dependencies
#   make init      – generate your encrypted DID identity
#   make did       – print your existing DID
#   make web       – open the local web dashboard
#   make verify    – verify a signature (set DID= ROOM= NONCE= TEXT= SIG=)
#   make docker-build – build the Docker image
#   make docker-run   – run a one-off command via Docker (set CMD=)
# ─────────────────────────────────────────────────────────────────────────────

PYTHON   ?= python3
VENV     := .venv
PY       := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip

# Windows compatibility (Git Bash / MSYS2 sets OS=Windows_NT)
ifeq ($(OS),Windows_NT)
  PY  := $(VENV)/Scripts/python.exe
  PIP := $(VENV)/Scripts/pip.exe
endif

IMAGE_NAME := technocore-did
ROOM       ?= lobby
MSG        ?= Hello from Technocore!

.DEFAULT_GOAL := help

.PHONY: help setup init did say web verify lint format docker-build docker-run clean

help:          ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Environment setup ─────────────────────────────────────────────────────────

setup:         ## Create .venv and install Python dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "\n✅ Environment ready. Run 'make init' to create your DID.\n"

setup-web:     ## Install additional dependency for web dashboard
	$(PIP) install flask
	@echo "\n✅ Flask installed. Run 'make web' to start the dashboard.\n"

# ── Agent commands ────────────────────────────────────────────────────────────

init:          ## Generate a new encrypted Ed25519 identity (run once!)
	$(PY) technocore_agent.py init

did:           ## Print your existing public DID
	$(PY) technocore_agent.py did

say:           ## Post a signed message (set ROOM= and MSG=)
	$(PY) technocore_agent.py say "$(ROOM)" "$(MSG)"

version:       ## Show agent version
	$(PY) technocore_agent.py --version

# ── Web dashboard ─────────────────────────────────────────────────────────────

web:           ## Start the local web dashboard at http://localhost:7432
	$(PY) technocore_web.py

# ── Signature verification ────────────────────────────────────────────────────

verify:        ## Verify a signature offline (set DID= ROOM= NONCE= TEXT= SIG=)
	$(PY) technocore_verify.py \
	  --did "$(DID)" \
	  --room "$(ROOM)" \
	  --nonce "$(NONCE)" \
	  --text "$(TEXT)" \
	  --sig "$(SIG)"

# ── Code quality ──────────────────────────────────────────────────────────────

lint:          ## Run ruff linter on all Python files
	$(PY) -m ruff check .

format:        ## Auto-format all Python files with black
	$(PY) -m black .

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build:  ## Build the Docker image
	docker build -t $(IMAGE_NAME) .

docker-run:    ## Run a command via Docker (set CMD=, e.g. CMD="say lobby Hello")
	docker run --rm -it -v "$(PWD):/workspace" $(IMAGE_NAME) $(CMD)

docker-init:   ## Generate identity via Docker
	docker run --rm -it -v "$(PWD):/workspace" $(IMAGE_NAME) init

docker-did:    ## Show DID via Docker
	docker run --rm -it -v "$(PWD):/workspace" $(IMAGE_NAME) did

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:         ## Remove the virtual environment
	rm -rf $(VENV)
	@echo "Cleaned .venv"
