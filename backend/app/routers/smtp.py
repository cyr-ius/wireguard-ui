"""SMTP/Mail server configuration router — admin only."""

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
from ..models import SmtpSettings, User
from ..schemas import Lang, SmtpSettingsResponse, SmtpSettingsUpdate, SmtpTestRequest
from ..services.email import _resolve_mail_from

logger = logging.getLogger(__name__)
default_lang: Lang = "en"
router = APIRouter()

SMTP_DEFAULTS = {
    "server": None,
    "port": None,
    "username": None,
    "password": None,
    "from_address": "no-reply@wg.ui",
    "from_name": "WireGuard UI",
    "tls": True,
    "ssl": False,
    "verify": True,
    "default_language": "en",
}


def _build_smtp_response(smtp: SmtpSettings) -> SmtpSettingsResponse:
    """Map SmtpSettings to SmtpSettingsResponse, omitting the password."""
    return SmtpSettingsResponse(
        smtp_server=smtp.server,
        smtp_port=smtp.port,
        smtp_username=smtp.username,
        smtp_from=smtp.from_address,
        smtp_from_name=smtp.from_name,
        smtp_tls=smtp.tls,
        smtp_ssl=smtp.ssl,
        smtp_verify=smtp.verify,
        default_email_language=smtp.default_language or default_lang,
        smtp_configured=bool(smtp.server and smtp.port),
    )


async def _get_smtp_settings(db: AsyncSession) -> SmtpSettings:
    """Return existing SmtpSettings or create a default row."""
    smtp = (await db.exec(select(SmtpSettings))).one_or_none()
    if smtp is None:
        smtp = SmtpSettings()
        db.add(smtp)
        await db.commit()
        await db.refresh(smtp)
    return smtp


@router.get("", response_model=SmtpSettingsResponse)
async def get_smtp_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Return current SMTP configuration (password excluded)."""
    return _build_smtp_response(await _get_smtp_settings(db))


@router.put("", response_model=SmtpSettingsResponse)
async def update_smtp_settings(
    payload: SmtpSettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Update SMTP settings, preserving the password if not provided."""
    smtp = await _get_smtp_settings(db)

    update_data = {
        "server": payload.smtp_server,
        "port": payload.smtp_port,
        "username": payload.smtp_username,
        "from_address": payload.smtp_from,
        "from_name": payload.smtp_from_name,
        "tls": payload.smtp_tls,
        "ssl": payload.smtp_ssl,
        "verify": payload.smtp_verify,
        "default_language": payload.default_email_language,
    }
    # Remove keys not explicitly set by the caller
    for key in list(update_data):
        field = (
            f"smtp_{key}"
            if key not in ("from_address", "from_name", "default_language")
            else key
        )
        if key == "from_address":
            field = "smtp_from"
        elif key == "from_name":
            field = "smtp_from_name"
        elif key == "default_language":
            field = "default_email_language"
        if field not in payload.model_fields_set:
            del update_data[key]

    # Preserve existing password if not explicitly provided or blank
    password = payload.smtp_password
    if (
        "smtp_password" not in payload.model_fields_set
        or password is None
        or (isinstance(password, str) and not password.strip())
    ):
        pass  # do not touch existing password
    else:
        update_data["password"] = password

    smtp.sqlmodel_update(update_data)
    db.add(smtp)
    await db.commit()
    await db.refresh(smtp)

    logger.info("SMTP settings updated: server=%s, port=%s", smtp.server, smtp.port)

    return _build_smtp_response(smtp)


@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_smtp_settings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Reset all mail-related settings to their defaults."""
    smtp = await _get_smtp_settings(db)
    smtp.sqlmodel_update(SMTP_DEFAULTS)
    db.add(smtp)
    await db.commit()
    await db.refresh(smtp)


@router.post("/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_smtp_settings(
    body: SmtpTestRequest,
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Schedule a test email to verify the current SMTP configuration."""
    smtp = (await db.exec(select(SmtpSettings))).one_or_none()

    if not smtp or not smtp.server or not smtp.port:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="SMTP is not configured. Please save SMTP settings first.",
        )

    try:
        try:
            mail_from = _resolve_mail_from(smtp)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        email_config = ConnectionConfig(
            MAIL_USERNAME=smtp.username or "",
            MAIL_PASSWORD=SecretStr(smtp.password or ""),
            MAIL_PORT=smtp.port,
            MAIL_SERVER=smtp.server,
            MAIL_STARTTLS=smtp.tls,
            MAIL_SSL_TLS=smtp.ssl,
            USE_CREDENTIALS=bool(smtp.username),
            VALIDATE_CERTS=smtp.verify,
            MAIL_FROM=mail_from,
            MAIL_FROM_NAME=smtp.from_name or "WireGuard UI",
        )

        message = MessageSchema(
            subject="WireGuard UI — SMTP Test Email",
            recipients=cast(list[NameEmail], [str(body.recipient)]),
            body=(
                "<h2>SMTP Configuration Test</h2>"
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
