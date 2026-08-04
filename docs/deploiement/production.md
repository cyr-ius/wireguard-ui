# Recommandations production

## Sécurité de base

- **`SECRET_KEY`** : définissez une valeur longue et aléatoire explicitement. Sans cela, une clé est générée automatiquement et stockée dans `/var/lib/wireguard-ui/secret_key` — cela fonctionne, mais toute réinstallation ou perte du volume de données invalide toutes les sessions, et la clé ne peut pas être partagée entre plusieurs réplicas.

  ```bash
  openssl rand -base64 64
  ```

- **Identifiants admin** : changez le mot de passe généré automatiquement dès la première connexion (page _Profil_). Envisagez de définir `ADMIN_USERNAME`/`ADMIN_EMAIL` avant le tout premier démarrage si vous ne voulez pas des valeurs par défaut (`admin`/`admin@wg.ui`).
- **`SWAGGER_ENABLED`** : laissez à `false` (défaut) en production si l'exposition de la documentation OpenAPI n'est pas nécessaire.

## Derrière un reverse proxy TLS

Si vous exposez l'interface via Traefik, Nginx, Caddy, etc. :

1. Terminez le TLS au niveau du reverse proxy.
2. Renseignez **`TRUSTED_PROXIES`** avec l'IP ou le sous-réseau du proxy (ex. `172.16.0.0/12` pour un réseau Docker par défaut). Sans cela :
   - le cookie de session `access_token` ne sera pas marqué `Secure` (HTTPS non détecté) ;
   - le rate-limiting regroupera **tous** les visiteurs sur l'IP du proxy, ce qui peut bloquer l'accès à tout le monde après quelques requêtes.
3. Le reverse proxy doit transmettre les en-têtes `X-Forwarded-For` et `X-Forwarded-Proto`.

Voir le détail dans [Authentification & sécurité](../fonctions/authentification.md) et [Variables d'environnement](../demarrage/variables-environnement.md#securite-authentification).

## Rate limiting

Activé par défaut (`RATE_LIMIT_ENABLED=true`). Ajustez `RATE_LIMIT_MAX_REQUESTS`/`RATE_LIMIT_WINDOW_SECONDS` selon votre trafic normal, et gardez `RATE_LIMIT_AUTH_MAX_REQUESTS` bas pour limiter le brute-force sur `/api/auth/login`.

!!! warning "Déploiement mono-worker"
Le rate-limiter et l'état du service WireGuard sont gérés **en mémoire, par process**. L'image ne doit pas être répliquée horizontalement (plusieurs conteneurs actifs simultanément) sans revoir cette architecture — un seul conteneur `wireguard-ui` doit gérer une interface `wg0` donnée.

## Sauvegardes

Deux volumes à sauvegarder régulièrement :

| Volume                  | Contenu                                                                        | Criticité                                                 |
| ----------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------- |
| `/var/lib/wireguard-ui` | Base SQLite (utilisateurs, clients, réglages, audit, PAT), clé secrète générée | Élevée — perte = perte de toutes les données applicatives |
| `/etc/wireguard`        | `wg0.conf`, clés serveur/clients actives                                       | Élevée — perte = reconstruction manuelle des tunnels      |

## Base de données en production

SQLite convient pour un déploiement mono-instance. Pour un environnement plus exigeant (sauvegardes centralisées, réplication), configurez `DB_PATH` vers une instance PostgreSQL :

```env
DB_PATH=postgresql://user:password@host:5432/wireguard_ui
```

L'URL est automatiquement convertie vers le driver asynchrone `asyncpg` — voir [`config.py`](../architecture/backend.md#configpy).

## Audit et conformité

- `AUDIT_RETENTION_DAYS` (défaut 90) et `AUDIT_MAX_EVENTS` (défaut 10 000) contrôlent la purge automatique du journal d'audit. Augmentez ces valeurs si une politique de conformité impose une rétention plus longue.
- Le journal est accessible via `GET /api/audit` (page _Audit_, admin uniquement) — pensez à l'exporter périodiquement si la rétention configurée est courte.

## Emails

Configurez SMTP depuis l'interface d'administration (page _SMTP_), pas via l'environnement (seuls `MAIL_FROM`/`MAIL_NAME` sont des variables d'environnement, utilisées comme repli). Testez la configuration avec le bouton _Envoyer un email de test_ avant de compter dessus pour l'enrôlement des clients.

## Checklist avant mise en production

- [ ] `SECRET_KEY` définie explicitement et sauvegardée.
- [ ] Mot de passe admin changé.
- [ ] `TRUSTED_PROXIES` renseigné si un reverse proxy est utilisé.
- [ ] TLS activé au niveau du reverse proxy.
- [ ] Volumes `wg_config` et `wireguard-ui_data` sauvegardés automatiquement.
- [ ] `SWAGGER_ENABLED=false` sauf besoin explicite.
- [ ] SMTP configuré et testé si l'envoi de configuration par email est utilisé.
- [ ] OIDC configuré si une connexion SSO est requise (voir [Authentification & sécurité](../fonctions/authentification.md#oidc-single-sign-on)).
