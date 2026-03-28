"""WireGuard server configuration and service control router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import GlobalSettings, User, WireGuardClient, WireGuardServer
from ..schemas import KeyPairResponse, ServerCreate, ServerResponse
from ..services.wireguard import (
    WireGuardError,
    generate_keypair,
    restart_service,
    start_service,
    stop_service,
    write_server_config,
)

router = APIRouter()


@router.get("", response_model=ServerResponse)
async def get_server(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    s = (await db.exec(select(WireGuardServer))).one_or_none()
    if not s:
        raise HTTPException(404, detail="Server not configured yet")
    return s


@router.put("", response_model=ServerResponse)
async def upsert_server(
    data: ServerCreate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    s = (await db.exec(select(WireGuardServer))).one_or_none()
    if s is None:
        s = WireGuardServer.model_validate(data)
        db.add(s)
    else:
        s.sqlmodel_update(data.model_dump())
        db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.post("/keypair", response_model=KeyPairResponse)
async def gen_keypair(_: User = Depends(get_current_admin)):
    try:
        return KeyPairResponse(**(await generate_keypair()))
    except WireGuardError as exc:
        raise HTTPException(500, detail=str(exc))


@router.post("/apply", status_code=status.HTTP_204_NO_CONTENT)
async def apply_config(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Write config to disk and restart WireGuard."""
    s = (await db.exec(select(WireGuardServer))).one_or_none()
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    clients = (await db.exec(select(WireGuardClient))).all()

    if not s:
        raise HTTPException(400, detail="Server not configured")
    if not settings:
        raise HTTPException(400, detail="Settings not configured")

    try:
        await write_server_config(s, clients, settings)
        await restart_service()
    except WireGuardError as exc:
        raise HTTPException(500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(500, detail=f"Failed to apply config: {exc}")


@router.post("/service/{action}", status_code=status.HTTP_204_NO_CONTENT)
async def control_service(action: str, _: User = Depends(get_current_admin)):
    """start | stop | restart the WireGuard interface."""
    try:
        match action:
            case "start":
                await start_service()
            case "stop":
                await stop_service()
            case "restart":
                await restart_service()
            case _:
                raise HTTPException(400, detail=f"Unknown action: {action}")
    except WireGuardError as exc:
        raise HTTPException(500, detail=str(exc))
