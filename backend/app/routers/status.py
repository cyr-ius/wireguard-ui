"""WireGuard runtime status router — accessible to all authenticated users."""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..config import GITHUB_REPOSITORY, app_settings
from ..models import User
from ..schemas import AppVersionResponse, GithubReleaseResponse, WireGuardStatus
from ..services.wireguard import get_status

router = APIRouter()


@router.get("", response_model=WireGuardStatus)
async def wireguard_status(_: User = Depends(get_current_user)):
    """Return current WireGuard state and peer statistics."""
    return WireGuardStatus(**(await get_status()))


@router.get("/version", response_model=AppVersionResponse)
async def app_version(_: User = Depends(get_current_user)):
    """Return application version loaded from APP_VERSION env var."""
    return AppVersionResponse(
        version=app_settings.app_version, repository=GITHUB_REPOSITORY
    )


@router.get("/latest-release", response_model=GithubReleaseResponse)
async def latest_release(_: User = Depends(get_current_user)):
    """Proxy GitHub releases API to avoid browser cross-origin/network restrictions."""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                url, headers={"Accept": "application/vnd.github+json"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail="Unable to reach GitHub API"
            ) from exc
