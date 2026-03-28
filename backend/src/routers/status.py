"""WireGuard runtime status router — accessible to all authenticated users."""

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..config import app_settings
from ..models import User
from ..schemas import AppVersionResponse, WireGuardStatus
from ..services.wireguard import get_status

router = APIRouter()


@router.get("", response_model=WireGuardStatus)
async def wireguard_status(_: User = Depends(get_current_user)):
    """Return current WireGuard state and peer statistics."""
    return WireGuardStatus(**(await get_status()))


@router.get("/version", response_model=AppVersionResponse)
async def app_version(_: User = Depends(get_current_user)):
    """Return application version loaded from APP_VERSION env var."""
    return AppVersionResponse(version=app_settings.app_version)
