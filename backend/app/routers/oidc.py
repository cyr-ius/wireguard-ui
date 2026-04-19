"""OIDC settings and authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import create_access_token, get_current_admin
from ..database import get_db
from ..models import User
from ..schemas import (
    OidcPublicConfig,
    OidcSettingsResponse,
    OidcSettingsUpdate,
    TokenResponse,
    UserResponse,
)
from ..services.oidc import (
    OIDC_DEFAULT,
    exchange_code,
    fetch_discovery_document,
    get_bool_attr,
    get_or_create_settings,
    get_str_attr,
    to_oidc_response,
)

router = APIRouter()


@router.get("/settings", response_model=OidcSettingsResponse)
async def get_oidc_settings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Return the current OIDC settings."""
    return to_oidc_response(await get_or_create_settings(db))


@router.put("/settings", response_model=OidcSettingsResponse)
async def update_oidc_settings(
    payload: OidcSettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update OIDC settings, validating OIDC-only mode requirements."""
    if payload.oidc_only and not payload.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC-only mode requires OIDC authentication to be enabled.",
        )

    settings = await get_or_create_settings(db)
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
    return to_oidc_response(settings)


@router.get("/config", response_model=OidcPublicConfig)
async def get_oidc_public_config(
    db: AsyncSession = Depends(get_db),
) -> OidcPublicConfig:
    """Return public OIDC config including authorization and logout endpoints."""
    settings = await get_or_create_settings(db)

    authorization_endpoint = ""
    end_session_endpoint = ""

    if settings.oidc_enabled and settings.oidc_issuer:
        try:
            discovery = await fetch_discovery_document(settings.oidc_issuer)
            authorization_endpoint = str(discovery.get("authorization_endpoint", ""))
            end_session_endpoint = str(discovery.get("end_session_endpoint", ""))
        except HTTPException:
            pass

    return OidcPublicConfig(
        enabled=get_bool_attr(settings, "oidc_enabled", False),
        oidc_only=get_bool_attr(settings, "oidc_only", False),
        issuer=get_str_attr(settings, "oidc_issuer", ""),
        client_id=get_str_attr(settings, "oidc_client_id", ""),
        redirect_uri=get_str_attr(settings, "oidc_redirect_uri", ""),
        post_logout_redirect_uri=get_str_attr(
            settings, "oidc_post_logout_redirect_uri", ""
        ),
        response_type=get_str_attr(settings, "oidc_response_type", "code"),
        scope=get_str_attr(settings, "oidc_scope", "openid profile email"),
        authorization_endpoint=authorization_endpoint,
        end_session_endpoint=end_session_endpoint,
    )


@router.post("/callback", response_model=TokenResponse)
async def oidc_callback(body: dict[str, str], db: AsyncSession = Depends(get_db)):
    """Exchange an OIDC authorization code for an application JWT."""
    code = (body.get("code") or "").strip()
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OIDC authorization code.",
        )
    user = await exchange_code(db, code)
    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_oidc_settings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Reset OIDC settings to their defaults."""
    settings = await get_or_create_settings(db)
    settings.sqlmodel_update(OIDC_DEFAULT)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
