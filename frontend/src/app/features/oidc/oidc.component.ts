import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from "@angular/core";
import { FormBuilder, ReactiveFormsModule, Validators } from "@angular/forms";
import { OidcService } from "../../core/services/oidc.service";
import { OidcAdminSettings } from "../../shared/models/api.models";

@Component({
  selector: "app-oidc",
  standalone: true,
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./oidc.component.html",
  styleUrl: "./oidc.component.css",
})
export class OidcComponent implements OnInit {
  private readonly oidc = inject(OidcService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly oidcForm = this.fb.group({
    enabled: [false],
    issuer: ["", [Validators.maxLength(512)]],
    client_id: ["", [Validators.maxLength(255)]],
    client_secret: ["", [Validators.maxLength(512)]],
    redirect_uri: ["", [Validators.maxLength(512)]],
    post_logout_redirect_uri: ["", [Validators.maxLength(512)]],
    response_type: ["code", [Validators.maxLength(50)]],
    scope: ["openid profile email", [Validators.maxLength(255)]],
  });

  ngOnInit(): void {
    this.oidc.getAdminSettings().subscribe({
      next: (settings) => {
        this.oidcForm.patchValue({
          enabled: settings.enabled ?? false,
          issuer: settings.issuer ?? "",
          client_id: settings.client_id ?? "",
          client_secret: settings.client_secret ?? "",
          redirect_uri: settings.redirect_uri ?? "",
          post_logout_redirect_uri: settings.post_logout_redirect_uri ?? "",
          response_type: settings.response_type ?? "code",
          scope: settings.scope ?? "openid profile email",
        });
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? "Failed to load OIDC settings");
        this.loading.set(false);
      },
    });
  }

  save(): void {
    if (this.oidcForm.invalid || this.saving()) return;

    this.saving.set(true);
    this.saveError.set(null);

    const value = this.oidcForm.value as OidcAdminSettings;

    this.oidc.saveAdminSettings(value).subscribe({
      next: () => {
        this.saving.set(false);
        this.successMessage.set("OIDC settings saved successfully");
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.saving.set(false);
        this.saveError.set(err?.error?.detail ?? "Failed to save OIDC settings");
      },
    });
  }
}
