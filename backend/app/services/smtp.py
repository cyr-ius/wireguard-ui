"""SMTP settings CRUD helpers."""

from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import SmtpSettings
from ..schemas import SmtpSettingsResponse, SmtpSettingsUpdate

SMTP_DEFAULTS: dict = {
    "server": None,
    "port": 587,
    "username": None,
    "password": None,
    "from_address": "no-reply@wg.ui",
    "from_name": "WireGuard UI",
    "tls": True,
    "ssl": False,
    "verify": True,
    "default_language": "en",
}

# Schema field name → model field name
_PAYLOAD_TO_MODEL: dict[str, str] = {
    "smtp_server": "server",
    "smtp_port": "port",
    "smtp_username": "username",
    "smtp_from": "from_address",
    "smtp_from_name": "from_name",
    "smtp_tls": "tls",
    "smtp_ssl": "ssl",
    "smtp_verify": "verify",
    "default_email_language": "default_language",
}


async def get_or_create_smtp_settings(db: AsyncSession) -> SmtpSettings:
    """Return the single SmtpSettings row, creating it with defaults if absent."""
    smtp = (await db.exec(select(SmtpSettings))).one_or_none()
    if smtp is None:
        smtp = SmtpSettings()
        db.add(smtp)
        await db.commit()
        await db.refresh(smtp)
    return smtp


def build_smtp_response(smtp: SmtpSettings) -> SmtpSettingsResponse:
    """Map SmtpSettings to SmtpSettingsResponse (password excluded)."""
    return SmtpSettingsResponse(
        smtp_server=smtp.server,
        smtp_port=smtp.port,
        smtp_username=smtp.username,
        smtp_from=smtp.from_address,
        smtp_from_name=smtp.from_name,
        smtp_tls=smtp.tls,
        smtp_ssl=smtp.ssl,
        smtp_verify=smtp.verify,
        default_email_language=smtp.default_language or "en",
        smtp_configured=bool(smtp.server and smtp.port),
    )


def build_smtp_update_dict(payload: SmtpSettingsUpdate) -> dict:
    """Return model-field dict for only the fields explicitly set in the payload.

    Password is included only when non-blank and explicitly provided.
    """
    update: dict = {
        model_key: getattr(payload, schema_key)
        for schema_key, model_key in _PAYLOAD_TO_MODEL.items()
        if schema_key in payload.model_fields_set
    }
    if (
        "smtp_password" in payload.model_fields_set
        and payload.smtp_password
        and isinstance(payload.smtp_password, str)
        and payload.smtp_password.strip()
    ):
        update["password"] = payload.smtp_password
    return update
