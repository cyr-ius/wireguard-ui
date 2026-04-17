"""WireGuard server configuration and service control router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import User, WireGuardServer
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
logger = logging.getLogger(__name__)


@router.get("", response_model=ServerResponse)
async def get_server(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    server = (await db.exec(select(WireGuardServer))).one_or_none()
    if not server:
        raise HTTPException(404, detail="Server not configured yet")
    return server


@router.put("", response_model=ServerResponse)
async def upsert_server(
    data: ServerCreate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    server = (await db.exec(select(WireGuardServer))).one_or_none()

    if server is None:
        server = WireGuardServer.model_validate(data)
        db.add(server)
    else:
        server.sqlmodel_update(data.model_dump())
        db.add(server)
    await db.commit()
    await db.refresh(server)

    try:
        await write_server_config()
    except WireGuardError as exc:
        logger.exception("WireGuard apply config failed: %s", exc)
        raise HTTPException(
            500, detail="Failed to apply WireGuard configuration. Check server logs."
        )
    except Exception as exc:
        logger.exception("Unexpected error while applying WireGuard config: %s", exc)
        raise HTTPException(
            500, detail="Failed to apply WireGuard configuration. Check server logs."
        )

    return server


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def reset_server(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove the saved WireGuard server configuration."""
    await db.exec(delete(WireGuardServer))
    await db.commit()


@router.post("/keypair", response_model=KeyPairResponse)
async def gen_keypair(_: User = Depends(get_current_admin)):
    try:
        return KeyPairResponse(**(await generate_keypair()))
    except WireGuardError as exc:
        raise HTTPException(500, detail=str(exc))


@router.post("/apply", status_code=status.HTTP_204_NO_CONTENT)
async def apply_config(_: User = Depends(get_current_admin)):
    """Write config to disk and restart WireGuard."""
    try:
        await write_server_config()
        await restart_service()
    except WireGuardError as exc:
        logger.exception("WireGuard apply config failed: %s", exc)
        raise HTTPException(
            500, detail="Failed to apply WireGuard configuration. Check server logs."
        )
    except Exception as exc:
        logger.exception("Unexpected error while applying WireGuard config: %s", exc)
        raise HTTPException(
            500, detail="Failed to apply WireGuard configuration. Check server logs."
        )


@router.post("/service/{action}", status_code=status.HTTP_204_NO_CONTENT)
async def control_service(action: str, _: User = Depends(get_current_admin)):
    """start | stop | restart the WireGuard interface."""
    try:
        match action:
            case "start":
                await write_server_config()
                await start_service()
            case "stop":
                await stop_service()
            case "restart":
                await write_server_config()
                await restart_service()
            case _:
                raise HTTPException(400, detail=f"Unknown action: {action}")
    except WireGuardError as exc:
        logger.exception("WireGuard service action '%s' failed: %s", action, exc)
        raise HTTPException(
            500, detail="WireGuard service action failed. Check server logs."
        )
