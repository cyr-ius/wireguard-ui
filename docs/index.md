# WireGuard UI

**WireGuard UI** est une interface web permettant d'administrer un serveur WireGuard sans manipuler directement les fichiers de configuration (`wg0.conf`, clés, règles `iptables`).

## Fonctionnalités principales

- Gestion des pairs (clients) : création, édition, révocation, avec suggestion automatique d'IP libre.
- Génération de configuration client, export en fichier `.conf` et en QR code.
- Envoi de la configuration par email (SMTP configurable depuis l'interface).
- Authentification locale (mot de passe), **OIDC** (SSO) et **Personal Access Tokens (PAT)** pour l'API.
- Journal d'audit des actions sensibles (connexions, gestion des utilisateurs, changements de configuration…), avec rétention configurable.
- Healthcheck intégré (`GET /api/health`).
- Image Docker unique, prête pour la production.

## Stack technique

| Couche              | Technologie                                                          |
| ------------------- | -------------------------------------------------------------------- |
| **Frontend**        | Angular 21+ — Signals, Signal Forms, Zoneless, composants standalone |
| **Style**           | Bootstrap 5 + Bootstrap Icons                                        |
| **Backend**         | FastAPI + Python 3.14 (entièrement asynchrone)                       |
| **Validation**      | Pydantic v2 / SQLModel                                               |
| **Base de données** | SQLite (par défaut) ou PostgreSQL, migrations via Alembic            |
| **Conteneur**       | Image unique — le backend sert aussi le build Angular                |
| **Plateformes**     | `linux/amd64`, `linux/arm64` (Raspberry Pi, Apple Silicon)           |

## Comment lire cette documentation

- Commencez par **[Démarrage rapide (Docker)](demarrage/quickstart-docker.md)** si vous voulez simplement lancer l'application.
- Consultez **[Installation locale (dev)](demarrage/installation-locale.md)** si vous développez sur le projet.
- La section **[Architecture](architecture/backend.md)** explique comment le code est organisé, côté backend comme côté frontend.
- La section **[Fonctions & API](fonctions/routers.md)** détaille le rôle de chaque router et service métier.
- La section **[Déploiement](deploiement/docker.md)** couvre Docker et les recommandations de mise en production.

!!! info "Schéma général"
`mermaid
    flowchart LR
        subgraph Client["Navigateur"]
            UI[Angular SPA]
        end
        subgraph Serveur["Conteneur wireguard-ui"]
            API[FastAPI backend]
            DB[(SQLite / PostgreSQL)]
            WG[wg-quick / iptables]
        end
        UI -- "HTTP /api/*\n(cookies JWT + CSRF)" --> API
        API --> DB
        API -- "subprocess" --> WG
        WG -- "UDP 51820" --> Peers["Pairs WireGuard"]
    `
