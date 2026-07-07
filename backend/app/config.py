"""Application settings loaded from environment using pydantic-settings."""

import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

DATA_DIR = os.getenv("DATA_DIR", "/var/lib/wireguard-ui")
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/wireguard_ui.db"
CONFIG_FILE = "/etc/wireguard/wg0.conf"
GITHUB_REPOSITORY = "cyr-ius/wireguard-ui"

DEFAULT_SECRET_KEY = "CHANGE_ME_use_a_long_random_secret_in_production"
SECRET_KEY_FILE = "secret_key"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    db_path: str = Field(default=DEFAULT_DATABASE_URL, validation_alias="DB_PATH")
    db_echo: bool = Field(default=False, validation_alias="DB_ECHO")
    secret_key: str = Field(
        default=DEFAULT_SECRET_KEY,
        validation_alias="SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, ge=1, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    bcrypt_rounds: int = Field(default=12, ge=4, validation_alias="BCRYPT_ROUNDS")
    login_rate_limit_max: int = Field(
        default=10, ge=1, validation_alias="LOGIN_RATE_LIMIT_MAX"
    )
    login_rate_limit_window: int = Field(
        default=60, ge=1, validation_alias="LOGIN_RATE_LIMIT_WINDOW"
    )
    # Comma-separated IPs/CIDRs of reverse proxies whose X-Forwarded-* headers
    # are trusted. Empty (default) → forwarded headers are ignored, only the
    # socket peer / real scheme are used.
    trusted_proxies: str = Field(default="", validation_alias="TRUSTED_PROXIES")
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_email: str = Field(default="admin@wg.ui", validation_alias="ADMIN_EMAIL")
    mail_from: str = Field(default="no-reply@wg.ui", validation_alias="MAIL_FROM")
    mail_name: str = Field(default="WireGuardUI", validation_alias="MAIL_NAME")
    wg_autostart: bool = Field(default=True, validation_alias="WIREGUARD_AUTOSTART")
    swagger_enabled: bool = Field(default=True, validation_alias="SWAGGER_ENABLED")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    app_version: str = Field(default="Development", validation_alias="APP_VERSION")

    @field_validator("db_path", mode="before")
    @classmethod
    def normalize_db_path(cls, value: object) -> str:
        if value is None:
            return DEFAULT_DATABASE_URL

        raw = str(value).strip().strip('"').strip("'")
        if not raw or raw.startswith("${"):
            return DEFAULT_DATABASE_URL

        if "://" not in raw:
            # Treat plain path values as sqlite db file paths.
            if raw.startswith("/"):
                return f"sqlite+aiosqlite:///{raw}"
            return f"sqlite+aiosqlite:///./{raw}"

        if raw.startswith("sqlite:///"):
            return raw.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        if raw.startswith("postgres://"):
            return raw.replace("postgres://", "postgresql+asyncpg://", 1)

        if raw.startswith("postgresql://") and not raw.startswith(
            "postgresql+asyncpg://"
        ):
            return raw.replace("postgresql://", "postgresql+asyncpg://", 1)

        return raw


def _resolve_secret_key(settings: AppSettings) -> str:
    """Return a stable secret key, generating one on first run if none is provided.

    When SECRET_KEY is set explicitly via the environment it is used as-is.
    Otherwise a random key is read from (or written to) ``DATA_DIR/secret_key``
    so JWT sessions stay valid across restarts without shipping a known default.
    """
    provided = settings.secret_key.strip()
    if provided and provided != DEFAULT_SECRET_KEY:
        return provided

    key_file = Path(DATA_DIR) / SECRET_KEY_FILE
    try:
        if key_file.is_file():
            existing = key_file.read_text(encoding="utf-8").strip()
            if existing:
                return existing
    except OSError as exc:
        logger.warning("Could not read secret key file %s: %s", key_file, exc)

    generated = secrets.token_urlsafe(64)
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(generated, encoding="utf-8")
        key_file.chmod(0o600)
        logger.warning(
            "No SECRET_KEY provided; generated a new random key and stored it at %s. "
            "Set SECRET_KEY explicitly to share sessions across replicas.",
            key_file,
        )
    except OSError as exc:
        logger.error(
            "Could not persist generated secret key to %s (%s); using an in-memory "
            "key. All tokens will be invalidated on restart.",
            key_file,
            exc,
        )
    return generated


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.secret_key = _resolve_secret_key(settings)
    return settings


app_settings = get_settings()
