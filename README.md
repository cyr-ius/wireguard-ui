# 🔒 WireGuard UI

_Lire ceci en [français](README.fr.md)._

![licence] ![python] ![angular] [![ci::status]][ci::github] [![docker::pulls]][docker::hub] [![documentation::badge]][documentation::web]

[licence]: https://img.shields.io/github/license/cyr-ius/wireguard-ui?label=Licence&color=blue
[python]: https://img.shields.io/badge/Python-3.14%2B-blue?logo=python
[angular]: https://img.shields.io/badge/Angular-22-blue?logo=angular
[ci::status]: https://img.shields.io/github/actions/workflow/status/cyr-ius/wireguard-ui/docker-publish.yml?color=blue&logo=github
[ci::github]: https://github.com/cyr-ius/wireguard-ui/actions
[docker::pulls]: https://img.shields.io/docker/pulls/cyrius44/wireguard-ui.svg?logo=docker
[docker::hub]: https://hub.docker.com/r/cyrius44/wireguard
[documentation::badge]: https://img.shields.io/badge/Documentation-Wiki-green?logo=helpdesk
[documentation::web]: https://cyr-ius.github.io/wireguard-ui/

**WireGuard UI** is a web interface for managing a WireGuard server without
touching configuration files directly (`wg0.conf`, keys, `iptables` rules).
Peer management, configuration export, OIDC authentication, audit log — all
in a single Docker image.

<img width="1295" height="948" alt="WireGuard UI dashboard" src="https://github.com/user-attachments/assets/f147aeed-9d02-43c4-b686-aa400d06942c" />

---

## Features

- 🔧 Peer management (create, edit, revoke) with free IP suggestion
- 📄 Client configuration generation, export as `.conf` file and QR code
- ✉️ Send configuration by email (SMTP configurable from the UI)
- 🔐 Local authentication, **OIDC** (SSO) and **Personal Access Tokens** for the API
- 📋 Audit log of sensitive actions, with configurable retention
- 🩺 Built-in healthcheck (`GET /api/health`)
- 🐳 Single Docker image, `linux/amd64` / `linux/arm64` (Raspberry Pi, Apple Silicon)

FastAPI (async) backend + Angular (Signals, zoneless) frontend — see the
[Architecture](https://cyr-ius.github.io/wireguard-ui/architecture/backend/)
page for the technical stack details.

---

## Quick start

```bash
docker run -d \
  --name wireguard-ui \
  --cap-add NET_ADMIN \
  --sysctl net.ipv4.ip_forward=1 \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  -p 8000:8000 \
  -p 51820:51820/udp \
  -v wg_config:/etc/wireguard \
  -v wireguard-ui_data:/var/lib/wireguard-ui \
  cyrius44/wireguard-ui:latest
```

An admin password is generated automatically on first startup and
**shown only once** in the logs — the default user is `admin`:

```bash
docker logs wireguard-ui | grep -A4 "Initial admin account"
```

Open **http://localhost:8000** and log in with `admin` and this password.

Or with Docker Compose:

```yaml
services:
  wireguard-ui:
    image: cyrius44/wireguard-ui:latest
    container_name: wireguard-ui
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv4.conf.all.src_valid_mark=1
    ports:
      - "8000:8000"
      - "51820:51820/udp"
    volumes:
      - wg_config:/etc/wireguard
      - wireguard-ui_data:/var/lib/wireguard-ui

volumes:
  wg_config:
  wireguard-ui_data:
```

> **Note:** `SECRET_KEY` is optional — if absent, the application automatically
> generates a random key and persists it in `wireguard-ui_data`. In
> production, set it explicitly to share sessions across multiple replicas
> or survive a loss of the data volume.

For the full guide (local installation without Docker, environment
variables, production recommendations) see
**[Getting started](https://cyr-ius.github.io/wireguard-ui/demarrage/quickstart-docker/)**.

---

## Documentation

The full documentation — architecture, environment variable reference,
routers & services, deployment — is published at
**[cyr-ius.github.io/wireguard-ui](https://cyr-ius.github.io/wireguard-ui/)**.

| Looking for...                             | Go to...                                                                                           |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| All environment variables                  | [Environment variables](https://cyr-ius.github.io/wireguard-ui/demarrage/variables-environnement/) |
| Local installation (dev, no Docker)        | [Local installation](https://cyr-ius.github.io/wireguard-ui/demarrage/installation-locale/)        |
| Backend / frontend / database architecture | [Architecture](https://cyr-ius.github.io/wireguard-ui/architecture/backend/)                       |
| Routers, business services, authentication | [Functions & API](https://cyr-ius.github.io/wireguard-ui/fonctions/routers/)                       |
| Deployment & production recommendations    | [Deployment](https://cyr-ius.github.io/wireguard-ui/deploiement/docker/)                           |

---

## License

MIT — see [LICENSE](LICENSE) for details.

## About

Author: [@cyr-ius](https://github.com/cyr-ius) — Sponsor: [GitHub Sponsors](https://github.com/sponsors/cyr-ius)
