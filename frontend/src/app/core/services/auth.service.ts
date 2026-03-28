/**
 * Authentication service using Angular signals.
 * Stores the current user state reactively.
 * All role checks are mirrored from backend enforcement.
 */

import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: {
    username: string;
    roles: Array<{ name: string }>;
  };
}

export interface CurrentUser {
  username: string;
  role: 'admin' | 'user';
  token: string;
}

const STORAGE_KEY = 'wg_auth';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  // Reactive state
  private readonly _currentUser = signal<CurrentUser | null>(this._loadFromStorage());

  // Public computed signals
  readonly currentUser = this._currentUser.asReadonly();
  readonly isAuthenticated = computed(() => this._currentUser() !== null);
  readonly isAdmin = computed(() => this._currentUser()?.role === 'admin');
  readonly username = computed(() => this._currentUser()?.username ?? '');

  /** Login: exchange credentials for JWT token. */
  login(username: string, password: string) {
    return this.http
      .post<TokenResponse>('/api/auth/login', { username, password })
      .pipe(tap((response) => this.applyTokenResponse(response)));
  }

  loginWithTokenResponse(response: TokenResponse): void {
    this.applyTokenResponse(response);
  }

  /** Logout: clear state and redirect to login. */
  logout(): void {
    this._currentUser.set(null);
    sessionStorage.removeItem(STORAGE_KEY);
    this.router.navigate(['/login']);
  }

  /** Get the raw JWT token for use in HTTP interceptor. */
  getToken(): string | null {
    return this._currentUser()?.token ?? null;
  }

  private _loadFromStorage(): CurrentUser | null {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as CurrentUser) : null;
    } catch {
      return null;
    }
  }

  private applyTokenResponse(response: TokenResponse): void {
    const isAdmin = response.user.roles?.some((r) => r.name === 'admin') ?? false;
    const user: CurrentUser = {
      username: response.user.username,
      role: isAdmin ? 'admin' : 'user',
      token: response.access_token,
    };
    this._currentUser.set(user);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  }
}
