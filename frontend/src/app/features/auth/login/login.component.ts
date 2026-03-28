/**
 * Login page component.
 * Uses Angular signal-based forms (FormGroup from @angular/forms with signals).
 */

import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { OidcService } from '../../../core/services/oidc.service';
import { OidcPublicConfig } from '../../../shared/models/api.models';
import { ThemeMode, ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly oidc = inject(OidcService);
  readonly theme = inject(ThemeService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  readonly loginForm = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', [Validators.required, Validators.minLength(1)]],
  });

  readonly isLoading = signal(false);
  readonly isOidcLoading = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly oidcConfig = signal<OidcPublicConfig | null>(null);

  ngOnInit(): void {
    this.oidc.getPublicConfig().subscribe({
      next: (config) => this.oidcConfig.set(config),
      error: () => this.oidcConfig.set(null),
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) return;

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const { username, password } = this.loginForm.getRawValue();
    this.auth.login(username!, password!).subscribe({
      next: () => this.router.navigate(['/']),
      error: (err) => {
        this.errorMessage.set(
          err.status === 401
            ? 'Invalid username or password'
            : 'Connection error. Please try again.'
        );
        this.isLoading.set(false);
      },
    });
  }

  startOidcLogin(): void {
    const config = this.oidcConfig();
    if (!config || !config.enabled || !config.authorization_endpoint) {
      return;
    }

    this.isOidcLoading.set(true);
    const state = crypto.randomUUID();
    sessionStorage.setItem('oidc_state', state);

    const params = new URLSearchParams({
      response_type: config.response_type || 'code',
      client_id: config.client_id,
      redirect_uri: config.redirect_uri,
      scope: config.scope || 'openid profile email',
      state,
    });
    window.location.href = `${config.authorization_endpoint}?${params.toString()}`;
  }

  changeThemeMode(value: string): void {
    if (value === 'auto' || value === 'light' || value === 'dark') {
      this.theme.setMode(value as ThemeMode);
    }
  }
}
