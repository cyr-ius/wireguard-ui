"""
Pydantic v2 schemas for all request bodies and response models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi_mail import NameEmail
from pydantic import EmailStr
from sqlmodel import Field, SQLModel

Lang = Literal["en", "fr", "es"]

# ── Auth ──────────────────────────────────────────────────────────────────────


class LoginRequest(SQLModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class PasswordChangeRequest(SQLModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class RoleResponse(SQLModel):
    id: int
    name: str
    description: str | None = None
    permissions: str | None = None
    model_config = {"from_attributes": True}


class UserResponse(SQLModel):
    id: int
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    active: bool
    roles: list[RoleResponse] = Field(default_factory=list)
    model_config = {"from_attributes": True}


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Users ─────────────────────────────────────────────────────────────────────


class UserCreate(SQLModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    password: str = Field(..., min_length=8)
    role_ids: list[int] = Field(default_factory=list)
    active: bool = True


class UserUpdate(SQLModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    active: bool | None = None
    role_ids: list[int] | None = None


# ── WireGuard Server ──────────────────────────────────────────────────────────


class ServerCreate(SQLModel):
    address: str = Field(..., description="CIDR notation, e.g. 10.0.0.1/24")
    listen_port: int = Field(default=51820, ge=1, le=65535)
    private_key: str
    public_key: str
    postup: str | None = None
    postdown: str | None = None


class ServerResponse(SQLModel):
    id: int
    address: str
    listen_port: int
    private_key: str
    public_key: str
    postup: str | None = None
    postdown: str | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class KeyPairResponse(SQLModel):
    private_key: str
    public_key: str


# ── WireGuard Clients ─────────────────────────────────────────────────────────


class ClientCreate(SQLModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    allocated_ips: str
    allowed_ips: list[str] = ["0.0.0.0/0"]
    use_server_dns: bool = True
    enabled: bool = True
    preshared_key: str | None = ""
    send_email: bool = False
    email_language: str = "en"


class ClientUpdate(SQLModel):
    name: str | None = None
    email: EmailStr | None = None
    allocated_ips: str | None = None
    allowed_ips: list[str] | None = None
    use_server_dns: bool | None = None
    enabled: bool | None = None
    preshared_key: str | None = None


class ClientResponse(SQLModel):
    id: int
    name: str
    email: str
    public_key: str
    preshared_key: str | None = None
    allocated_ips: str
    allowed_ips: list[str]
    use_server_dns: bool
    enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class ClientConfigResponse(SQLModel):
    client_id: int
    config: str
    qr_code_base64: str | None = None


class SendClientEmailRequest(SQLModel):
    """Request body for sending a client configuration email."""

    language: str = Field(default="en", description="Language code: en, fr, es")


class SuggestIpResponse(SQLModel):
    """Response containing the suggested next available IP address."""

    suggested_ip: str | None = None


# ── Settings ──────────────────────────────────────────────────────────────────


class SettingsUpdate(SQLModel):
    endpoint_address: str | None = None
    dns_servers: list[str] | None = None
    mtu: int | None = Field(default=None, ge=576, le=9000)
    persistent_keepalive: int | None = Field(default=None, ge=0, le=65535)
    maintenance_mode: bool | None = None
    default_email_language: Lang | None = None


class SettingsResponse(SQLModel):
    id: int
    endpoint_address: str | None = None
    dns_servers: list[str] | None = None
    mtu: int | None = None
    persistent_keepalive: int | None = None
    maintenance_mode: bool
    default_email_language: str = "en"
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


# ── SMTP Settings ─────────────────────────────────────────────────────────────


class SmtpSettingsUpdate(SQLModel):
    """Request body for updating SMTP/email server settings."""

    smtp_server: str | None = None
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_from_name: str | None = None
    smtp_tls: bool = False
    smtp_ssl: bool = False
    smtp_verify: bool = False
    default_email_language: Lang = "en"


class SmtpSettingsResponse(SQLModel):
    """Response containing SMTP settings (password is excluded for security)."""

    smtp_server: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_from: str | None = None
    smtp_from_name: str | None = None
    smtp_tls: bool = True
    smtp_ssl: bool = False
    smtp_verify: bool = True
    default_email_language: Lang = "en"
    smtp_configured: bool = False
    model_config = {"from_attributes": True}


class SmtpTestRequest(SQLModel):
    """Request body for sending a test email."""

    recipient: NameEmail


# ── OIDC ─────────────────────────────────────────────────────────────────────


class OidcSettingsUpdate(SQLModel):
    enabled: bool = False
    oidc_only: bool = False
    issuer: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    post_logout_redirect_uri: str | None = None
    response_type: str = "code"
    scope: str = "openid profile email"


class OidcSettingsResponse(SQLModel):
    enabled: bool
    oidc_only: bool = False
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    post_logout_redirect_uri: str
    response_type: str
    scope: str


class OidcPublicConfig(SQLModel):
    enabled: bool
    oidc_only: bool = False
    issuer: str
    client_id: str
    redirect_uri: str
    post_logout_redirect_uri: str
    response_type: str
    scope: str
    authorization_endpoint: str = ""
    end_session_endpoint: str = ""


class OidcCallbackRequest(SQLModel):
    code: str = Field(..., min_length=1)


# ── Status ────────────────────────────────────────────────────────────────────


class PeerStatus(SQLModel):
    public_key: str
    endpoint: str | None = None
    latest_handshake: str | None = None
    transfer_rx: str | None = None
    transfer_tx: str | None = None
    allowed_ips: str | None = None


class WireGuardStatus(SQLModel):
    state: str  # "running" | "stopped" | "error"
    interface: str | None = None
    public_key: str | None = None
    listen_port: int | None = None
    peers: list[PeerStatus] = Field(default_factory=list)


class IPAddressInfo(SQLModel):
    name: str
    ip_address: str


class AppVersionResponse(SQLModel):
    repository: str
    version: str


class GithubReleaseResponse(SQLModel):
    html_url: str
    name: str
    tag_name: str
    published_at: str
