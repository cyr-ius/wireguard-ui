# ─── FastAPI + Angular Development Image ───────────────────────────────────────

FROM mcr.microsoft.com/devcontainers/base:alpine

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# ── System dependencies (apk = gestionnaire Alpine) ────────────────────────────
RUN apk add --no-cache \
    curl \
    git \
    python3 \
    nodejs \
    npm \
    wireguard-tools \
    iptables

# ── uv (fast Python package manager) ──────────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ── Environment variables for Python and uv ─────────────────────────────────────────
ENV UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
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

RUN mkdir -p /workspaces/wireguard-ui/.data_env \
    && chown vscode:vscode /workspaces/wireguard-ui/.data_env

USER vscode

# ── Dependencies ───────────────────────────────────────────────────────────────
RUN uv tool install ruff \
    && uv tool install prek

# ── Workspace ──────────────────────────────────────────────────────────────────
ARG WORKSPACE=/workspaces
WORKDIR /${WORKSPACE}

# ── Volume for WireGuard configuration and data ────────────────────────────────
VOLUME ["${WORKSPACE}/.data_env", "/etc/wireguard"]
