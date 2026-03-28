"""WireGuard clients router — full CRUD, admin only."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import GlobalSettings, User, WireGuardClient, WireGuardServer
from ..schemas import (
    ClientConfigResponse,
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    KeyPairResponse,
)
from ..services.wireguard import (
    WireGuardError,
    build_client_config,
    generate_keypair,
    get_machine_ips,
)

router = APIRouter()


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    result = await db.exec(select(WireGuardClient).order_by(WireGuardClient.name))
    return result.all()


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Uniqueness checks
    for field, value, msg in [
        (WireGuardClient.name, data.name, "Client name already in use"),
        (WireGuardClient.email, data.email, "Email address already in use"),
        (
            WireGuardClient.allocated_ips,
            data.allocated_ips,
            "IP address already in use",
        ),
    ]:
        if (await db.exec(select(WireGuardClient).where(field == value))).one_or_none():
            raise HTTPException(422, detail=msg)

    try:
        keys = await generate_keypair()
    except WireGuardError as exc:
        raise HTTPException(500, detail=str(exc))

    payload = data.model_dump()
    payload["public_key"] = keys["public_key"]
    payload["private_key"] = keys["private_key"]
    payload["preshared_key"] = payload.get("preshared_key") or ""
    client = WireGuardClient.model_validate(payload)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("/utils/keypair", response_model=KeyPairResponse)
async def generate_client_keypair(_: User = Depends(get_current_admin)):
    try:
        return KeyPairResponse(**(await generate_keypair()))
    except WireGuardError as exc:
        raise HTTPException(500, detail=str(exc))


@router.get("/utils/machine-ips")
async def machine_ips(_: User = Depends(get_current_admin)):
    return get_machine_ips()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(WireGuardClient, client_id)
    if not c:
        raise HTTPException(404, detail="Client not found")
    return c


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(WireGuardClient, client_id)
    if not c:
        raise HTTPException(404, detail="Client not found")
    c.sqlmodel_update(data.model_dump(exclude_unset=True))
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(WireGuardClient, client_id)
    if not c:
        raise HTTPException(404, detail="Client not found")
    await db.delete(c)
    await db.commit()


@router.get("/{client_id}/config", response_model=ClientConfigResponse)
async def get_client_config(
    client_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    client = await db.get(WireGuardClient, client_id)
    server = (await db.exec(select(WireGuardServer))).one_or_none()
    settings = (await db.exec(select(GlobalSettings))).one_or_none()

    if not client:
        raise HTTPException(404, detail="Client not found")
    if not server:
        raise HTTPException(400, detail="Server not configured")
    if not settings:
        raise HTTPException(400, detail="Settings not configured")

    return ClientConfigResponse(
        client_id=client_id, config=build_client_config(client, server, settings)
    )
