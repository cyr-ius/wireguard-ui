"""Global settings router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import GlobalSettings, User
from ..schemas import SettingsResponse, SettingsUpdate

router = APIRouter()

SETTINGS_DEFAULTS = {
    "endpoint_address": None,
    "dns_servers": ["1.1.1.1"],
    "mtu": None,
    "persistent_keepalive": None,
    "maintenance_mode": False,
    "default_email_language": "en",
}


@router.get("", response_model=SettingsResponse)
async def get_settings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Return the current global settings."""
    s = (await db.exec(select(GlobalSettings))).one_or_none()
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Settings not found")
    return s


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Partially update global settings."""
    s = (await db.exec(select(GlobalSettings))).one_or_none()
    if s is None:
        s = GlobalSettings.model_validate(data.model_dump(exclude_unset=True))
        db.add(s)
    else:
        s.sqlmodel_update(data.model_dump(exclude_unset=True))
        db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reset only the global network settings to their defaults."""
    s = (await db.exec(select(GlobalSettings))).one_or_none()
    if s is None:
        s = GlobalSettings(**SETTINGS_DEFAULTS)
    else:
        s.sqlmodel_update(SETTINGS_DEFAULTS)

    db.add(s)
    await db.commit()
    await db.refresh(s)
