# WireGuard UI

**WireGuard UI** is a web interface for administering a WireGuard server without directly manipulating configuration files (`wg0.conf`, keys, `iptables` rules).

## Main features

- Peer (client) management: creation, editing, revocation, with automatic free IP suggestion.
- Client configuration generation, export as a `.conf` file and as a QR code.
- Sending the configuration by email (SMTP configurable from the interface).
- Local (password) authentication, **OIDC** (SSO) and **Personal Access Tokens (PAT)** for the API.
- Audit log of sensitive actions (logins, user management, configuration changes…), with configurable retention.
- Built-in healthcheck (`GET /api/health`).
- Single Docker image, production-ready.

## Technical stack

| Layer          | Technology                                                           |
| -------------- | -------------------------------------------------------------------- |
| **Frontend**   | Angular 21+ — Signals, Signal Forms, Zoneless, standalone components |
| **Style**      | Bootstrap 5 + Bootstrap Icons                                        |
| **Backend**    | FastAPI + Python 3.14 (fully asynchronous)                           |
| **Validation** | Pydantic v2 / SQLModel                                               |
| **Database**   | SQLite (default) or PostgreSQL, migrations via Alembic               |
| **Container**  | Single image — the backend also serves the Angular build             |
| **Platforms**  | `linux/amd64`, `linux/arm64` (Raspberry Pi, Apple Silicon)           |

## How to read this documentation

- Start with **[Quick start (Docker)](demarrage/quickstart-docker.md)** if you simply want to launch the application.
- See **[Local installation (dev)](demarrage/installation-locale.md)** if you are developing on the project.
- The **[Architecture](architecture/backend.md)** section explains how the code is organized, both backend and frontend.
- The **[Functions & API](fonctions/routers.md)** section details the role of each router and business service.
- The **[Deployment](deploiement/docker.md)** section covers Docker and production recommendations.

!!! info "General diagram"
`mermaid
    flowchart LR
        subgraph Client["Browser"]
            UI[Angular SPA]
        end
        subgraph Serveur["wireguard-ui container"]
            API[FastAPI backend]
            DB[(SQLite / PostgreSQL)]
            WG[wg-quick / iptables]
        end
        UI -- "HTTP /api/*\n(JWT + CSRF cookies)" --> API
        API --> DB
        API -- "subprocess" --> WG
        WG -- "UDP 51820" --> Peers["WireGuard peers"]
    `
