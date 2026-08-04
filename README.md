# 🔒 WireGuard UI

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

**WireGuard UI** est une interface web pour administrer un serveur WireGuard sans
manipuler directement les fichiers de configuration (`wg0.conf`, clés, règles
`iptables`). Gestion des pairs, export de configuration, authentification OIDC,
journal d'audit — le tout dans une image Docker unique.

<img width="1295" height="948" alt="Tableau de bord WireGuard UI" src="https://github.com/user-attachments/assets/f147aeed-9d02-43c4-b686-aa400d06942c" />

---

## Fonctionnalités

- 🔧 Gestion des pairs (création, édition, révocation) avec suggestion d'IP libre
- 📄 Génération de configuration client, export en fichier `.conf` et QR code
- ✉️ Envoi de la configuration par email (SMTP configurable depuis l'UI)
- 🔐 Authentification locale, **OIDC** (SSO) et **Personal Access Tokens** pour l'API
- 📋 Journal d'audit des actions sensibles, avec rétention configurable
- 🩺 Healthcheck intégré (`GET /api/health`)
- 🐳 Image Docker unique, `linux/amd64` / `linux/arm64` (Raspberry Pi, Apple Silicon)

Backend FastAPI (async) + frontend Angular (Signals, zoneless) — voir la page
[Architecture](https://cyr-ius.github.io/wireguard-ui/architecture/backend/)
pour le détail de la stack technique.

---

## Démarrage rapide

```bash
docker run -d \
  --name wireguard-ui \
  --cap-add NET_ADMIN \
  --sysctl net.ipv4.ip_forward=1 \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  -p 8000:8000 \
  -p 51820:51820/udp \
  -e SECRET_KEY=your-secret-key \
  -v wg_config:/etc/wireguard \
  -v wireguard-ui_data:/var/lib/wireguard-ui \
  cyrius44/wireguard-ui:latest
```

Un mot de passe admin est généré automatiquement au premier démarrage et
**affiché une seule fois** dans les logs — l'utilisateur par défaut est `admin` :

```bash
docker logs wireguard-ui | grep -A4 "Initial admin account"
```

Ouvrez **http://localhost:8000** et connectez-vous avec `admin` et ce mot de passe.

Ou avec Docker Compose :

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
    environment:
      - SECRET_KEY=your-secret-key
    volumes:
      - wg_config:/etc/wireguard
      - wireguard-ui_data:/var/lib/wireguard-ui

volumes:
  wg_config:
  wireguard-ui_data:
```

> **Note :** `SECRET_KEY` doit être remplacé par une valeur longue et aléatoire —
> l'application refuse de démarrer avec sa valeur par défaut en production.

Pour le guide complet (installation locale sans Docker, variables
d'environnement, recommandations de production) voir
**[Démarrage](https://cyr-ius.github.io/wireguard-ui/demarrage/quickstart-docker/)**.

---

## Documentation

La documentation complète — architecture, référence des variables
d'environnement, routers & services, déploiement — est publiée sur
**[cyr-ius.github.io/wireguard-ui](https://cyr-ius.github.io/wireguard-ui/)**.

| Vous cherchez...                                  | Allez à...                                                                                             |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Toutes les variables d'environnement              | [Variables d'environnement](https://cyr-ius.github.io/wireguard-ui/demarrage/variables-environnement/) |
| Installation locale (dev, sans Docker)            | [Installation locale](https://cyr-ius.github.io/wireguard-ui/demarrage/installation-locale/)           |
| Architecture backend / frontend / base de données | [Architecture](https://cyr-ius.github.io/wireguard-ui/architecture/backend/)                           |
| Routers, services métier, authentification        | [Fonctions & API](https://cyr-ius.github.io/wireguard-ui/fonctions/routers/)                           |
| Déploiement & recommandations production          | [Déploiement](https://cyr-ius.github.io/wireguard-ui/deploiement/docker/)                              |

---

## License

MIT — voir [LICENSE](LICENSE) pour le détail.

## About

Auteur : [@cyr-ius](https://github.com/cyr-ius) — Sponsor : [GitHub Sponsors](https://github.com/sponsors/cyr-ius)
