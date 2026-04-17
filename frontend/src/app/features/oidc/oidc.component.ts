import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from "@angular/core";
import { form, FormField, FormRoot, maxLength, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { ErrorField } from "../../core/applets/error-field.component";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { ApiError } from "../../core/models/api-error.model";
import { OidcAdminSettings } from "../../core/models/api.models";
import { OidcService } from "../../core/services/api.service";

@Component({
  selector: "app-oidc",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./oidc.component.html",
  styleUrl: "./oidc.component.css",
})
export class OidcComponent implements OnInit {
  private readonly oidc = inject(OidcService);

  readonly loading = signal(true);
  readonly resetting = signal(false);
  readonly error = signal<ApiError | null>(null);
  readonly successMessage = signal<string | null>(null);

  private readonly oidcInit: OidcAdminSettings = {
    enabled: false,
    issuer: "",
    client_id: "",
    client_secret: "",
    redirect_uri: "",
    post_logout_redirect_uri: "",
    response_type: "code",
    scope: "openid profile email",
  };

  readonly oidcSignal = signal<OidcAdminSettings>({ ...this.oidcInit });
  readonly oidcForm = form(
    this.oidcSignal,
    (p) => {
      required(p.issuer, { message: "The issuer is required" });
      required(p.client_id, { message: "Client ID is required" });
      required(p.client_secret, { message: "Client Secret is required" });
      required(p.redirect_uri, { message: "Redirect Uri is required" });
      required(p.response_type, { message: "the response type is required" });
      required(p.scope, { message: "Scope is required" });
      maxLength(p.issuer, 512);
      maxLength(p.client_id, 255);
      maxLength(p.client_secret, 512);
      maxLength(p.redirect_uri, 512);
      maxLength(p.post_logout_redirect_uri, 512);
      maxLength(p.response_type, 50);
      maxLength(p.scope, 255);
    },
    {
      submission: {
        action: async (f) => this.save(f),
      },
    },
  );

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.oidc.getAdminSettings().subscribe({
      next: (settings) => {
        this.oidcSignal.set({ ...this.oidcInit, ...settings });
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set((err as ApiError) ?? "Failed to load OIDC settings");
        this.loading.set(false);
      },
    });
  }

  async save(f: any): Promise<void> {
    this.successMessage.set(null);
    this.error.set(null);

    try {
      await firstValueFrom(this.oidc.saveAdminSettings(f().value()));
      this.successMessage.set("OIDC settings saved successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.error.set((err as ApiError) ?? "Failed to save OIDC settings");
    }
  }

  async reset() {
    this.resetting.set(true);
    try {
      await firstValueFrom(this.oidc.resetAdminSettings());
      this.successMessage.set("OIDC settings reset successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
      this.loadData();
    } catch (err: unknown) {
      this.error.set((err as ApiError) ?? "Failed to reset OIDC settings");
    } finally {
      this.resetting.set(false);
    }
  }
}
