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
  max,
  min,
  required,
  submit,
} from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { SmtpService } from "../../core/services/api.service";
import { SmtpSettings } from "../../shared/models/api.models";

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
  readonly error = signal<string | null>(null);
  readonly recipient = signal("Test mail sending.");
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  smtp = {
    smtp_server: "",
    smtp_port: 25,
    smtp_username: "",
    smtp_password: "",
    smtp_from: "no-reply@wireguard.local",
    smtp_from_name: "WireGuardUI",
    smtp_tls: true,
    smtp_ssl: false,
    smtp_verify: true,
  };
  readonly smtpSignal = signal({ ...this.smtp });
  readonly smtpForm = form(this.smtpSignal, (p) => {
    required(p.smtp_server);
    required(p.smtp_port);
    min(p.smtp_port, 1);
    max(p.smtp_port, 65535);
  });

  ngOnInit(): void {
    this.loadSmtp();
  }

  loadSmtp(): void {
    this.loading.set(true);
    this.smtpService.get().subscribe({
      next: (smtp: SmtpSettings) => {
        this.smtpSignal.set({
          smtp_server: smtp.smtp_server ?? "",
          smtp_port: smtp.smtp_port ?? 25,
          smtp_username: smtp.smtp_username ?? "",
          smtp_password: "",
          smtp_tls: smtp.smtp_tls,
          smtp_ssl: smtp.smtp_ssl,
          smtp_verify: smtp.smtp_verify,
          smtp_from: smtp.smtp_from ?? "",
          smtp_from_name: smtp.smtp_from_name ?? "",
        });
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status !== 404) {
          this.error.set(
            err?.error?.detail ?? "Failed to load server configuration",
          );
        }
        this.loading.set(false);
      },
    });
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    this.loading.set(true);
    this.error.set("");

    submit(this.smtpForm, async (f) => {
      try {
        await firstValueFrom(this.smtpService.update(f().value()));
        f().reset({ ...this.smtp });
      } catch (err: unknown) {
        const httpErr = err as { error?: { detail?: string } };
        this.error.set(httpErr.error?.detail ?? "SMTP recording failed");
      } finally {
        this.loading.set(false);
      }
    });
  }

  controlService(action: "test"): void {
    this.smtpService.test(this.recipient()).subscribe({
      next: () => this.successMessage.set(`Service ${action}ed successfully`),
      error: (err) =>
        this.saveError.set(err?.error?.detail ?? `Failed to ${action} service`),
    });
  }

  cleanConfig(): void {
    this.smtpService.delete(this.smtpSignal()).subscribe({
      next: () => this.successMessage.set("Delete successfully"),
      error: (err) =>
        this.saveError.set(
          err?.error?.detail ?? "Failed to delete configuration",
        ),
    });
  }
}
