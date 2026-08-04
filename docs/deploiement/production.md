# Production recommendations

## Basic security

- **`SECRET_KEY`**: set a long, random value explicitly. Without it, a key is generated automatically and stored in `/var/lib/wireguard-ui/secret_key` — this works, but any reinstall or loss of the data volume invalidates all sessions, and the key cannot be shared across multiple replicas.

  ```bash
  openssl rand -base64 64
  ```

- **Admin credentials**: change the automatically generated password on first login (_Profile_ page). Consider setting `ADMIN_USERNAME`/`ADMIN_EMAIL` before the very first startup if you don't want the default values (`admin`/`admin@wg.ui`).
- **`SWAGGER_ENABLED`**: leave at `false` (default) in production if exposing the OpenAPI documentation is not needed.

## Behind a TLS reverse proxy

If you expose the interface via Traefik, Nginx, Caddy, etc.:

1. Terminate TLS at the reverse proxy level.
2. Set **`TRUSTED_PROXIES`** to the proxy's IP or subnet (e.g. `172.16.0.0/12` for a default Docker network). Without this:
   - the `access_token` session cookie will not be marked `Secure` (HTTPS not detected);
   - rate limiting will group **all** visitors under the proxy's IP, which can lock out everyone after a few requests.
3. The reverse proxy must forward the `X-Forwarded-For` and `X-Forwarded-Proto` headers.

See the details in [Authentication & security](../fonctions/authentification.md) and [Environment variables](../demarrage/variables-environnement.md#security-authentication).

## Rate limiting

Enabled by default (`RATE_LIMIT_ENABLED=true`). Adjust `RATE_LIMIT_MAX_REQUESTS`/`RATE_LIMIT_WINDOW_SECONDS` to your normal traffic, and keep `RATE_LIMIT_AUTH_MAX_REQUESTS` low to limit brute-force attempts on `/api/auth/login`.

!!! warning "Single-worker deployment"
The rate-limiter and the WireGuard service state are managed **in memory, per process**. The image must not be scaled horizontally (multiple containers running simultaneously) without revisiting this architecture — a single `wireguard-ui` container must manage a given `wg0` interface.

## Backups

Two volumes to back up regularly:

| Volume                  | Content                                                                      | Criticality                                    |
| ----------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| `/var/lib/wireguard-ui` | SQLite database (users, clients, settings, audit, PAT), generated secret key | High — loss = loss of all application data     |
| `/etc/wireguard`        | `wg0.conf`, active server/client keys                                        | High — loss = manual reconstruction of tunnels |

## Database in production

SQLite is suitable for a single-instance deployment. For a more demanding environment (centralized backups, replication), point `DB_PATH` to a PostgreSQL instance:

```env
DB_PATH=postgresql://user:password@host:5432/wireguard_ui
```

The URL is automatically converted to the async `asyncpg` driver — see [`config.py`](../architecture/backend.md#configpy).

## Audit and compliance

- `AUDIT_RETENTION_DAYS` (default 90) and `AUDIT_MAX_EVENTS` (default 10,000) control automatic purging of the audit log. Increase these values if a compliance policy requires longer retention.
- The log is accessible via `GET /api/audit` (_Audit_ page, admin only) — consider exporting it periodically if the configured retention is short.

## Emails

Configure SMTP from the admin interface (_SMTP_ page), not via the environment (only `MAIL_FROM`/`MAIL_NAME` are environment variables, used as a fallback). Test the configuration with the _Send test email_ button before relying on it for client enrollment.

## Pre-production checklist

- [ ] `SECRET_KEY` explicitly set and backed up.
- [ ] Admin password changed.
- [ ] `TRUSTED_PROXIES` set if a reverse proxy is used.
- [ ] TLS enabled at the reverse proxy level.
- [ ] `wg_config` and `wireguard-ui_data` volumes backed up automatically.
- [ ] `SWAGGER_ENABLED=false` unless explicitly needed.
- [ ] SMTP configured and tested if sending configuration by email is used.
- [ ] OIDC configured if SSO login is required (see [Authentication & security](../fonctions/authentification.md#oidc-single-sign-on)).
