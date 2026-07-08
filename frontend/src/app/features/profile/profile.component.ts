import { ChangeDetectionStrategy, Component, computed, inject, signal } from "@angular/core";
import { form, FormField, FormRoot, minLength, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { ErrorField } from "../../core/applets/error-field.component";
import { ApiError } from "../../core/models/api-error.model";
import { ApiService } from "../../core/services/api.service";
import { AuthService } from "../../core/services/auth.service";

@Component({
  selector: "app-profile",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./profile.component.html",
  styleUrls: ["./profile.component.css"],
})
export class ProfileComponent {
  private readonly api = inject(ApiService);
  private readonly authService = inject(AuthService);

  readonly error = signal<ApiError | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly username = computed(() => this.authService.username());
  readonly role = computed(() => (this.authService.isAdmin() ? "Administrator" : "User"));

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
