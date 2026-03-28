import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable } from 'rxjs';
import {
  AppVersionResponse,
  ClientConfig,
  ClientCreate,
  ClientUpdate,
  GlobalSettings,
  KeyPair,
  OidcAdminSettings,
  OidcPublicConfig,
  Role,
  ServerCreate,
  SettingsUpdate,
  TokenResponse,
  User,
  UserCreate,
  UserUpdate,
  WireGuardClient,
  WireGuardServer,
  WireGuardStatus,
} from '../../shared/models/api.models';

export interface WgStatus extends WireGuardStatus {
  is_running: boolean;
  public_key?: string | null;
  listen_port?: number | null;
}

export interface GithubRelease {
  html_url: string;
  name: string;
  tag_name: string;
  published_at: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  getStatus(): Observable<WgStatus> {
    return this.http.get<WireGuardStatus>('/api/status').pipe(
      map((status) => ({
        ...status,
        is_running: status.state === 'running',
      }))
    );
  }

  getAppVersion(): Observable<AppVersionResponse> {
    return this.http.get<AppVersionResponse>('/api/status/version');
  }

  getClients(): Observable<WireGuardClient[]> {
    return this.http.get<WireGuardClient[]>('/api/clients');
  }

  createClient(data: ClientCreate): Observable<WireGuardClient> {
    return this.http.post<WireGuardClient>('/api/clients', data);
  }

  updateClient(id: number, data: ClientUpdate): Observable<WireGuardClient> {
    return this.http.patch<WireGuardClient>('/api/clients/' + id, data);
  }

  deleteClient(id: number): Observable<void> {
    return this.http.delete<void>('/api/clients/' + id);
  }

  getClientConfig(id: number): Observable<ClientConfig> {
    return this.http.get<ClientConfig>('/api/clients/' + id + '/config');
  }

  getClientConfigUrl(id: number): string {
    return '/api/clients/' + id + '/config';
  }

  getServer(): Observable<WireGuardServer> {
    return this.http.get<WireGuardServer>('/api/server');
  }

  upsertServer(data: ServerCreate): Observable<WireGuardServer> {
    return this.http.put<WireGuardServer>('/api/server', data);
  }

  generateServerKeypair(): Observable<KeyPair> {
    return this.http.post<KeyPair>('/api/server/keypair', {});
  }

  applyServerConfig(): Observable<void> {
    return this.http.post<void>('/api/server/apply', {});
  }

  serverServiceControl(action: 'start' | 'stop' | 'restart'): Observable<void> {
    return this.http.post<void>('/api/server/service/' + action, {});
  }

  getSettings(): Observable<GlobalSettings> {
    return this.http.get<GlobalSettings>('/api/settings');
  }

  updateSettings(data: SettingsUpdate): Observable<GlobalSettings> {
    return this.http.patch<GlobalSettings>('/api/settings', data);
  }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>('/api/users');
  }

  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>('/api/users/utils/roles');
  }

  createUser(data: UserCreate): Observable<User> {
    return this.http.post<User>('/api/users', data);
  }

  updateUser(id: number, data: UserUpdate): Observable<User> {
    return this.http.patch<User>('/api/users/' + id, data);
  }

  deleteUser(id: number): Observable<void> {
    return this.http.delete<void>('/api/users/' + id);
  }

  changePassword(current_password: string, new_password: string): Observable<void> {
    return this.http.post<void>('/api/auth/change-password', {
      current_password,
      new_password,
    });
  }

  getLatestGithubRelease(repo: string): Observable<GithubRelease> {
    return this.http.get<GithubRelease>(
      `https://api.github.com/repos/${repo}/releases/latest`
    );
  }

  getOidcSettings(): Observable<OidcAdminSettings> {
    return this.http.get<OidcAdminSettings>("/api/oidc/settings");
  }

  updateOidcSettings(data: OidcAdminSettings): Observable<OidcAdminSettings> {
    return this.http.put<OidcAdminSettings>("/api/oidc/settings", data);
  }

  getOidcPublicConfig(): Observable<OidcPublicConfig> {
    return this.http.get<OidcPublicConfig>("/api/oidc/config");
  }

  oidcCallback(code: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>("/api/oidc/callback", { code });
  }
}

@Injectable({ providedIn: 'root' })
export class ClientsService {
  private readonly api = inject(ApiService);

  list(): Observable<WireGuardClient[]> {
    return this.api.getClients();
  }

  create(data: ClientCreate): Observable<WireGuardClient> {
    return this.api.createClient(data);
  }

  update(id: number, data: ClientUpdate): Observable<WireGuardClient> {
    return this.api.updateClient(id, data);
  }

  delete(id: number): Observable<void> {
    return this.api.deleteClient(id);
  }

  getConfig(id: number): Observable<ClientConfig> {
    return this.api.getClientConfig(id);
  }
}

@Injectable({ providedIn: 'root' })
export class ServerService {
  private readonly api = inject(ApiService);

  get(): Observable<WireGuardServer> {
    return this.api.getServer();
  }

  upsert(data: ServerCreate): Observable<WireGuardServer> {
    return this.api.upsertServer(data);
  }

  generateKeypair(): Observable<KeyPair> {
    return this.api.generateServerKeypair();
  }

  applyConfig(): Observable<void> {
    return this.api.applyServerConfig();
  }

  controlService(action: 'start' | 'stop' | 'restart'): Observable<void> {
    return this.api.serverServiceControl(action);
  }
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly api = inject(ApiService);

  get(): Observable<GlobalSettings> {
    return this.api.getSettings();
  }

  update(data: SettingsUpdate): Observable<GlobalSettings> {
    return this.api.updateSettings(data);
  }
}

@Injectable({ providedIn: 'root' })
export class UsersService {
  private readonly api = inject(ApiService);

  list(): Observable<User[]> {
    return this.api.getUsers();
  }

  getRoles(): Observable<Role[]> {
    return this.api.getRoles();
  }

  create(data: UserCreate): Observable<User> {
    return this.api.createUser(data);
  }

  update(id: number, data: UserUpdate): Observable<User> {
    return this.api.updateUser(id, data);
  }

  delete(id: number): Observable<void> {
    return this.api.deleteUser(id);
  }
}
