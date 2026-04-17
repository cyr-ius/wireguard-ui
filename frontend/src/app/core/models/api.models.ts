// ─── Authentication ──────────────────────────────────────────────────────────

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

// ─── Users & Roles ───────────────────────────────────────────────────────────

export interface Role {
  id: number;
  name: string;
  description?: string;
  permissions?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  active: boolean;
  roles: Role[];
}

export interface UserCreate {
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  password: string;
  role_ids: number[];
  active: boolean;
}

export interface UserUpdate {
  email?: string;
  first_name?: string;
  last_name?: string;
  active?: boolean;
  role_ids?: number[];
}

// ─── WireGuard Server ─────────────────────────────────────────────────────────

export interface WireGuardServer {
  id: number;
  address: string;
  listen_port: number;
  public_key: string;
  postup?: string;
  postdown?: string;
  updated_at?: string;
}

export interface ServerCreate {
  address: string;
  listen_port: number;
  private_key: string;
  public_key: string;
  postup?: string;
  postdown?: string;
}

export interface KeyPair {
  private_key: string;
  public_key: string;
}

// ─── WireGuard Clients ────────────────────────────────────────────────────────

export interface WireGuardClient {
  id: number;
  name: string;
  email: string;
  public_key: string;
  preshared_key?: string;
  allocated_ips: string;
  allowed_ips: string[];
  use_server_dns: boolean;
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ClientCreate {
  name: string;
  email: string;
  allocated_ips: string;
  allowed_ips: string;
  use_server_dns: boolean;
  enabled: boolean;
  preshared_key?: string;
  /** Whether to send config email on creation */
  send_email: boolean;
  /** Language for the email template: en, fr, es */
  email_language: string;
}

export interface ClientUpdate {
  name?: string;
  email?: string;
  allocated_ips?: string;
  allowed_ips?: string;
  use_server_dns?: boolean;
  enabled?: boolean;
  preshared_key?: string;
}

export interface ClientConfig {
  config: string;
  client_id: number;
  /** Base64-encoded PNG QR code image */
  qr_code_base64?: string;
}

export interface SendClientEmailRequest {
  /** Language code: en, fr, es */
  language: string;
}

export interface SuggestIpResponse {
  suggested_ip: string | null;
}

// ─── Settings ─────────────────────────────────────────────────────────────────

export interface GlobalSettings {
  id: number;
  endpoint_address?: string;
  dns_servers?: string[];
  mtu?: number;
  persistent_keepalive?: number;
  config_file_path: string;
  maintenance_mode: boolean;
  updated_at?: string;
}

export interface SettingsUpdate {
  endpoint_address?: string;
  dns_servers?: string[];
  mtu?: number;
  persistent_keepalive?: number;
  config_file_path?: string;
  maintenance_mode?: boolean;
}

// ─── SMTP Settings ─────────────────────────────────────────────────────────────

export interface SmtpSettings {
  smtp_server: string | null;
  smtp_port: number | null;
  smtp_username: string | null;
  smtp_from: string | null;
  smtp_from_name: string | null;
  smtp_tls: boolean;
  smtp_ssl: boolean;
  smtp_verify: boolean;
  default_email_language: string;
  smtp_configured: boolean;
}

export interface SmtpSettingsUpdate {
  smtp_server?: string | null;
  smtp_port?: number | null;
  smtp_username?: string | null;
  smtp_password?: string | null;
  smtp_from?: string | null;
  smtp_from_name?: string | null;
  smtp_tls: boolean;
  smtp_ssl: boolean;
  smtp_verify: boolean;
  default_email_language: string;
}

export interface SmtpTestRequest {
  recipient: string;
}

// ─── OIDC ─────────────────────────────────────────────────────────────────────

export interface OidcAdminSettings {
  enabled: boolean;
  oidc_only: boolean;
  issuer: string;
  client_id: string;
  client_secret: string;
  redirect_uri: string;
  post_logout_redirect_uri: string;
  response_type: string;
  scope: string;
}

export interface OidcPublicConfig {
  enabled: boolean;
  oidc_only: boolean;
  issuer: string;
  client_id: string;
  redirect_uri: string;
  post_logout_redirect_uri: string;
  response_type: string;
  scope: string;
  authorization_endpoint: string;
  end_session_endpoint: string;
}

// ─── Status ───────────────────────────────────────────────────────────────────

export interface PeerStatus {
  public_key: string;
  endpoint?: string;
  latest_handshake?: string;
  transfer_rx?: string;
  transfer_tx?: string;
  allowed_ips?: string;
}

export interface WireGuardStatus {
  state: "running" | "stopped" | "error";
  interface?: string;
  peers: PeerStatus[];
}

export interface IPAddressInfo {
  name: string;
  ip_address: string;
}

export interface AppVersionResponse {
  repository: string;
  version: string;
}
