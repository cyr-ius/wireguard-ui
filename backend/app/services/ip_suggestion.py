"""
IP address suggestion service.
Computes the next available IP in the WireGuard network CIDR
based on already-allocated client IPs and the server address.
"""

from __future__ import annotations

import ipaddress
import logging

logger = logging.getLogger(__name__)


def suggest_next_ip(
    server_cidr: str,
    allocated_ips: list[str],
) -> str | None:
    """Return the next available client IP in the server CIDR, skipping the server's own address."""
    try:
        # Parse the network from server CIDR (e.g. "10.0.0.1/24" -> 10.0.0.0/24)
        network = ipaddress.ip_network(server_cidr, strict=False)
    except ValueError:
        logger.warning("Invalid server CIDR: %s", server_cidr)
        return None

    # Collect all host IPs already in use (server + clients)
    used_ips: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()

    # Reserve the address actually assigned to the WireGuard server:
    # the first usable host in the configured subnet.
    try:
        used_ips.add(next(network.hosts()))
    except StopIteration, ValueError:
        logger.debug("Could not reserve server IP from network %s", network)

    # Add all client allocated IPs (strip /32 or /128 suffix)
    for ip_cidr in allocated_ips:
        try:
            ip_str = ip_cidr.split("/")[0]
            used_ips.add(ipaddress.ip_address(ip_str))
        except ValueError:
            logger.debug("Could not parse allocated IP: %s", ip_cidr)

    # Find the first available host in the network
    for host in network.hosts():
        if host not in used_ips:
            return f"{host}/{network.prefixlen if network.prefixlen == 32 else 32}"

    logger.warning("No available IP addresses in network %s", network)
    return None
