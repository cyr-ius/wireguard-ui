"""
Email service for sending WireGuard client configurations.
Supports multilingual templates (en, fr, es) with QR code and config file attachment.
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Literal, cast

import qrcode
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

from ..models import GlobalSettings, WireGuardClient, WireGuardServer

logger = logging.getLogger(__name__)

# Path to email templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Supported language codes for email templates
SupportedLanguage = Literal["en", "fr", "es"]


def _generate_qr_code_base64(config_content: str) -> str:
    """Generate a QR code from WireGuard config content and return it as base64 PNG.

    Args:
        config_content: The WireGuard configuration file content.

    Returns:
        str: Base64-encoded PNG image of the QR code.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=6,
        border=4,
    )
    qr.add_data(config_content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


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

    raise ValueError(
        "Mail From must be a valid email address, or SMTP Username must be a valid email address."
    )


def _render_email_template(
    language: SupportedLanguage,
    client: WireGuardClient,
    qr_code_base64: str,
    settings: GlobalSettings,
) -> str:
    """Render the HTML email template for a given language.

    Args:
        language: Language code (en, fr, es).
        client: The WireGuard client whose config is being sent.
        qr_code_base64: Base64-encoded QR code image.
        settings: Global application settings (used for DNS, etc.).

    Returns:
        str: Rendered HTML content.
    """
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
        dns_servers=settings.dns_servers if client.use_server_dns else None,
        qr_code_base64=qr_code_base64,
    )


async def send_client_config_email(
    client: WireGuardClient,
    server: WireGuardServer,
    settings: GlobalSettings,
    config_content: str,
    language: SupportedLanguage = "en",
) -> None:
    """Send a WireGuard configuration email to the client.

    Sends an HTML email with:
    - Client configuration details
    - Inline QR code image
    - Attached .conf file

    Args:
        client: The WireGuard client to send configuration to.
        server: The WireGuard server (used for context).
        settings: Global application settings (SMTP config, DNS, etc.).
        config_content: The WireGuard configuration file content string.
        language: Language code for the email template (en, fr, es).

    Raises:
        ValueError: If SMTP is not configured in settings.
        Exception: If the email sending fails.
    """
    if not settings.smtp_server or not settings.smtp_port:
        raise ValueError("SMTP server is not configured in global settings.")

    # Generate QR code from config content
    qr_code_base64 = _generate_qr_code_base64(config_content)

    # Render HTML template
    html_content = _render_email_template(language, client, qr_code_base64, settings)

    # Subject lines per language
    subjects: dict[SupportedLanguage, str] = {
        "en": f"Your WireGuard VPN Configuration — {client.name}",
        "fr": f"Votre configuration VPN WireGuard — {client.name}",
        "es": f"Su configuración VPN WireGuard — {client.name}",
    }
    subject = subjects.get(language, subjects["en"])

    # Build SMTP connection config from global settings
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
