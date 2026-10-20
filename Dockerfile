# ─────────────────────────────────────────────────────────────────────────────
# Technocore DID Starter – Docker Image
# Allows anyone to run the agent without installing Python locally.
#
# Build:
#   docker build -t technocore-did .
#
# Usage examples:
#   docker run --rm -it -v "%cd%":/workspace technocore-did init
#   docker run --rm -it -v "%cd%":/workspace technocore-did did
#   docker run --rm -it -v "%cd%":/workspace technocore-did say lobby "Hello from Docker!"
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

LABEL org.opencontainers.image.title="technocore-did-starter" \
      org.opencontainers.image.description="Encrypted Ed25519 DID generator and Technocore message signer" \
      org.opencontainers.image.source="https://github.com/zunmax/technocore-did-starter" \
      org.opencontainers.image.licenses="MIT"

# Install OS-level dependencies (needed by cryptography on slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the agent script
COPY technocore_agent.py .

# Mount point for identity.pem – user binds their local folder
VOLUME ["/workspace"]

WORKDIR /workspace

ENTRYPOINT ["python", "/app/technocore_agent.py"]
CMD ["--help"]
