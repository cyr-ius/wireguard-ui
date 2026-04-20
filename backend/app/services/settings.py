"""Global settings CRUD helpers."""

from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import GlobalSettings

SETTINGS_DEFAULTS: dict = {
    "endpoint_address": None,
    "dns_servers": ["1.1.1.1"],
    "mtu": None,
    "persistent_keepalive": None,
    "maintenance_mode": False,
}


async def get_or_create_settings(db: AsyncSession) -> GlobalSettings:
    """Return the single GlobalSettings row, creating it with defaults if absent."""
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None:
        settings = GlobalSettings.model_validate(SETTINGS_DEFAULTS)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings
