# ─── Stage 1: Build Angular Frontend ──────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

# Install dependencies
COPY frontend/package.json ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Final container ─────────────────────────────────────────────
FROM python:3.14-alpine

LABEL maintainer="cyr-ius <https://github.com/cyr-ius>"
LABEL org.opencontainers.image.title="WireGuardUI"
LABEL org.opencontainers.image.description="WireGuardUI - Secure tunnel management"
LABEL org.opencontainers.image.source="https://github.com/cyr-ius/wireguard-ui"
LABEL org.opencontainers.image.url="https://github.com/cyr-ius/wireguard-ui"
LABEL org.opencontainers.image.licenses="MIT"

RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    libffi-dev \
    wireguard-tools \
    iptables \
    supervisor \
    ca-certificates


COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy Supervisor configuration template file
COPY ./docker/supervisord.conf /etc/supervisor/supervisord.conf

ENV UV_NO_CACHE=true
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PYTHONUNBUFFERED=1
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

WORKDIR /app

RUN --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    uv sync --frozen --no-dev

COPY --from=frontend-builder /build/frontend/dist/wireguard-ui/browser ./frontend

COPY backend ./backend

ARG VERSION
ENV APP_VERSION=${VERSION:-"1.0.0"}

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

VOLUME [ "/etc/wireguard", "/data" ]

EXPOSE 8000/tcp 51820/udp

CMD ["/usr/bin/supervisord", "-c","/etc/supervisor/supervisord.conf"]
