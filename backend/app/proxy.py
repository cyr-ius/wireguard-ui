"""Trusted-proxy aware helpers for reading forwarded request metadata.

``X-Forwarded-*`` headers are client-supplied and therefore spoofable. They are
only honoured when the direct TCP peer is a proxy explicitly declared in
``TRUSTED_PROXIES``; otherwise the socket peer / real scheme is used. This keeps
per-IP throttling and the ``Secure`` cookie flag reliable behind a reverse proxy
without letting a directly-connected client forge either value.
"""

from __future__ import annotations

import ipaddress
import logging

from fastapi import Request

from .config import app_settings

logger = logging.getLogger(__name__)


def _parse_trusted_networks() -> list:
    networks = []
    for entry in app_settings.trusted_proxies.split(","):
        entry = entry.strip()
        if not entry:
            continue
        try:
            networks.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            logger.warning("Ignoring invalid TRUSTED_PROXIES entry: %r", entry)
    return networks


# Parsed once at import; TRUSTED_PROXIES is deployment config, not per-request.
_TRUSTED_NETWORKS = _parse_trusted_networks()


def _peer_is_trusted(request: Request) -> bool:
    """Whether the immediate TCP peer is a declared trusted proxy."""
    if not _TRUSTED_NETWORKS or request.client is None:
        return False
    try:
        peer = ipaddress.ip_address(request.client.host)
    except ValueError:
        return False
    return any(peer in network for network in _TRUSTED_NETWORKS)


def client_ip(request: Request) -> str:
    """Return the originating client IP.

    When the peer is a trusted proxy, use the right-most ``X-Forwarded-For``
    entry — the address that trusted proxy actually observed, which a client
    cannot forge. Otherwise fall back to the socket peer.
    """
    if _peer_is_trusted(request):
        forwarded = request.headers.get("x-forwarded-for", "")
        hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"


def is_https(request: Request) -> bool:
    """Whether the request reached the client over HTTPS.

    Honours ``X-Forwarded-Proto`` only from a trusted proxy, else the real
    connection scheme.
    """
    if _peer_is_trusted(request):
        proto = request.headers.get("x-forwarded-proto")
        if proto:
            return proto.split(",")[0].strip().lower() == "https"
    return request.url.scheme == "https"
