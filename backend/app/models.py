"""SQLModel ORM models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(UTC)


class UserRoleLink(SQLModel, table=True):
    __tablename__ = "user_roles"  # type: ignore

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)


class Role(SQLModel, table=True):
    """Role model — carries a comma-separated list of permission strings."""

    __tablename__ = "roles"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=80, unique=True, index=True)
    description: str | None = Field(default=None, max_length=255)
    permissions: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),  # e.g. "admin-read,admin-write"
    )

    users: list["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)  # noqa: UP037

    def has_permission(self, permission: str) -> bool:
        if not self.permissions:
            return False
        return permission in self.permissions.split(",")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(SQLModel, table=True):
    """Application user with hashed password and role associations."""

    __tablename__ = "users"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=255, unique=True, index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    hashed_password: str = Field(max_length=255)
    auth_source: str = Field(default="local", max_length=20)
    active: bool = Field(default=True)
    fs_uniquifier: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        max_length=64,
        unique=True,
        index=True,
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
    )

    roles: list[Role] = Relationship(back_populates="users", link_model=UserRoleLink)

    def has_role(self, role_name: str) -> bool:
        return any(r.name == role_name for r in self.roles)

    def has_permission(self, permission: str) -> bool:
        return any(r.has_permission(permission) for r in self.roles)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class WireGuardServer(SQLModel, table=True):
    """WireGuard server interface configuration."""

    __tablename__ = "wg_server"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    address: str = Field(max_length=50)
    listen_port: int = Field(default=51820)
    private_key: str = Field(max_length=255)
    public_key: str = Field(max_length=255)
    postup: str | None = Field(
        default="EXT_IF=$(ip route show default | awk '/default/ {print $5; exit}'); iptables -A FORWARD -i wg0 -o $EXT_IF -j ACCEPT; iptables -A FORWARD -i $EXT_IF -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -A POSTROUTING -o $EXT_IF -j MASQUERADE",
        sa_column=Column(Text, nullable=True),
    )
    postdown: str | None = Field(
        default="EXT_IF=$(ip route show default | awk '/default/ {print $5; exit}'); iptables -D FORWARD -i wg0 -o $EXT_IF -j ACCEPT; iptables -D FORWARD -i $EXT_IF -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -D POSTROUTING -o $EXT_IF -j MASQUERADE",
        sa_column=Column(Text, nullable=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
    )

    def __repr__(self) -> str:
        return f"<WireGuardServer {self.address}:{self.listen_port}>"


class WireGuardClient(SQLModel, table=True):
    """WireGuard client (peer) configuration."""

    __tablename__ = "wg_clients"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    public_key: str = Field(max_length=255)
    private_key: str = Field(max_length=255)
    preshared_key: str | None = Field(default="")
    allocated_ips: str = Field(max_length=255)
    allowed_ips: list[str] = Field(
        default=["0.0.0.0/0"], max_length=255, sa_column=Column(JSON)
    )
    use_server_dns: bool = Field(default=True)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
    )

    def __repr__(self) -> str:
        return f"<WireGuardClient {self.name}>"


class OidcSettings(SQLModel, table=True):
    """OIDC / OpenID Connect configuration (single row)."""

    __tablename__ = "oidc_settings"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    enabled: bool = Field(default=False)
    oidc_only: bool = Field(default=False)
    issuer: str = Field(default="", max_length=512)
    client_id: str = Field(default="", max_length=255)
    client_secret: str = Field(default="", max_length=512)
    redirect_uri: str = Field(default="", max_length=512)
    post_logout_redirect_uri: str = Field(default="", max_length=512)
    response_type: str = Field(default="code", max_length=50)
    scope: str = Field(default="openid profile email", max_length=255)

    def __repr__(self) -> str:
        return f"<OidcSettings issuer={self.issuer}>"


class SmtpSettings(SQLModel, table=True):
    """SMTP / email relay configuration (single row)."""

    __tablename__ = "smtp_settings"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    server: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)
    from_address: str | None = Field(default="no-reply@wg.ui", max_length=255)
    from_name: str = Field(default="WireGuard UI", max_length=255)
    tls: bool = Field(default=True)
    ssl: bool = Field(default=False)
    verify: bool = Field(default=True)
    default_language: str = Field(default="en", max_length=5)

    def __repr__(self) -> str:
        return f"<SmtpSettings server={self.server}>"


class GlobalSettings(SQLModel, table=True):
    """Global application and VPN settings (single row)."""

    __tablename__ = "global_settings"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    endpoint_address: str | None = Field(default=None, max_length=255)
    dns_servers: list[str] | None = Field(
        default=["1.1.1.1"], max_length=255, sa_column=Column(JSON)
    )
    mtu: int | None = Field(default=None)
    persistent_keepalive: int | None = Field(default=None)
    maintenance_mode: bool = Field(default=False)

    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now},
    )

    def __repr__(self) -> str:
        return f"<GlobalSettings endpoint={self.endpoint_address}>"
