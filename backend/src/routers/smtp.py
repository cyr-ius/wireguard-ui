"""SMTP/Mail server configuration router — admin only.

Provides endpoints to configure and test email server settings
used for sending WireGuard client configurations.
"""

from __future__ import annotations

import logging
from typing import cast

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
    NameEmail,
)
from pydantic import SecretStr
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import GlobalSettings, User
from ..schemas import SmtpSettingsResponse, SmtpSettingsUpdate, SmtpTestRequest

logger = logging.getLogger(__name__)

router = APIRouter()

SMTP_DEFAULTS = {
    "smtp_server": None,
    "smtp_port": None,
    "smtp_username": None,
    "smtp_password": None,
    "smtp_from": None,
    "smtp_from_name": "WireGuard UI",
    "smtp_tls": True,
    "smtp_ssl": False,
    "smtp_verify": True,
    "default_email_language": "en",
}


def _build_smtp_response(settings: GlobalSettings) -> SmtpSettingsResponse:
    """Build a SmtpSettingsResponse from a GlobalSettings object.

    Password is intentionally omitted from the response for security.

    Args:
        settings: The global settings ORM object.

    Returns:
        SmtpSettingsResponse: The response DTO.
    """
    return SmtpSettingsResponse(
        smtp_server=settings.smtp_server,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_from=settings.smtp_from,
        smtp_from_name=settings.smtp_from_name,
        smtp_tls=settings.smtp_tls,
        smtp_ssl=settings.smtp_ssl,
        smtp_verify=settings.smtp_verify,
        default_email_language=settings.default_email_language or "en",
        smtp_configured=bool(settings.smtp_server and settings.smtp_port),
    )


def _resolve_mail_from(settings: GlobalSettings) -> str:
    """Return a valid sender email or raise a clear configuration error."""
    for candidate in (settings.smtp_from, settings.smtp_username):
        if not candidate:
            continue
        try:
            validate_email(candidate, check_deliverability=False)
            return candidate
        except EmailNotValidError:
            continue

    raise HTTPException(
        400,
        detail=(
            "Mail From must be a valid email address, or SMTP Username must be a valid email address."
        ),
    )


async def _get_settings(db: AsyncSession) -> GlobalSettings:
    """Retrieve existing settings or create a default row if none exists.

    Args:
        db: The async database session.

    Returns:
        GlobalSettings: The settings ORM object.
    """
    settings = (await db.exec(select(GlobalSettings))).one()
    return settings


@router.get("", response_model=SmtpSettingsResponse)
async def get_smtp_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Retrieve the current SMTP/email server configuration.

    Password is not included in the response.
    """
    settings = await _get_settings(db)
    return _build_smtp_response(settings)


@router.put("", response_model=SmtpSettingsResponse)
async def update_smtp_settings(
    payload: SmtpSettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Update the SMTP/email server configuration.

    If smtp_password is not provided (None), the existing password is preserved.

    Args:
        payload: The SMTP settings to update.
    """
    settings = await _get_settings(db)

    update_data = payload.model_dump(exclude_unset=True)

    # Preserve existing password if not explicitly provided or blank
    password = update_data.get("smtp_password")
    if (
        "smtp_password" not in update_data
        or password is None
        or (isinstance(password, str) and not password.strip())
    ):
        update_data.pop("smtp_password", None)

    settings.sqlmodel_update(update_data)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    logger.info(
        "SMTP settings updated: server=%s, port=%s",
        settings.smtp_server,
        settings.smtp_port,
    )

    return _build_smtp_response(settings)


@router.post("/reset", response_model=SmtpSettingsResponse)
async def reset_smtp_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Reset all mail-related settings to their defaults."""
    settings = await _get_settings(db)
    settings.sqlmodel_update(SMTP_DEFAULTS)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return _build_smtp_response(settings)


@router.post("/test", status_code=204)
async def test_smtp_settings(
    body: SmtpTestRequest,
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Send a test email to verify SMTP configuration.

    Args:
        body: Contains the recipient email address for the test.
    """
    settings = (await db.exec(select(GlobalSettings))).one_or_none()

    if not settings or not settings.smtp_server or not settings.smtp_port:
        raise HTTPException(
            400, detail="SMTP is not configured. Please save SMTP settings first."
        )

    try:
        email_config = ConnectionConfig(
            MAIL_USERNAME=settings.smtp_username or "",
            MAIL_PASSWORD=SecretStr(settings.smtp_password or ""),
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_server,
            MAIL_STARTTLS=settings.smtp_tls,
            MAIL_SSL_TLS=settings.smtp_ssl,
            USE_CREDENTIALS=bool(settings.smtp_username),
            VALIDATE_CERTS=settings.smtp_verify,
            MAIL_FROM=_resolve_mail_from(settings),
            MAIL_FROM_NAME=settings.smtp_from_name or "WireGuard UI",
        )

        message = MessageSchema(
            subject="WireGuard UI — SMTP Test Email",
            recipients=cast(list[NameEmail], [str(body.recipient)]),
            body=(
                "<h2>✅ SMTP Configuration Test</h2>"
                "<p>Your SMTP settings are correctly configured.</p>"
                "<p>This test email was sent by <strong>WireGuard UI</strong>.</p>"
            ),
            subtype=MessageType.html,
        )

        fm = FastMail(email_config)
        background_tasks.add_task(fm.send_message, message)

        logger.info("SMTP test email scheduled to %s", body.recipient)

    except Exception as exc:
        logger.error("SMTP test failed: %s", exc)
        raise HTTPException(500, detail=f"SMTP test failed: {exc!s}")
