# Démarrage rapide (Docker)

C'est la méthode recommandée pour utiliser WireGuard UI en production ou pour le tester rapidement.

## Prérequis

- Docker (et Docker Compose si vous utilisez la méthode Compose).
- Les capacités réseau nécessaires pour manipuler des interfaces WireGuard : le conteneur doit tourner avec `NET_ADMIN` et certains `sysctl` activés (voir ci-dessous).

## Étape 1 — Docker CLI

```bash
docker run -d \
  --name wireguard-ui \
  --cap-add NET_ADMIN \
  --sysctl net.ipv4.ip_forward=1 \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  -p 8000:8000 \
  -p 51820:51820/udp \
  -e ADMIN_USERNAME=admin \
  -e SECRET_KEY=your-secret-key \
  -v wg_config:/etc/wireguard \
  -v wireguard-ui_data:/var/lib/wireguard-ui \
  cyrius44/wireguard-ui:latest
```

Ouvrez ensuite **http://localhost:8000**.

## Étape 2 — Docker Compose (alternative)

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
      - ADMIN_USERNAME=admin
      - SECRET_KEY=your-secret-key
    volumes:
      - wg_config:/etc/wireguard
      - wireguard-ui_data:/var/lib/wireguard-ui

volumes:
  wg_config:
  wireguard-ui_data:
```

```bash
docker compose up -d
```

## Étape 3 — Récupérer le mot de passe admin

Au tout premier démarrage, le backend exécute `seed_initial_data()` ([services/seed.py](../fonctions/services.md#seedpy)) qui crée :

- les rôles `admin` et `user` ;
- un compte administrateur (`ADMIN_USERNAME`, par défaut `admin`) avec un **mot de passe généré aléatoirement** ;
- les réglages globaux, OIDC et SMTP par défaut.

Ce mot de passe n'est affiché **qu'une seule fois**, dans les logs du conteneur :

```bash
docker logs wireguard-ui
```

Changez-le immédiatement depuis la page **Profil** une fois connecté.

## Étape 4 — Vérifier que le service est en bonne santé

```bash
curl http://localhost:8000/api/health
```

```json
{ "status": "healthy", "app": "WireGuard UI", "version": "..." }
```

## Pourquoi ces `cap_add` / `sysctl` sont nécessaires

| Paramètre                            | Rôle                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `--cap-add NET_ADMIN`                | Autorise la création/gestion de l'interface `wg0` et des règles `iptables` depuis le conteneur.   |
| `net.ipv4.ip_forward=1`              | Active le routage IP nécessaire pour relayer le trafic des pairs vers le réseau.                  |
| `net.ipv4.conf.all.src_valid_mark=1` | Nécessaire pour que WireGuard puisse valider les sources après le marquage de paquets (`fwmark`). |

## Ports exposés

| Port        | Usage                                  |
| ----------- | -------------------------------------- |
| `8000/tcp`  | Interface web + API REST               |
| `51820/udp` | Port d'écoute WireGuard pour les pairs |

## Volumes persistants

| Volume              | Point de montage        | Contenu                                     |
| ------------------- | ----------------------- | ------------------------------------------- |
| `wg_config`         | `/etc/wireguard`        | Configuration WireGuard (`wg0.conf`, clés)  |
| `wireguard-ui_data` | `/var/lib/wireguard-ui` | Base de données SQLite, clé secrète générée |

!!! warning "SECRET_KEY obligatoire"
Sans `SECRET_KEY` défini explicitement, l'application en génère une automatiquement et la persiste dans `/var/lib/wireguard-ui/secret_key`. En production, définissez une valeur longue et aléatoire vous-même — voir [Variables d'environnement](variables-environnement.md) et [Recommandations production](../deploiement/production.md).

## Étape suivante

Une fois l'interface accessible, la première configuration côté administrateur consiste à :

1. Se connecter avec le compte admin.
2. Configurer le **serveur WireGuard** — page _Serveur_ : adresse réseau (CIDR), port d'écoute, puis cliquer sur **Generate Key Pair** pour générer la paire de clés (privée/publique) du serveur. Cette étape est indispensable : tant qu'aucune clé n'est générée (ou renseignée manuellement), la configuration ne peut pas être enregistrée ni appliquée.
3. Renseigner l'**adresse d'endpoint** — page _Global Settings_, champ **Endpoint Address** : il s'agit du nom d'hôte public (ex. `vpn.exemple.com`) ou de l'adresse IP publique par laquelle les clients WireGuard joindront le serveur. Sans cette valeur, les fichiers de configuration générés pour les clients seront incorrects et ces derniers ne pourront pas se connecter — pensez-y avant de créer des pairs.
4. Créer les premiers **pairs (clients)** — page _Clients_.
5. Éventuellement configurer **SMTP** (envoi de la config par email) et **OIDC** (SSO).

!!! warning "Ordre important"
Générez toujours les **clés du serveur** et renseignez l'**adresse d'endpoint** avant de créer des clients. Un pair créé avant que ces deux éléments soient définis produira une configuration `.conf`/QR code invalide (clé publique du serveur ou endpoint manquants), qu'il faudra régénérer et renvoyer au client une fois le serveur correctement configuré.

Ces écrans correspondent aux routers documentés dans [Routers (endpoints)](../fonctions/routers.md) (`server.py` pour les clés, `settings.py` pour l'endpoint).
