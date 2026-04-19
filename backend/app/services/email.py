"""
Email service for sending WireGuard client configurations.
Supports multilingual templates (en, fr, es) with QR code and config file attachment.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Literal, cast

from email_validator import EmailNotValidError, validate_email
from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
    NameEmail,
)
from jinja2 import Environment, FileSystemLoader
from pydantic import SecretStr
from starlette.datastructures import Headers, UploadFile

from ..models import GlobalSettings, SmtpSettings, WireGuardClient, WireGuardServer
from .qr import generate_qr_code_base64

logger = logging.getLogger(__name__)

# Path to email templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Supported language codes for email templates
SupportedLanguage = Literal["en", "fr", "es"]


def _resolve_mail_from(smtp: SmtpSettings) -> str:
    """Return a valid sender email or raise a clear configuration error."""
    for candidate in (smtp.from_address, smtp.username):
        if not candidate:
            continue
        try:
            validate_email(candidate, check_deliverability=False)
            return candidate
        except EmailNotValidError:
            continue

    raise ValueError(
        "Mail From must be a valid email address, or SMTP Username must be a valid email address."
    )


def _render_email_template(
    language: SupportedLanguage,
    client: WireGuardClient,
    qr_code_base64: str,
    settings: GlobalSettings,
) -> str:
    """Render the HTML email template for the given language and client."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    template_name = f"client_config_{language}.html"
    template = env.get_template(template_name)

    return template.render(
        client_name=client.name,
        allocated_ips=client.allocated_ips,
        allowed_ips=client.allowed_ips,
        dns_servers=",".join(settings.dns_servers) if client.use_server_dns else None,
        qr_code_base64=qr_code_base64,
    )


async def send_client_config_email(
    client: WireGuardClient,
    server: WireGuardServer,
    global_settings: GlobalSettings,
    smtp: SmtpSettings,
    config_content: str,
    language: SupportedLanguage = "en",
) -> None:
    """Send WireGuard config email with inline QR code and .conf attachment."""
    if not smtp.server or not smtp.port:
        raise ValueError("SMTP server is not configured.")

    # Generate QR code from config content
    qr_code_base64 = generate_qr_code_base64(config_content)

    # Render HTML template
    html_content = _render_email_template(
        language, client, qr_code_base64, global_settings
    )

    # Subject lines per language
    subjects: dict[SupportedLanguage, str] = {
        "en": f"Your WireGuard VPN Configuration — {client.name}",
        "fr": f"Votre configuration VPN WireGuard — {client.name}",
        "es": f"Su configuración VPN WireGuard — {client.name}",
    }
    subject = subjects.get(language, subjects["en"])

    email_config = ConnectionConfig(
        MAIL_USERNAME=smtp.username or "",
        MAIL_PASSWORD=SecretStr(smtp.password or ""),
        MAIL_PORT=smtp.port,
        MAIL_SERVER=smtp.server,
        MAIL_STARTTLS=smtp.tls,
        MAIL_SSL_TLS=smtp.ssl,
        USE_CREDENTIALS=bool(smtp.username),
        VALIDATE_CERTS=smtp.verify,
        MAIL_FROM=_resolve_mail_from(smtp),
        MAIL_FROM_NAME=smtp.from_name or "WireGuard UI",
    )

    # Prepare config file attachment
    conf_filename = f"{client.name}.conf"
    conf_bytes = config_content.encode("utf-8")

    attachment = UploadFile(
        filename=conf_filename,
        file=io.BytesIO(conf_bytes),
        headers=Headers({"content-type": "text/plain; charset=utf-8"}),
    )

    # Build message with attachment
    message = MessageSchema(
        subject=subject,
        recipients=cast(list[NameEmail], [client.email]),
        body=html_content,
        subtype=MessageType.html,
        attachments=[attachment],
    )

    fm = FastMail(email_config)
    await fm.send_message(message)

    logger.info(
        "Configuration email sent to %s for client '%s' (language: %s)",
        client.email,
        client.name,
        language,
    )
