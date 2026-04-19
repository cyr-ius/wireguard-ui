"""OIDC business logic: discovery, token exchange, user provisioning."""

from __future__ import annotations

import base64
import uuid
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import hash_password
from ..models import GlobalSettings, Role, User
from ..schemas import OidcSettingsResponse

AUTH_SOURCE_LOCAL = "local"
AUTH_SOURCE_OIDC = "oidc"

OIDC_DEFAULT: dict[str, Any] = {
    "oidc_enabled": False,
    "oidc_only": False,
    "oidc_issuer": None,
    "oidc_client_id": None,
    "oidc_client_secret": None,
    "oidc_redirect_uri": None,
    "oidc_post_logout_redirect_uri": None,
    "oidc_response_type": "code",
    "oidc_scope": "openid profile email",
}


def get_bool_attr(obj: object, name: str, default: bool = False) -> bool:
    """Return a boolean attribute from obj with fallback default."""
    return bool(getattr(obj, name, default))


def get_str_attr(obj: object, name: str, default: str = "") -> str:
    """Return a string attribute from obj with fallback default."""
    value = getattr(obj, name, default)
    return value if isinstance(value, str) else default


def _normalize_issuer(issuer: str) -> str:
    """Strip trailing slash from issuer URL."""
    return issuer.rstrip("/")


def discovery_url(issuer: str) -> str:
    """Return the OIDC discovery document URL for the given issuer."""
    return f"{_normalize_issuer(issuer)}/.well-known/openid-configuration"


def build_token_request(
    discovery: dict[str, Any], settings: GlobalSettings, code: str
) -> tuple[dict[str, str], dict[str, str]]:
    """Build token endpoint form data and headers for authorization code exchange."""
    client_id = get_str_attr(settings, "oidc_client_id").strip()
    client_secret = get_str_attr(settings, "oidc_client_secret")
    redirect_uri = get_str_attr(settings, "oidc_redirect_uri")

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC client ID is not configured.",
        )

    token_data: dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers: dict[str, str] = {}

    supported_methods_raw = discovery.get("token_endpoint_auth_methods_supported")
    supported_methods = (
        [str(m) for m in supported_methods_raw if isinstance(m, str)]
        if isinstance(supported_methods_raw, list)
        else []
    )
    if not supported_methods:
        supported_methods = ["client_secret_basic"]

    if client_secret and "client_secret_basic" in supported_methods:
        credentials = f"{client_id}:{client_secret}".encode()
        headers["Authorization"] = (
            f"Basic {base64.b64encode(credentials).decode('ascii')}"
        )
        token_data["client_id"] = client_id
    elif client_secret and "client_secret_post" in supported_methods:
        token_data["client_id"] = client_id
        token_data["client_secret"] = client_secret
    elif "none" in supported_methods:
        token_data["client_id"] = client_id
    else:
        allowed = ", ".join(supported_methods) or "none"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "OIDC provider and configured client credentials are incompatible. "
                f"Supported token endpoint auth methods: {allowed}."
            ),
        )

    return token_data, headers


def safe_username(claims: dict[str, Any]) -> str:
    """Extract a usable username from OIDC claims, raise 400 if none found."""
    for value in [
        claims.get("preferred_username"),
        claims.get("username"),
        claims.get("email"),
        claims.get("sub"),
    ]:
        if not isinstance(value, str):
            continue
        username = value.strip()
        if not username:
            continue
        if "@" in username:
            username = username.split("@", 1)[0]
        username = username[:255]
        if username:
            return username

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OIDC provider did not return a usable username.",
    )


def safe_email(claims: dict[str, Any], username: str) -> str:
    """Return email from claims or a generated fallback local address."""
    email = claims.get("email")
    if isinstance(email, str) and email.strip():
        return email.strip()[:255]
    return f"{username}@oidc.local"


def get_name_claim(claims: dict[str, Any], name: str) -> str | None:
    """Return a truncated string claim value, or None if absent or empty."""
    value = claims.get(name)
    if isinstance(value, str):
        value = value.strip()
        return value[:255] if value else None
    return None


def to_oidc_response(settings: GlobalSettings) -> OidcSettingsResponse:
    """Map GlobalSettings OIDC fields to OidcSettingsResponse."""
    return OidcSettingsResponse(
        enabled=get_bool_attr(settings, "oidc_enabled", False),
        oidc_only=get_bool_attr(settings, "oidc_only", False),
        issuer=get_str_attr(settings, "oidc_issuer", ""),
        client_id=get_str_attr(settings, "oidc_client_id", ""),
        client_secret=get_str_attr(settings, "oidc_client_secret", ""),
        redirect_uri=get_str_attr(settings, "oidc_redirect_uri", ""),
        post_logout_redirect_uri=get_str_attr(
            settings, "oidc_post_logout_redirect_uri", ""
        ),
        response_type=get_str_attr(settings, "oidc_response_type", "code"),
        scope=get_str_attr(settings, "oidc_scope", "openid profile email"),
    )


async def fetch_json(
    url: str,
    method: str = "GET",
    data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Execute an async HTTP request and return the parsed JSON dict."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(
                method, url, data=data, headers=headers or {}
            )
            response.raise_for_status()
            parsed = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail or f"OIDC provider returned HTTP {exc.response.status_code}.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OIDC provider is unreachable: {exc}",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OIDC provider returned an unexpected payload.",
        )
    return parsed


async def fetch_discovery_document(issuer: str) -> dict[str, Any]:
    """Fetch and return the OIDC provider OpenID configuration document."""
    issuer = issuer.strip()
    if not issuer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC issuer is not configured.",
        )
    return await fetch_json(discovery_url(issuer))


async def get_or_create_settings(db: AsyncSession) -> GlobalSettings:
    """Return existing GlobalSettings row, creating a default one if absent."""
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None:
        settings = GlobalSettings.model_validate(OIDC_DEFAULT)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


async def get_existing_user(db: AsyncSession, username: str, email: str) -> User | None:
    """Look up a user by username or email, eager-loading roles."""
    result = await db.exec(
        select(User)
        .where((User.username == username) | (User.email == email))
        .options(selectinload(User.roles))  # type: ignore[arg-type]
    )
    return result.first()


async def generate_unique_username(db: AsyncSession, base: str) -> str:
    """Return a unique username derived from base, appending a numeric suffix if taken."""
    candidate = base[:255] or "oidc-user"
    suffix = 1
    while True:
        if (
            await db.exec(select(User).where(User.username == candidate))
        ).one_or_none() is None:
            return candidate
        suffix += 1
        suffix_text = f"-{suffix}"
        candidate = f"{base[: 255 - len(suffix_text)]}{suffix_text}"


async def find_or_create_user(db: AsyncSession, claims: dict[str, Any]) -> User:
    """Return an existing User from OIDC claims or create a new provisioned one."""
    username = safe_username(claims)
    email = safe_email(claims, username)

    existing = await get_existing_user(db, username, email)
    if existing is not None:
        if existing.active is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled."
            )
        return existing

    user_role = (await db.exec(select(Role).where(Role.name == "user"))).one_or_none()

    created = User.model_validate(
        {
            "username": await generate_unique_username(db, username),
            "email": email,
            "first_name": get_name_claim(claims, "given_name"),
            "last_name": get_name_claim(claims, "family_name"),
            "hashed_password": hash_password(uuid.uuid4().hex),
            "auth_source": AUTH_SOURCE_OIDC,
            "active": True,
        }
    )
    created.roles = [user_role] if user_role else []
    db.add(created)
    await db.commit()
    await db.refresh(created)

    result = await db.exec(
        select(User).where(User.id == created.id).options(selectinload(User.roles))  # type: ignore[arg-type]
    )
    return result.one()


async def exchange_code(db: AsyncSession, code: str) -> User:
    """Full OIDC authorization code flow: return the authenticated User."""
    settings = await get_or_create_settings(db)
    if not settings.oidc_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC authentication is disabled.",
        )

    discovery = await fetch_discovery_document(get_str_attr(settings, "oidc_issuer"))
    token_endpoint = str(discovery.get("token_endpoint", "")).strip()
    if not token_endpoint:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OIDC discovery document does not include a token endpoint.",
        )

    token_data, token_headers = build_token_request(discovery, settings, code)
    token_response = await fetch_json(
        token_endpoint, method="POST", data=token_data, headers=token_headers
    )

    claims: dict[str, Any] = {}
    userinfo_endpoint = str(discovery.get("userinfo_endpoint", "")).strip()
    access_token = str(token_response.get("access_token", "")).strip()
    if userinfo_endpoint and access_token:
        claims = await fetch_json(
            userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"}
        )
    elif isinstance(token_response.get("id_token"), str):
        claims = jwt.get_unverified_claims(token_response["id_token"])

    if not claims:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OIDC provider did not return usable identity claims.",
        )

    return await find_or_create_user(db, claims)
