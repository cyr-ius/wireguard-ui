# Environment variables

All variables are read by `AppSettings` (`backend/app/config.py`, `pydantic-settings`), either from the environment or from a `.env` file at the repository root. Names are case-insensitive.

## Security / authentication

| Variable                       | Default                     | Description                                                                                                                                                                              |
| ------------------------------ | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ADMIN_USERNAME`               | `admin`                     | Username of the administrator account created on first startup.                                                                                                                          |
| `ADMIN_EMAIL`                  | `admin@wg.ui`               | Email associated with this account.                                                                                                                                                      |
| `SECRET_KEY`                   | _(generated automatically)_ | JWT signing key. **Required in production**; if absent, a random key is generated and persisted in `DATA_DIR/secret_key`.                                                                |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `60`                        | Lifetime of JWT tokens (minutes).                                                                                                                                                        |
| `BCRYPT_ROUNDS`                | `12`                        | bcrypt hashing cost for passwords.                                                                                                                                                       |
| `RATE_LIMIT_ENABLED`           | `true`                      | Enables per-IP rate limiting on the API.                                                                                                                                                 |
| `RATE_LIMIT_MAX_REQUESTS`      | `100`                       | Max number of requests per IP on `/api/*` within a sliding window.                                                                                                                       |
| `RATE_LIMIT_WINDOW_SECONDS`    | `60`                        | Duration of the sliding window (seconds).                                                                                                                                                |
| `RATE_LIMIT_AUTH_MAX_REQUESTS` | `5`                         | Stricter limit on `/api/auth/login` and `/api/auth/token`, to slow down brute-force attempts.                                                                                            |
| `TRUSTED_PROXIES`              | _(empty)_                   | IP/CIDR of trusted reverse proxies, comma-separated (e.g. `172.16.0.0/12`). Required for the `X-Forwarded-For`/`X-Forwarded-Proto` headers to be taken into account — see the box below. |

!!! danger "TRUSTED_PROXIES behind a reverse proxy"
Without this variable set, two side effects appear behind a TLS reverse proxy:

    - the session cookie is not marked `Secure` (the TLS proxy is not detected);
    - rate limiting groups **all** clients under the proxy's IP, which can block everyone after a few requests.

## API / Application

| Variable               | Default       | Description                                                                  |
| ---------------------- | ------------- | ---------------------------------------------------------------------------- |
| `LOG_LEVEL`            | `INFO`        | Log level (`DEBUG`, `INFO`, `WARNING`…).                                     |
| `APP_VERSION`          | `Development` | Version displayed by the application.                                        |
| `SWAGGER_ENABLED`      | `false`       | Exposes `/api/docs` (self-hosted Swagger UI) and `/api/openapi.json`.        |
| `API_KEYS_ENABLED`     | `true`        | Enables creating Personal Access Tokens (PAT) from the user profile.         |
| `AUDIT_MAX_EVENTS`     | `10000`       | Max number of events kept in the audit log (oldest ones purged beyond this). |
| `AUDIT_RETENTION_DAYS` | `90`          | Audit log retention duration, in days.                                       |

## Database

| Variable   | Default                                                     | Description                                                                                                                                                             |
| ---------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DB_PATH`  | `sqlite+aiosqlite:////var/lib/wireguard-ui/wireguard_ui.db` | Async SQLAlchemy connection URL. Also accepts a raw path, a `sqlite:///` URL, or `postgres://`/`postgresql://` (automatically converted to the async `asyncpg` driver). |
| `DATA_DIR` | `/var/lib/wireguard-ui`                                     | Application data directory (default DB, generated secret key).                                                                                                          |

## WireGuard

| Variable              | Default | Description                                                                                                                                 |
| --------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `WIREGUARD_AUTOSTART` | `true`  | Automatically starts the WireGuard service when the application launches (see [lifespan](../architecture/backend.md#4-lifecycle-lifespan)). |

## Email

| Variable    | Default          | Description                             |
| ----------- | ---------------- | --------------------------------------- |
| `MAIL_FROM` | `no-reply@wg.ui` | Sender address of configuration emails. |
| `MAIL_NAME` | `WireGuardUI`    | Name displayed as sender.               |

> Other SMTP settings (server, port, credentials, TLS/SSL) are configured from the admin interface (_SMTP_ page), not via the environment — see [`services/smtp.py`](../fonctions/services.md#smtppy-settingspy).

## System settings (Docker host)

These `sysctl` are not application variables but must be enabled on the container for WireGuard to work:

| Sysctl                               | Role                                                              |
| ------------------------------------ | ----------------------------------------------------------------- |
| `net.ipv4.ip_forward=1`              | Required to relay (route) peer traffic to the main interface.     |
| `net.ipv4.conf.all.src_valid_mark=1` | Required for source validation after packet marking by WireGuard. |
