import {
  ChangeDetectionStrategy,
  Component,
  inject,
  OnInit,
  signal,
} from "@angular/core";
import {
  form,
  FormField,
  maxLength,
  required,
  submit,
} from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { FormExtraFieldsComponent } from "../../core/applets/form-extra-fields.component";
import { OidcService } from "../../core/services/oidc.service";
import { OidcAdminSettings } from "../../shared/models/api.models";

const OIDC_DEFAULTS: OidcAdminSettings = {
  enabled: false,
  issuer: "",
  client_id: "",
  client_secret: "",
  redirect_uri: "",
  post_logout_redirect_uri: "",
  response_type: "code",
  scope: "openid profile email",
};

@Component({
  selector: "app-oidc",
  standalone: true,
  imports: [FormField, FormExtraFieldsComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./oidc.component.html",
  styleUrl: "./oidc.component.css",
})
export class OidcComponent implements OnInit {
  private readonly oidc = inject(OidcService);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly submitted = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly oidcSignal = signal<OidcAdminSettings>({ ...OIDC_DEFAULTS });
  readonly oidcForm = form(this.oidcSignal, (p) => {
    required(p.issuer, { message: "The issuer is required" });
    required(p.client_id);
    required(p.client_secret);
    required(p.redirect_uri);
    required(p.response_type);
    required(p.scope);
    maxLength(p.issuer, 512);
    maxLength(p.client_id, 255);
    maxLength(p.client_secret, 512);
    maxLength(p.redirect_uri, 512);
    maxLength(p.post_logout_redirect_uri, 512);
    maxLength(p.response_type, 50);
    maxLength(p.scope, 255);
  });

  ngOnInit(): void {
    this.oidc.getAdminSettings().subscribe({
      next: (settings) => {
        this.oidcSignal.set({
          enabled: settings.enabled ?? OIDC_DEFAULTS.enabled,
          issuer: settings.issuer ?? OIDC_DEFAULTS.issuer,
          client_id: settings.client_id ?? OIDC_DEFAULTS.client_id,
          client_secret: settings.client_secret ?? OIDC_DEFAULTS.client_secret,
          redirect_uri: settings.redirect_uri ?? OIDC_DEFAULTS.redirect_uri,
          post_logout_redirect_uri:
            settings.post_logout_redirect_uri ??
            OIDC_DEFAULTS.post_logout_redirect_uri,
          response_type: settings.response_type ?? OIDC_DEFAULTS.response_type,
          scope: settings.scope ?? OIDC_DEFAULTS.scope,
        });
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? "Failed to load OIDC settings");
        this.loading.set(false);
      },
    });
  }

  save(event: Event): void {
    event.preventDefault();
    this.submitted.set(true);
    this.successMessage.set(null);
    this.saveError.set(null);

    submit(this.oidcForm, async (f) => {
      try {
        await firstValueFrom(this.oidc.saveAdminSettings(f().value()));
        this.successMessage.set("OIDC settings saved successfully");
      } catch (err: unknown) {
        this.error.set("Failed to save OIDC settings");
      }
    });
  }
}
