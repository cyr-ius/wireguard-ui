import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  OnInit,
  signal,
} from "@angular/core";
import { form, FormField, max, min, required, submit } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { SmtpService } from "../../core/services/api.service";
import { SmtpSettings, SmtpSettingsUpdate } from "../../shared/models/api.models";

const SMTP_DEFAULTS = {
  smtp_server: "",
  smtp_port: 25,
  smtp_username: "",
  smtp_password: "",
  smtp_from: "",
  smtp_from_name: "WireGuard UI",
  smtp_tls: true,
  smtp_ssl: false,
  smtp_verify: true,
  default_email_language: "en",
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type SmtpField =
  | "smtp_server"
  | "smtp_port"
  | "smtp_from"
  | "default_email_language";

@Component({
  selector: "app-smtp",
  standalone: true,
  imports: [FormField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./smtp.component.html",
  styleUrls: ["./smtp.component.css"],
})
export class SmtpComponent implements OnInit {
  private readonly smtpService = inject(SmtpService);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly resetting = signal(false);
  readonly submitted = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly showTestModal = signal(false);
  readonly testRecipient = signal("");
  readonly testRecipientError = signal<string | null>(null);
  readonly testError = signal<string | null>(null);
  readonly testing = signal(false);
  readonly testSubject = signal("WireGuard UI - SMTP Test Email");
  readonly previewFrom = computed(
    () => this.smtpSignal().smtp_from || this.smtpSignal().smtp_username || "sender@example.com",
  );
  readonly previewFromName = computed(
    () => this.smtpSignal().smtp_from_name || SMTP_DEFAULTS.smtp_from_name,
  );

  readonly smtpSignal = signal({ ...SMTP_DEFAULTS });
  readonly smtpForm = form(this.smtpSignal, (p) => {
    required(p.smtp_server);
    required(p.smtp_port);
    min(p.smtp_port, 1);
    max(p.smtp_port, 65535);
    required(p.default_email_language);
  });

  ngOnInit(): void {
    this.loadSmtp();
  }

  loadSmtp(): void {
    this.loading.set(true);
    this.error.set(null);

    this.smtpService.get().subscribe({
      next: (smtp: SmtpSettings) => {
        this.applySmtpSettings(smtp);
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status !== 404) {
          this.error.set(this.extractErrorMessage(err, "Failed to load mail configuration"));
        } else {
          this.resetLocalForm();
        }
        this.loading.set(false);
      },
    });
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    this.submitted.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);

    if (this.hasFormErrors()) {
      this.saveError.set("Please correct the highlighted fields before saving.");
      return;
    }

    this.saving.set(true);

    submit(this.smtpForm, async () => {
      try {
        const saved = await firstValueFrom(this.smtpService.update(this.buildPayload()));
        this.applySmtpSettings(saved);
        this.successMessage.set("Mail settings saved successfully");
        setTimeout(() => this.successMessage.set(null), 4000);
      } catch (err: unknown) {
        this.saveError.set(this.extractErrorMessage(err, "Failed to save mail settings"));
      } finally {
        this.saving.set(false);
      }
    });
  }

  resetConfig(): void {
    if (this.resetting()) return;

    this.resetting.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);
    this.error.set(null);

    this.smtpService.reset().subscribe({
      next: (smtp) => {
        this.applySmtpSettings(smtp);
        this.resetting.set(false);
        this.successMessage.set("Mail settings reset successfully");
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.resetting.set(false);
        this.saveError.set(this.extractErrorMessage(err, "Failed to reset mail settings"));
      },
    });
  }

  openTestModal(): void {
    this.saveError.set(null);
    this.testError.set(null);
    this.testRecipientError.set(null);
    this.testRecipient.set(this.smtpSignal().smtp_username || "");
    this.showTestModal.set(true);
  }

  closeTestModal(): void {
    if (this.testing()) return;

    this.showTestModal.set(false);
    this.testRecipient.set("");
    this.testRecipientError.set(null);
    this.testError.set(null);
  }

  updateTestRecipient(event: Event): void {
    this.testRecipient.set((event.target as HTMLInputElement).value);
    this.testRecipientError.set(null);
    this.testError.set(null);
  }


  onSslToggle(event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    this.smtpSignal.update((smtp) => ({
      ...smtp,
      smtp_ssl: checked,
      smtp_tls: checked ? false : smtp.smtp_tls,
      smtp_port: checked ? 465 : smtp.smtp_port,
    }));
  }

  onStartTlsToggle(event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    this.smtpSignal.update((smtp) => ({
      ...smtp,
      smtp_tls: checked,
      smtp_ssl: checked ? false : smtp.smtp_ssl,
      smtp_port: checked ? 587 : smtp.smtp_port,
    }));
  }

  sendTestEmail(): void {
    const recipient = this.testRecipient().trim();
    this.testRecipientError.set(null);
    this.testError.set(null);
    this.saveError.set(null);

    if (!recipient) {
      this.testRecipientError.set("Recipient email is required.");
      return;
    }

    if (!EMAIL_REGEX.test(recipient)) {
      this.testRecipientError.set("Recipient email format is invalid.");
      return;
    }

    this.testing.set(true);

    this.smtpService.test(recipient).subscribe({
      next: () => {
        this.testing.set(false);
        this.showTestModal.set(false);
        this.successMessage.set(`Test email queued for ${recipient}`);
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.testing.set(false);
        this.testError.set(this.extractErrorMessage(err, "Failed to send test email"));
      },
    });
  }

  isFieldInvalid(field: SmtpField): boolean {
    return this.submitted() && this.getFieldError(field) !== null;
  }

  getFieldError(field: SmtpField): string | null {
    const smtp = this.smtpSignal();

    switch (field) {
      case "smtp_server":
        return smtp.smtp_server.trim() ? null : "SMTP server is required.";
      case "smtp_port":
        return Number.isInteger(smtp.smtp_port) && smtp.smtp_port >= 1 && smtp.smtp_port <= 65535
          ? null
          : "SMTP port must be between 1 and 65535.";
      case "smtp_from":
        if (!smtp.smtp_from.trim()) return null;
        return EMAIL_REGEX.test(smtp.smtp_from.trim())
          ? null
          : "Mail From must be a valid email address.";
      case "default_email_language":
        return ["en", "fr", "es"].includes(smtp.default_email_language)
          ? null
          : "Please select a supported email language.";
      default:
        return null;
    }
  }

  private hasFormErrors(): boolean {
    return ["smtp_server", "smtp_port", "smtp_from", "default_email_language"].some(
      (field) => this.getFieldError(field as SmtpField) !== null,
    );
  }

  private buildPayload(): SmtpSettingsUpdate {
    const smtp = this.smtpSignal();
    return {
      smtp_server: smtp.smtp_server.trim(),
      smtp_port: smtp.smtp_port,
      smtp_username: smtp.smtp_username.trim() || null,
      smtp_password: smtp.smtp_password.trim() || null,
      smtp_from: smtp.smtp_from.trim() || null,
      smtp_from_name: smtp.smtp_from_name.trim() || SMTP_DEFAULTS.smtp_from_name,
      smtp_tls: smtp.smtp_tls,
      smtp_ssl: smtp.smtp_ssl,
      smtp_verify: smtp.smtp_verify,
      default_email_language: smtp.default_email_language,
    };
  }

  private applySmtpSettings(smtp: SmtpSettings): void {
    this.smtpSignal.set({
      smtp_server: smtp.smtp_server ?? "",
      smtp_port: smtp.smtp_port ?? SMTP_DEFAULTS.smtp_port,
      smtp_username: smtp.smtp_username ?? "",
      smtp_password: "",
      smtp_tls: smtp.smtp_tls,
      smtp_ssl: smtp.smtp_ssl,
      smtp_verify: smtp.smtp_verify,
      smtp_from: smtp.smtp_from ?? SMTP_DEFAULTS.smtp_from,
      smtp_from_name: smtp.smtp_from_name ?? SMTP_DEFAULTS.smtp_from_name,
      default_email_language:
        smtp.default_email_language ?? SMTP_DEFAULTS.default_email_language,
    });
    this.submitted.set(false);
    this.testError.set(null);
    this.testRecipientError.set(null);
  }

  private extractErrorMessage(err: unknown, fallback: string): string {
    const httpErr = err as
      | { error?: { detail?: string | string[] | { msg?: string }[] } }
      | undefined;

    const detail = httpErr?.error?.detail;

    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          return item?.msg ?? "Validation error";
        })
        .join(" ");
    }

    return fallback;
  }

  private resetLocalForm(): void {
    this.smtpSignal.set({ ...SMTP_DEFAULTS });
    this.submitted.set(false);
    this.testError.set(null);
    this.testRecipientError.set(null);
  }
}
