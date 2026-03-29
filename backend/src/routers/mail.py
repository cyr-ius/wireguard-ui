from __future__ import annotations

import logging
import traceback

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
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
from ..config import app_settings
from ..database import get_db
from ..models import GlobalSettings, User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/send", status_code=204)
async def send_mail(
    tasks: BackgroundTasks,
    *,
    subject: str,
    recipients: list[NameEmail],
    body: str,
    attachments: list[UploadFile] | dict | str | None = None,
    type: MessageType = MessageType.html,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None or settings.smtp_server is None or settings.smtp_port is None:
        raise HTTPException(404, "SMTP Server not found")

    try:
        email_config = ConnectionConfig(
            MAIL_USERNAME=settings.smtp_username or "",
            MAIL_PASSWORD=SecretStr(settings.smtp_password or ""),
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_server,
            MAIL_STARTTLS=settings.smtp_tls,
            MAIL_SSL_TLS=settings.smtp_ssl,
            USE_CREDENTIALS=settings.smtp_username is not None,
            VALIDATE_CERTS=settings.smtp_verify,
            MAIL_FROM=app_settings.mail_from,
            MAIL_FROM_NAME=app_settings.mail_name,
        )
        fm = FastMail(email_config)

        msg = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=type,
            attachments=attachments,
        )

        tasks.add_task(fm.send_message, msg)

    except Exception as e:
        logger.error(f"Cannot send account verification email. Error: {e}")
        logger.debug(traceback.format_exc())
