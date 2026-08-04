import { DatePipe } from "@angular/common";
import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from "@angular/core";
import { form, FormField, FormRoot, minLength, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { ErrorField } from "../../core/applets/error-field.component";
import { ApiError } from "../../core/models/api-error.model";
import { Pat, PatDuration } from "../../core/models/api.models";
import { ApiService, PatService } from "../../core/services/api.service";
import { AuthService } from "../../core/services/auth.service";

@Component({
  selector: "app-profile",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./profile.component.html",
  styleUrls: ["./profile.component.css"],
})
export class ProfileComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly patService = inject(PatService);
  private readonly authService = inject(AuthService);

  readonly error = signal<ApiError | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly username = computed(() => this.authService.username());
  readonly role = computed(() => (this.authService.isAdmin() ? "Administrator" : "User"));
  readonly isOidc = computed(() => this.authService.isOidc());

  // ── Personal Access Tokens ───────────────────────────────────────────────

  readonly apiKeysEnabled = signal(false);
  readonly tokens = signal<Pat[]>([]);
  readonly tokensError = signal<ApiError | null>(null);
  readonly showCreateModal = signal(false);
  readonly newTokenName = signal("");
  readonly newTokenDuration = signal<PatDuration>("30d");
  readonly createdToken = signal<string | null>(null);
  readonly revokeTarget = signal<Pat | null>(null);

  ngOnInit(): void {
    this.api.getAppConfig().subscribe({
      next: (config) => {
        this.apiKeysEnabled.set(config.api_keys_enabled);
        if (config.api_keys_enabled) {
          this.loadTokens();
        }
      },
      error: () => this.apiKeysEnabled.set(false),
    });
  }

  loadTokens(): void {
    this.patService.list().subscribe({
      next: (tokens) => this.tokens.set(tokens),
      error: (err) => this.tokensError.set((err as ApiError) ?? { code: "UNKNOWN", message: "Failed to load tokens" }),
    });
  }

  openCreateTokenModal(): void {
    this.newTokenName.set("");
    this.newTokenDuration.set("30d");
    this.tokensError.set(null);
    this.showCreateModal.set(true);
  }

  closeCreateTokenModal(): void {
    this.showCreateModal.set(false);
  }

  async createToken(): Promise<void> {
    this.tokensError.set(null);
    const name = this.newTokenName().trim();
    if (!name) {
      this.tokensError.set({ code: "REQUIRED", message: "Token name is required" });
      return;
    }
    try {
      const result = await firstValueFrom(
        this.patService.create({ name, duration: this.newTokenDuration() }),
      );
      this.showCreateModal.set(false);
      this.createdToken.set(result.token);
      this.loadTokens();
    } catch (err: unknown) {
      this.tokensError.set((err as ApiError) ?? { code: "UNKNOWN", message: "Failed to create token" });
    }
  }

  dismissCreatedToken(): void {
    this.createdToken.set(null);
  }

  confirmRevokeToken(): void {
    const target = this.revokeTarget();
    if (!target) return;
    this.patService.revoke(target.id).subscribe({
      next: () => {
        this.revokeTarget.set(null);
        this.loadTokens();
      },
      error: (err: unknown) => this.tokensError.set((err as ApiError) ?? { code: "UNKNOWN", message: "Failed to revoke token" }),
    });
  }

  private readonly formInit = {
    current_password: "",
    new_password: "",
    confirm_password: "",
  };
  readonly passwordModel = signal({ ...this.formInit });
  readonly passwordForm = form(
    this.passwordModel,
    (p) => {
      required(p.current_password, { message: "Current password is required" });
      required(p.new_password, { message: "New password is required" });
      minLength(p.new_password, 8, { message: "String should have at least 8 characters" });
      required(p.confirm_password, { message: "Please confirm the new password" });
    },
    {
      submission: {
        action: async () => this.changePassword(),
      },
    },
  );

  async changePassword(): Promise<void> {
    this.error.set(null);
    this.successMessage.set(null);

    const { current_password, new_password, confirm_password } = this.passwordModel();

    if (new_password !== confirm_password) {
      this.error.set({ code: "MISMATCH", message: "New password and confirmation do not match" });
      return;
    }

    try {
      await firstValueFrom(this.api.changePassword(current_password, new_password));
      this.passwordForm().reset({ ...this.formInit });
      this.successMessage.set("Password changed successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.error.set((err as ApiError) ?? { code: "UNKNOWN", message: "Failed to change password" });
    }
  }
}
