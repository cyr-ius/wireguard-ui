"""Application settings loaded from environment using pydantic-settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:////data/wireguard_ui.db"
GITHUB_REPOSITORY = "cyr-ius/wireguard-ui"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    db_path: str = Field(default=DEFAULT_DATABASE_URL, validation_alias="DB_PATH")
    db_echo: bool = Field(default=False, validation_alias="DB_ECHO")
    secret_key: str = Field(
        default="CHANGE_ME_use_a_long_random_secret_in_production",
        validation_alias="SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, ge=1, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    bcrypt_rounds: int = Field(default=12, ge=4, validation_alias="BCRYPT_ROUNDS")
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_email: str = Field(default="admin@wg.ui", validation_alias="ADMIN_EMAIL")
    admin_password: str = Field(default="admin", validation_alias="ADMIN_PASSWORD")
    mail_from: str = Field(default="no-reply@wg.ui", validation_alias="MAIL_FROM")
    mail_name: str = Field(default="WireGuardUI", validation_alias="MAIL_NAME")
    wg_autostart: bool = Field(default=True, validation_alias="WIREGUARD_AUTOSTART")
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


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


app_settings = get_settings()
