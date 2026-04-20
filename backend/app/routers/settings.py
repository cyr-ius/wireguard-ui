"""Global settings router."""

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import User
from ..schemas import SettingsResponse, SettingsUpdate
from ..services.settings import SETTINGS_DEFAULTS, get_or_create_settings

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """Return the current global settings."""
    return await get_or_create_settings(db)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """Partially update global settings."""
    s = await get_or_create_settings(db)
    s.sqlmodel_update(data.model_dump(exclude_unset=True))
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/reset", status_code=204)
async def reset_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Reset global network settings to their defaults."""
    s = await get_or_create_settings(db)
    s.sqlmodel_update(SETTINGS_DEFAULTS)
    db.add(s)
    await db.commit()
    await db.refresh(s)
