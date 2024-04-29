"""Wireguard Apis."""

from flask import Blueprint, request
from flask_restx import Api
from flask_security import current_user

from ..config import SECURITY_TOKEN_AUTHENTICATION_HEADER

bp = Blueprint("api", __name__)
authorizations = {
    "Bearer": {
        "type": "apiKey",
        "in": "header",
        "name": SECURITY_TOKEN_AUTHENTICATION_HEADER,
    }
}
api = Api(
    app=bp,
    title="Wireguard API",
    version="1.0",
    description="API for Wireguard",
    doc="/doc",
    authorizations=authorizations,
    security="Bearer",
)


@bp.before_request
def add_security_header_token():
    """Add X-API-KEY header."""
    sec_token_hdr = SECURITY_TOKEN_AUTHENTICATION_HEADER.replace("-", "_")
    if (
        current_user.is_authenticated
        and request.headers.get(SECURITY_TOKEN_AUTHENTICATION_HEADER) is None
    ):
        request.environ[f"HTTP_{sec_token_hdr}"] = current_user.get_auth_token()
