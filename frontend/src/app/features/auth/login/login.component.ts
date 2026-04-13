/**
 * Login page component.
 * Uses Angular signal-based forms (FormGroup from @angular/forms with signals).
 */

import { Component, inject, OnInit, signal } from "@angular/core";
import { form, FormField, FormRoot, min, required } from "@angular/forms/signals";
import { Router } from "@angular/router";
import { firstValueFrom } from "rxjs";
import { ErrorField } from "../../../core/applets/error-field.component";
import { FormExtraFields } from "../../../core/applets/form-extra-fields.component";
import { OidcService } from "../../../core/services/api.service";
import { AuthService } from "../../../core/services/auth.service";
import { ThemeMode, ThemeService } from "../../../core/services/theme.service";
import { ApiError } from "../../../shared/models/api-error.model";
import { OidcPublicConfig } from "../../../shared/models/api.models";

@Component({
  selector: "app-login",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField],
  templateUrl: "./login.component.html",
  styleUrl: "./login.component.css",
})
export class LoginComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly oidc = inject(OidcService);
  readonly theme = inject(ThemeService);
  private readonly router = inject(Router);

  readonly isLoading = signal(false);
  readonly isOidcLoading = signal(false);
  readonly error = signal<ApiError | null>(null);
  readonly oidcConfig = signal<OidcPublicConfig | null>(null);

  private readonly loginInit = {
    username: "",
    password: "",
  };
  readonly loginModel = signal({ ...this.loginInit });
  readonly loginForm = form(
    this.loginModel,
    (f) => {
      required(f.username, { message: "Username is required" });
      required(f.password, { message: "Password is required" });
      min(f.username, 3, { message: "Username must be at least 3 characters" });
      min(f.password, 1, { message: "Password must be at least 1 character" });
    },
    {
      submission: {
        action: async (f) => this.onSubmit(f),
      },
    },
  );

  ngOnInit(): void {
    this.oidc.getPublicConfig().subscribe({
      next: (config) => this.oidcConfig.set(config),
      error: () => this.oidcConfig.set(null),
    });
  }

  async onSubmit(loginForm: any): Promise<void> {
    this.isLoading.set(true);
    this.error.set(null);

    const formData = loginForm().value();

    try {
      await firstValueFrom(this.auth.login(formData.username, formData.password));
      this.router.navigate(["/"]);
    } catch (err: unknown) {
      this.error.set({
        code: "login",
        message:
          (err as ApiError).code === "UNAUTHORIZED"
            ? "Invalid username or password"
            : "Connection error. Please try again.",
      } as ApiError);
      this.isLoading.set(false);
    }
  }

  startOidcLogin(): void {
    const config = this.oidcConfig();
    if (!config || !config.enabled || !config.authorization_endpoint) {
      return;
    }

    this.isOidcLoading.set(true);
    const state = crypto.randomUUID();
    sessionStorage.setItem("oidc_state", state);

    const params = new URLSearchParams({
      response_type: config.response_type || "code",
      client_id: config.client_id,
      redirect_uri: config.redirect_uri,
      scope: config.scope || "openid profile email",
      state,
    });
    window.location.href = `${config.authorization_endpoint}?${params.toString()}`;
  }

  changeThemeMode(value: string): void {
    if (value === "auto" || value === "light" || value === "dark") {
      this.theme.setMode(value as ThemeMode);
    }
  }
}
