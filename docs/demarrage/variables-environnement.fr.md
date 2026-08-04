# Variables d'environnement

Toutes les variables sont lues par `AppSettings` (`backend/app/config.py`, `pydantic-settings`), soit depuis l'environnement, soit depuis un fichier `.env` à la racine du dépôt. Les noms ne sont pas sensibles à la casse.

## Sécurité / authentification

| Variable                       | Défaut                     | Description                                                                                                                                                                                                         |
| ------------------------------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ADMIN_USERNAME`               | `admin`                    | Identifiant du compte administrateur créé au premier démarrage.                                                                                                                                                     |
| `ADMIN_EMAIL`                  | `admin@wg.ui`              | Email associé à ce compte.                                                                                                                                                                                          |
| `SECRET_KEY`                   | _(généré automatiquement)_ | Clé de signature des JWT. **Obligatoire en production** ; si absente, une clé aléatoire est générée et persistée dans `DATA_DIR/secret_key`.                                                                        |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `60`                       | Durée de vie des tokens JWT (minutes).                                                                                                                                                                              |
| `BCRYPT_ROUNDS`                | `12`                       | Coût de hachage bcrypt des mots de passe.                                                                                                                                                                           |
| `RATE_LIMIT_ENABLED`           | `true`                     | Active le rate-limiting par IP sur l'API.                                                                                                                                                                           |
| `RATE_LIMIT_MAX_REQUESTS`      | `100`                      | Nombre max de requêtes par IP sur `/api/*` par fenêtre glissante.                                                                                                                                                   |
| `RATE_LIMIT_WINDOW_SECONDS`    | `60`                       | Durée de la fenêtre glissante (secondes).                                                                                                                                                                           |
| `RATE_LIMIT_AUTH_MAX_REQUESTS` | `5`                        | Limite plus stricte sur `/api/auth/login` et `/api/auth/token`, pour freiner le brute-force.                                                                                                                        |
| `TRUSTED_PROXIES`              | _(vide)_                   | IP/CIDR des reverse-proxies de confiance, séparés par des virgules (ex. `172.16.0.0/12`). Nécessaire pour que les en-têtes `X-Forwarded-For`/`X-Forwarded-Proto` soient pris en compte — voir l'encadré ci-dessous. |

!!! danger "TRUSTED_PROXIES derrière un reverse proxy"
Sans cette variable renseignée, deux effets de bord apparaissent derrière un reverse proxy TLS :

    - le cookie de session n'est pas marqué `Secure` (le proxy TLS n'est pas détecté) ;
    - le rate-limiting regroupe **tous** les clients sur l'IP du proxy, ce qui peut bloquer tout le monde après quelques requêtes.

## API / Application

| Variable               | Défaut        | Description                                                                                 |
| ---------------------- | ------------- | ------------------------------------------------------------------------------------------- |
| `LOG_LEVEL`            | `INFO`        | Niveau de logs (`DEBUG`, `INFO`, `WARNING`…).                                               |
| `APP_VERSION`          | `Development` | Version affichée par l'application.                                                         |
| `SWAGGER_ENABLED`      | `false`       | Expose `/api/docs` (Swagger UI auto-hébergé) et `/api/openapi.json`.                        |
| `API_KEYS_ENABLED`     | `true`        | Active la création de Personal Access Tokens (PAT) depuis le profil utilisateur.            |
| `AUDIT_MAX_EVENTS`     | `10000`       | Nombre max d'événements conservés dans le journal d'audit (purge des plus anciens au-delà). |
| `AUDIT_RETENTION_DAYS` | `90`          | Durée de rétention du journal d'audit, en jours.                                            |

## Base de données

| Variable   | Défaut                                                      | Description                                                                                                                                                                          |
| ---------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `DB_PATH`  | `sqlite+aiosqlite:////var/lib/wireguard-ui/wireguard_ui.db` | URL de connexion SQLAlchemy async. Accepte aussi un chemin brut, une URL `sqlite:///`, ou `postgres://`/`postgresql://` (converties automatiquement vers le driver async `asyncpg`). |
| `DATA_DIR` | `/var/lib/wireguard-ui`                                     | Répertoire de données applicatives (DB par défaut, clé secrète générée).                                                                                                             |

## WireGuard

| Variable              | Défaut | Description                                                                                                                                       |
| --------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WIREGUARD_AUTOSTART` | `true` | Démarre automatiquement le service WireGuard au lancement de l'application (voir [lifespan](../architecture/backend.md#4-cycle-de-vie-lifespan)). |

## Email

| Variable    | Défaut           | Description                                      |
| ----------- | ---------------- | ------------------------------------------------ |
| `MAIL_FROM` | `no-reply@wg.ui` | Adresse expéditrice des emails de configuration. |
| `MAIL_NAME` | `WireGuardUI`    | Nom affiché comme expéditeur.                    |

> Les autres réglages SMTP (serveur, port, identifiants, TLS/SSL) se configurent depuis l'interface d'administration (page _SMTP_), pas via l'environnement — voir [`services/smtp.py`](../fonctions/services.md#smtppy-settingspy).

## Réglages système (hôte Docker)

Ces `sysctl` ne sont pas des variables de l'application mais doivent être activés sur le conteneur pour que WireGuard fonctionne :

| Sysctl                               | Rôle                                                                               |
| ------------------------------------ | ---------------------------------------------------------------------------------- |
| `net.ipv4.ip_forward=1`              | Nécessaire pour relayer (router) le trafic des pairs vers l'interface principale.  |
| `net.ipv4.conf.all.src_valid_mark=1` | Nécessaire pour la validation des sources après marquage de paquets par WireGuard. |
