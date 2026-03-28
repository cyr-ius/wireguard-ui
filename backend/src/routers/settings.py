"""Global settings router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import GlobalSettings, User
from ..schemas import SettingsResponse, SettingsUpdate

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    s = (await db.exec(select(GlobalSettings))).one_or_none()
    if not s:
        raise HTTPException(404, detail="Settings not found")
    return s


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
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
