"""Models handler."""
from flask_restx import Model, fields

POSTUP = "iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE"
POSTDOWN = "iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE"

message = Model("Error", {"message": fields.String(required=True)})
forbidden = Model(
    "Forbidden", {"message": fields.String(default="The provided API key is not valid")}
)
client = Model(
    "Client",
    {
        "name": fields.String(required=True, description="The user name"),
        "email": fields.String(required=True, description="Email"),
        "allocated_ips": fields.String(required=True, description="IP Allocation"),
        "allowed_ips": fields.String(description="Allowed IPs", default="0.0.0.0/0"),
        "use_server_dns": fields.Boolean(description="Use DNS Server", default=True),
        "enabled": fields.Boolean(description="Enable this client", default=True),
    },
)

clients = Model(
    "Clients",
    {
        "id": fields.Integer(required=True, description="Id"),
        **client,
    },
)

server = Model(
    "Server",
    {
        "address": fields.String(required=True, description="192.168.1.0/24"),
        "private_key": fields.String(required=True, description="private_key"),
        "public_key": fields.String(required=True, description="public_key"),
        "postup": fields.String(description="Post up script", default=POSTUP),
        "postdown": fields.String(description="Post own script", default=POSTDOWN),
        "listen_port": fields.Integer(
            description="Listen Port", default=51820, min=1, max=65535
        ),
    },
)

global_settings = Model(
    "GlobalSettings",
    {
        "endpoint_address": fields.String(
            required=True, description="Endpoint Address"
        ),
        "dns_servers": fields.String(description="The user name"),
        "mtu": fields.Integer(description="IP Allocation"),
        "config_file_path": fields.String(
            description="Persistent Keepalive", default="/etc/wireguard/wg0.conf"
        ),
    },
)

user = Model(
    "User",
    {
        "first_name": fields.String(required=True, description="First name"),
        "last_name": fields.String(description="Last name"),
        "email": fields.String(required=True, description="Email"),
        "gravatar_url": fields.String(description="Gravatar url"),
    },
)

version = Model(
    "Version",
    {
        "current_version": fields.String(required=True, description="Current version"),
        "update_available": fields.Boolean(description="Update available"),
    },
)


pairing_key = Model(
    "KeyPair",
    {
        "PrivateKey": fields.String(required=True, description="Current version"),
        "PublicKey": fields.String(required=True, description="Current version"),
    },
)


ip_addresses = Model(
    "IPaddresses",
    {
        "name": fields.String(required=True),
        "ip_address": fields.String(required=True),
    },
)

suggest_client_ip = Model(
    "SuggestIP",
    {
        "ip_address": fields.String(required=True),
    },
)
status = Model(
    "ActiveStatus",
    {
        "id": fields.Integer(required=True, description="Client id"),
        "status": fields.Boolean(required=True, description="To active set True"),
    },
)
