"""QR code helpers shared across routers and services."""

from __future__ import annotations

import base64
import io

import qrcode


def generate_qr_code_base64(content: str) -> str:
    """Generate a QR code image and return it as base64-encoded PNG."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=6,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode("utf-8")
