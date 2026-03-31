"""WireGuard clients router — full CRUD, admin only."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
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
    SendClientEmailRequest,
    SuggestIpResponse,
)
from ..services.email import SupportedLanguage, send_client_config_email
from ..services.ip_suggestion import suggest_next_ip
from ..services.qr import generate_qr_code_base64
from ..services.wireguard import (
    WireGuardError,
    build_client_config,
    generate_keypair,
    get_machine_ips,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> list[ClientResponse]:
    """List all WireGuard clients ordered by name."""
    result = await db.exec(select(WireGuardClient).order_by(WireGuardClient.name))
    return result.all()  # type: ignore[return-value]


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    """Create a new WireGuard client peer.

    Optionally sends a configuration email to the client if send_email is True.

    Args:
        data: Client creation data including optional email sending preferences.
        background_tasks: FastAPI background tasks for async email sending.
    """

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

    payload = data.model_dump(exclude={"send_email", "email_language"})
    payload["public_key"] = keys["public_key"]
    payload["private_key"] = keys["private_key"]
    payload["preshared_key"] = payload.get("preshared_key") or ""

    client = WireGuardClient.model_validate(payload)
    db.add(client)
    await db.commit()
    await db.refresh(client)

    # Optionally send configuration email in background
    if data.send_email:
        server = (await db.exec(select(WireGuardServer))).one_or_none()
        settings = (await db.exec(select(GlobalSettings))).one_or_none()

        if server and settings and settings.smtp_server:
            config_content = build_client_config(client, server, settings)
            default_language = (
                settings.default_email_language
                if settings.default_email_language in ("en", "fr", "es")
                else "en"
            )
            lang: SupportedLanguage = (
                data.email_language
                if data.email_language in ("en", "fr", "es")
                else default_language
            )  # type: ignore[assignment]

            background_tasks.add_task(
                send_client_config_email,
                client,
                server,
                settings,
                config_content,
                lang,
            )
            logger.info(
                "Scheduled config email for client '%s' to %s",
                client.name,
                client.email,
            )
        else:
            logger.warning(
                "Email sending requested for client '%s' but SMTP is not configured.",
                client.name,
            )

    return client  # type: ignore[return-value]


@router.get("/suggest-ip", response_model=SuggestIpResponse)
async def suggest_ip(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SuggestIpResponse:
    """Suggest the next available IP address based on server CIDR and existing clients.

    Returns the first free IP host in the server's network range
    that is not yet allocated to any client.
    """
    server = (await db.exec(select(WireGuardServer))).one_or_none()
    if not server:
        return SuggestIpResponse(suggested_ip=None)

    # Collect all currently allocated IPs
    clients = (await db.exec(select(WireGuardClient))).all()
    allocated = [c.allocated_ips for c in clients]

    suggested = suggest_next_ip(server.address, allocated)
    return SuggestIpResponse(suggested_ip=suggested)


@router.get("/utils/keypair", response_model=KeyPairResponse)
async def generate_client_keypair(
    _: User = Depends(get_current_admin),
) -> KeyPairResponse:
    """Generate a new WireGuard key pair for a client."""
    try:
        return KeyPairResponse(**(await generate_keypair()))
    except WireGuardError as exc:
        raise HTTPException(500, detail=str(exc))


@router.get("/utils/machine-ips")
async def machine_ips(_: User = Depends(get_current_admin)) -> list[dict]:
    """Return all non-loopback IP addresses on the host machine."""
    return get_machine_ips()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    """Retrieve a single client by ID."""
    c = await db.get(WireGuardClient, client_id)
    if not c:
        raise HTTPException(404, detail="Client not found")
    return c  # type: ignore[return-value]


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    """Partially update a client's configuration."""
    c = await db.get(WireGuardClient, client_id)
    if not c:
        raise HTTPException(404, detail="Client not found")

    payload = data.model_dump(exclude_unset=True)
    unique_checks = [
        ("name", WireGuardClient.name, "Client name already in use"),
        ("email", WireGuardClient.email, "Email address already in use"),
        ("allocated_ips", WireGuardClient.allocated_ips, "IP address already in use"),
    ]
    for field_name, model_field, message in unique_checks:
        if field_name not in payload:
            continue
        if payload[field_name] == getattr(c, field_name):
            continue
        existing = (
            await db.exec(
                select(WireGuardClient).where(model_field == payload[field_name])
            )
        ).one_or_none()
        if existing:
            raise HTTPException(422, detail=message)

    c.sqlmodel_update(payload)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c  # type: ignore[return-value]


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a client and remove its peer configuration."""
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
) -> ClientConfigResponse:
    """Return the WireGuard configuration for a client, optionally with QR code.

    Args:
        client_id: The client's ID.
    """
    client = await db.get(WireGuardClient, client_id)
    server = (await db.exec(select(WireGuardServer))).one_or_none()
    settings = (await db.exec(select(GlobalSettings))).one_or_none()

    if not client:
        raise HTTPException(404, detail="Client not found")
    if not server:
        raise HTTPException(400, detail="Server not configured")
    if not settings:
        raise HTTPException(400, detail="Settings not configured")

    config_content = build_client_config(client, server, settings)
    qr_code_base64 = generate_qr_code_base64(config_content)

    return ClientConfigResponse(
        client_id=client_id,
        config=config_content,
        qr_code_base64=qr_code_base64,
    )


@router.post("/{client_id}/send-email", status_code=status.HTTP_204_NO_CONTENT)
async def send_client_email(
    client_id: int,
    body: SendClientEmailRequest,
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Send the WireGuard configuration email to a client.

    Sends an HTML email with QR code and .conf file attachment in the specified language.

    Args:
        client_id: The client's ID.
        body: Request body containing the language preference.
    """
    client = await db.get(WireGuardClient, client_id)
    if not client:
        raise HTTPException(404, detail="Client not found")

    server = (await db.exec(select(WireGuardServer))).one_or_none()
    settings = (await db.exec(select(GlobalSettings))).one_or_none()

    if not server:
        raise HTTPException(400, detail="Server not configured")
    if not settings:
        raise HTTPException(400, detail="Settings not configured")
    if not settings.smtp_server or not settings.smtp_port:
        raise HTTPException(
            400,
            detail="SMTP is not configured. Please configure it in Administration > Mail Server.",
        )

    config_content = build_client_config(client, server, settings)
    default_language = (
        settings.default_email_language
        if settings.default_email_language in ("en", "fr", "es")
        else "en"
    )
    lang: SupportedLanguage = (
        body.language if body.language in ("en", "fr", "es") else default_language
    )  # type: ignore[assignment]

    background_tasks.add_task(
        send_client_config_email,
        client,
        server,
        settings,
        config_content,
        lang,
    )

    logger.info(
        "Scheduled config email for client '%s' (language: %s)",
        client.name,
        lang,
    )
