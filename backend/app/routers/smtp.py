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
from ..schemas import SmtpSettingsResponse, SmtpSettingsUpdate, SmtpTestRequest
from ..services.email import _resolve_mail_from
from ..services.smtp import (
    SMTP_DEFAULTS,
    build_smtp_response,
    build_smtp_update_dict,
    get_or_create_smtp_settings,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=SmtpSettingsResponse)
async def get_smtp_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Return current SMTP configuration (password excluded)."""
    return build_smtp_response(await get_or_create_smtp_settings(db))


@router.put("", response_model=SmtpSettingsResponse)
async def update_smtp_settings(
    payload: SmtpSettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Update SMTP settings, preserving the password if not provided."""
    smtp = await get_or_create_smtp_settings(db)
    smtp.sqlmodel_update(build_smtp_update_dict(payload))
    db.add(smtp)
    await db.commit()
    await db.refresh(smtp)
    logger.info("SMTP settings updated: server=%s, port=%s", smtp.server, smtp.port)
    return build_smtp_response(smtp)


@router.delete("/reset", response_model=SmtpSettingsResponse)
async def reset_smtp_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsResponse:
    """Reset all mail-related settings to their defaults."""
    smtp = await get_or_create_smtp_settings(db)
    smtp.sqlmodel_update(SMTP_DEFAULTS)
    db.add(smtp)
    await db.commit()
    await db.refresh(smtp)
    return build_smtp_response(smtp)


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
