"""OIDC settings and authentication helpers."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import create_access_token, get_current_admin, hash_password
from ..database import get_db
from ..models import GlobalSettings, Role, User
from ..schemas import (
    OidcPublicConfig,
    OidcSettingsResponse,
    OidcSettingsUpdate,
    TokenResponse,
    UserResponse,
)

router = APIRouter()

OIDC_DEFAULT = {
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


def _get_bool_attr(obj: object, name: str, default: bool = False) -> bool:
    return bool(getattr(obj, name, default))


def _get_str_attr(obj: object, name: str, default: str = "") -> str:
    value = getattr(obj, name, default)
    return value if isinstance(value, str) else default


def _normalize_issuer(issuer: str) -> str:
    return issuer.rstrip("/")


def _discovery_url(issuer: str) -> str:
    return f"{_normalize_issuer(issuer)}/.well-known/openid-configuration"


def _build_token_request(
    discovery: dict[str, Any], settings: GlobalSettings, code: str
) -> tuple[bytes, dict[str, str]]:
    client_id = _get_str_attr(settings, "oidc_client_id").strip()
    client_secret = _get_str_attr(settings, "oidc_client_secret")
    redirect_uri = _get_str_attr(settings, "oidc_redirect_uri")

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
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    supported_methods_raw = discovery.get("token_endpoint_auth_methods_supported")
    supported_methods = (
        [str(method) for method in supported_methods_raw if isinstance(method, str)]
        if isinstance(supported_methods_raw, list)
        else []
    )

    # RFC 8414: if omitted, the default is client_secret_basic.
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

    return urllib.parse.urlencode(token_data).encode("utf-8"), headers


def _safe_username(claims: dict[str, Any]) -> str:
    candidates = [
        claims.get("preferred_username"),
        claims.get("username"),
        claims.get("email"),
        claims.get("sub"),
    ]

    for value in candidates:
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


def _safe_email(claims: dict[str, Any], username: str) -> str:
    email = claims.get("email")
    if isinstance(email, str) and email.strip():
        return email.strip()[:255]
    return f"{username}@oidc.local"


def _get_name_claim(claims: dict[str, Any], name: str) -> str | None:
    value = claims.get(name)
    if isinstance(value, str):
        value = value.strip()
        return value[:255] if value else None
    return None


def _to_oidc_response(settings: GlobalSettings) -> OidcSettingsResponse:
    return OidcSettingsResponse(
        enabled=_get_bool_attr(settings, "oidc_enabled", False),
        oidc_only=_get_bool_attr(settings, "oidc_only", False),
        issuer=_get_str_attr(settings, "oidc_issuer", ""),
        client_id=_get_str_attr(settings, "oidc_client_id", ""),
        client_secret=_get_str_attr(settings, "oidc_client_secret", ""),
        redirect_uri=_get_str_attr(settings, "oidc_redirect_uri", ""),
        post_logout_redirect_uri=_get_str_attr(
            settings, "oidc_post_logout_redirect_uri", ""
        ),
        response_type=_get_str_attr(settings, "oidc_response_type", "code"),
        scope=_get_str_attr(settings, "oidc_scope", "openid profile email"),
    )


async def _fetch_json(
    url: str,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    def _request() -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=data,
            headers=headers or {},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore").strip()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail or f"OIDC provider returned HTTP {exc.code}.",
            ) from exc
        except urllib.error.URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OIDC provider is unreachable: {exc.reason}",
            ) from exc

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OIDC provider returned invalid JSON.",
            ) from exc

        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OIDC provider returned an unexpected payload.",
            )
        return parsed

    from asyncio import to_thread

    return await to_thread(_request)


async def _fetch_discovery_document(issuer: str) -> dict[str, Any]:
    issuer = issuer.strip()
    if not issuer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC issuer is not configured.",
        )
    return await _fetch_json(_discovery_url(issuer))


async def _get_or_create_settings(db: AsyncSession) -> GlobalSettings:
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None:
        settings = GlobalSettings.model_validate(OIDC_DEFAULT)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


async def _get_existing_user(
    db: AsyncSession, username: str, email: str
) -> User | None:
    result = await db.exec(
        select(User)
        .where((User.username == username) | (User.email == email))
        .options(selectinload(User.roles))  # type: ignore[arg-type]
    )
    return result.first()


async def _generate_unique_username(db: AsyncSession, base: str) -> str:
    candidate = base[:255] or "oidc-user"
    suffix = 1
    while True:
        exists = await db.exec(select(User).where(User.username == candidate))
        if exists.one_or_none() is None:
            return candidate
        suffix += 1
        suffix_text = f"-{suffix}"
        candidate = f"{base[: 255 - len(suffix_text)]}{suffix_text}"


async def _find_or_create_user(db: AsyncSession, claims: dict[str, Any]) -> User:
    username = _safe_username(claims)
    email = _safe_email(claims, username)

    existing = await _get_existing_user(db, username, email)
    if existing is not None:
        if existing.active is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )
        return existing

    role_result = await db.exec(select(Role).where(Role.name == "user"))
    user_role = role_result.one_or_none()

    created = User.model_validate(
        {
            "username": await _generate_unique_username(db, username),
            "email": email,
            "first_name": _get_name_claim(claims, "given_name"),
            "last_name": _get_name_claim(claims, "family_name"),
            "hashed_password": hash_password(uuid.uuid4().hex),
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
    user = result.one()
    return user


@router.get("/settings", response_model=OidcSettingsResponse)
async def get_oidc_settings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    settings = await _get_or_create_settings(db)
    return _to_oidc_response(settings)


@router.put("/settings", response_model=OidcSettingsResponse)
async def update_oidc_settings(
    payload: OidcSettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.oidc_only and not payload.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC-only mode requires OIDC authentication to be enabled.",
        )

    settings = await _get_or_create_settings(db)

    settings.sqlmodel_update(
        {
            "oidc_enabled": payload.enabled,
            "oidc_only": payload.oidc_only,
            "oidc_issuer": payload.issuer,
            "oidc_client_id": payload.client_id,
            "oidc_client_secret": payload.client_secret,
            "oidc_redirect_uri": payload.redirect_uri,
            "oidc_post_logout_redirect_uri": payload.post_logout_redirect_uri,
            "oidc_response_type": payload.response_type,
            "oidc_scope": payload.scope,
        }
    )

    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    return _to_oidc_response(settings)


@router.get("/config", response_model=OidcPublicConfig)
async def get_oidc_public_config(
    db: AsyncSession = Depends(get_db),
) -> OidcPublicConfig:
    settings = await _get_or_create_settings(db)

    authorization_endpoint = ""
    end_session_endpoint = ""

    if settings.oidc_enabled and settings.oidc_issuer:
        try:
            discovery = await _fetch_discovery_document(settings.oidc_issuer)
            authorization_endpoint = str(discovery.get("authorization_endpoint", ""))
            end_session_endpoint = str(discovery.get("end_session_endpoint", ""))
        except HTTPException:
            authorization_endpoint = ""
            end_session_endpoint = ""

    return OidcPublicConfig(
        enabled=_get_bool_attr(settings, "oidc_enabled", False),
        oidc_only=_get_bool_attr(settings, "oidc_only", False),
        issuer=_get_str_attr(settings, "oidc_issuer", ""),
        client_id=_get_str_attr(settings, "oidc_client_id", ""),
        redirect_uri=_get_str_attr(settings, "oidc_redirect_uri", ""),
        post_logout_redirect_uri=_get_str_attr(
            settings, "oidc_post_logout_redirect_uri", ""
        ),
        response_type=_get_str_attr(settings, "oidc_response_type", "code"),
        scope=_get_str_attr(settings, "oidc_scope", "openid profile email"),
        authorization_endpoint=authorization_endpoint,
        end_session_endpoint=end_session_endpoint,
    )


@router.post("/callback", response_model=TokenResponse)
async def oidc_callback(body: dict[str, str], db: AsyncSession = Depends(get_db)):
    code = (body.get("code") or "").strip()
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OIDC authorization code.",
        )

    settings = await _get_or_create_settings(db)
    if not settings.oidc_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC authentication is disabled.",
        )

    discovery = await _fetch_discovery_document(_get_str_attr(settings, "oidc_issuer"))
    token_endpoint = str(discovery.get("token_endpoint", "")).strip()
    if not token_endpoint:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OIDC discovery document does not include a token endpoint.",
        )

    token_data, token_headers = _build_token_request(discovery, settings, code)

    token_response = await _fetch_json(
        token_endpoint,
        method="POST",
        data=token_data,
        headers=token_headers,
    )

    claims: dict[str, Any] = {}
    userinfo_endpoint = str(discovery.get("userinfo_endpoint", "")).strip()
    access_token = str(token_response.get("access_token", "")).strip()
    if userinfo_endpoint and access_token:
        claims = await _fetch_json(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    elif isinstance(token_response.get("id_token"), str):
        claims = jwt.get_unverified_claims(token_response["id_token"])

    if not claims:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OIDC provider did not return usable identity claims.",
        )

    user = await _find_or_create_user(db, claims)
    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_oidc_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is not None:
        settings.sqlmodel_update(OIDC_DEFAULT)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
