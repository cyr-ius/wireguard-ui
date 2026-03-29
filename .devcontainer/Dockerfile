# ─── FastAPI + Angular Development Image ─────────────────────────────────────────────

FROM mcr.microsoft.com/devcontainers/base:alpine

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# ── System dependencies (apk = gestionnaire Alpine) ────────────────────────
RUN apk add --no-cache \
    curl \
    git \
    python3 \
    python3-dev \
    build-base \
    linux-headers \
    nodejs \
    npm \
    wireguard-tools \
    iptables

# ── uv (fast Python package manager) ──────────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Node.js LTS + Angular CLI ──────────────────────────────────────────────────
ENV NG_CLI_ANALYTICS=ci \
    NG_FORCE_TTY=false

RUN npm install -g \
    @angular/cli@21 \
    prettier@3

# ── WireGuard directory ────────────────────────────────────────────────────────
RUN mkdir -p /etc/wireguard \
    && chown vscode:vscode /etc/wireguard

USER vscode

# ── Dépendances Python via uv ───────────────────────────────────────────────
RUN uv tool install ruff \
    && uv tool install pre-commit

# ── Workspace ───────────────────────────────────────────────────────────────
VOLUME ["/data"]

WORKDIR /workspace
