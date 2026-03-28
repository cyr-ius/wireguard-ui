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

# ── Installation de uv (gestionnaire Python ultra-rapide) ──────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ── Configurer uv pour installer dans le système (pas de venv par défaut)
ENV UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Angular CLI 21 + outils globaux ────────────────────────────────────────
ENV NG_CLI_ANALYTICS=ci \
    NG_FORCE_TTY=false
RUN npm install -g \
    @angular/cli@21 \
    typescript \
    prettier@3

#  ── Wireguard  ────────────────────────────────────────
RUN mkdir -p /etc/wireguard \
    && chown vscode:vscode /etc/wireguard

USER vscode

# ── Dépendances Python via uv ───────────────────────────────────────────────
RUN uv tool install ruff \
    && uv tool install pre-commit

# ── Workspace ───────────────────────────────────────────────────────────────
WORKDIR /workspace
