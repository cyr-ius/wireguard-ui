"""OIDC configuration router (portalcrane-style /api/oidc/settings endpoints)."""

from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import GlobalSettings, User
from ..schemas import OidcSettingsResponse, OidcSettingsUpdate

router = APIRouter()


def _get_bool_attr(obj: object, name: str, default: bool = False) -> bool:
    return bool(getattr(obj, name, default))


def _get_str_attr(obj: object, name: str, default: str = "") -> str:
    value = getattr(obj, name, default)
    return value if isinstance(value, str) else default


def _to_oidc_response(settings: GlobalSettings) -> OidcSettingsResponse:
    return OidcSettingsResponse(
        enabled=_get_bool_attr(settings, "oidc_enabled", False),
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


async def _get_or_create_settings(db: AsyncSession) -> GlobalSettings:
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None:
        settings = GlobalSettings.model_validate(
            {
                "dns_servers": "1.1.1.1,8.8.8.8",
                "config_file_path": "/etc/wireguard/wg0.conf",
                "maintenance_mode": False,
                "oidc_enabled": False,
                "oidc_response_type": "code",
                "oidc_scope": "openid profile email",
            }
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


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
    settings = await _get_or_create_settings(db)

    settings.sqlmodel_update(
        {
            "oidc_enabled": payload.enabled,
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
