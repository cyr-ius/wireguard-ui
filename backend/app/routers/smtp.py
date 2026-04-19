"""SMTP/Mail server configuration router — admin only.

Provides endpoints to configure and test email server settings
used for sending WireGuard client configurations.
"""

from __future__ import annotations

import logging
from typing import cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
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
from ..schemas import Lang, SmtpSettingsResponse, SmtpSettingsUpdate, SmtpTestRequest
from ..services.email import _resolve_mail_from

logger = logging.getLogger(__name__)
default_lang: Lang = "en"
router = APIRouter()

SMTP_DEFAULTS = {
    "smtp_server": None,
    "smtp_port": None,
    "smtp_username": None,
    "smtp_password": None,
    "smtp_from": "no-reply@wg.ui",
    "smtp_from_name": "WireGuard UI",
    "smtp_tls": True,
    "smtp_ssl": False,
    "smtp_verify": True,
    "default_email_language": "en",
}


def _build_smtp_response(settings: GlobalSettings) -> SmtpSettingsResponse:
    """Map GlobalSettings to SmtpSettingsResponse, omitting the password."""
    return SmtpSettingsResponse(
        smtp_server=settings.smtp_server,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_from=settings.smtp_from,
        smtp_from_name=settings.smtp_from_name,
        smtp_tls=settings.smtp_tls,
        smtp_ssl=settings.smtp_ssl,
        smtp_verify=settings.smtp_verify,
        default_email_language=settings.default_email_language or default_lang,
        smtp_configured=bool(settings.smtp_server and settings.smtp_port),
    )


async def _get_settings(db: AsyncSession) -> GlobalSettings:
    """Return existing GlobalSettings or create a default row."""
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None:
        settings = GlobalSettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("", response_model=SmtpSettingsResponse)
async def get_smtp_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Return current SMTP configuration (password excluded)."""
    settings = await _get_settings(db)
    return _build_smtp_response(settings)


@router.put("", response_model=SmtpSettingsResponse)
async def update_smtp_settings(
    payload: SmtpSettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Update SMTP settings, preserving the password if not provided."""
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


@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_smtp_settings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Reset all mail-related settings to their defaults."""
    settings = await _get_settings(db)
    settings.sqlmodel_update(SMTP_DEFAULTS)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)


@router.post("/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_smtp_settings(
    body: SmtpTestRequest,
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Schedule a test email to verify the current SMTP configuration."""
    settings = (await db.exec(select(GlobalSettings))).one_or_none()

    if not settings or not settings.smtp_server or not settings.smtp_port:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="SMTP is not configured. Please save SMTP settings first.",
        )

    try:
        try:
            mail_from = _resolve_mail_from(settings)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        email_config = ConnectionConfig(
            MAIL_USERNAME=settings.smtp_username or "",
            MAIL_PASSWORD=SecretStr(settings.smtp_password or ""),
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_server,
            MAIL_STARTTLS=settings.smtp_tls,
            MAIL_SSL_TLS=settings.smtp_ssl,
            USE_CREDENTIALS=bool(settings.smtp_username),
            VALIDATE_CERTS=settings.smtp_verify,
            MAIL_FROM=mail_from,
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
        logger.exception("SMTP test failed: %s", exc)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP test failed due to an internal error. Check server logs.",
        )
