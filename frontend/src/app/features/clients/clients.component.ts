import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from "@angular/core";
import { email, form, FormField, FormRoot, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { ErrorField } from "../../core/applets/error-field.component";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { ClientsService, SmtpService } from "../../core/services/api.service";
import { ApiError } from "../../shared/models/api-error.model";
import { ClientCreate, ClientUpdate, WireGuardClient } from "../../shared/models/api.models";

/** Modal display modes */
type ModalMode = "create" | "edit" | null;

/** Email language options */
const EMAIL_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "fr", label: "Français" },
  { code: "es", label: "Español" },
] as const;

@Component({
  selector: "app-clients",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./clients.component.html",
  styleUrls: ["./clients.component.css"],
})
export class ClientsComponent implements OnInit {
  private readonly clientsService = inject(ClientsService);
  private readonly smtpService = inject(SmtpService);

  // ── Available language options for email ──────────────────────────────────
  readonly emailLanguages = EMAIL_LANGUAGES;

  // ── Data signals ──────────────────────────────────────────────────────────
  readonly clients = signal<WireGuardClient[]>([]);
  readonly loading = signal(true);
  readonly error = signal<ApiError | null>(null);
  readonly formError = signal<ApiError | null>(null);

  // ── Modal state signals ───────────────────────────────────────────────────
  readonly modalMode = signal<ModalMode>(null);
  readonly selectedClient = signal<WireGuardClient | null>(null);
  readonly deleteTarget = signal<WireGuardClient | null>(null);

  // ── QR code modal signals ─────────────────────────────────────────────────
  readonly qrClient = signal<WireGuardClient | null>(null);
  readonly qrCodeBase64 = signal<string | null>(null);
  readonly qrLoading = signal(false);

  // ── Config viewer signals ─────────────────────────────────────────────────
  readonly configContent = signal<string | null>(null);
  readonly showConfig = signal(false);

  // ── Email sending modal signals ───────────────────────────────────────────
  readonly emailTarget = signal<WireGuardClient | null>(null);
  readonly sendingEmail = signal(false);
  readonly emailSuccess = signal<string | null>(null);
  readonly emailError = signal<ApiError | null>(null);
  readonly selectedEmailLang = signal<string>("en");
  readonly defaultEmailLanguage = signal<string>("en");

  // ── IP suggestion signal ──────────────────────────────────────────────────
  readonly suggestedIp = signal<string | null>(null);

  // ── Computed values ───────────────────────────────────────────────────────
  readonly filteredClients = computed(() => this.clients());
  readonly enabledCount = computed(() => this.clients().filter((c) => c.enabled).length);

  // ── Client creation form ──────────────────────────────────────────────────
  readonly clientInit = {
    name: "",
    email: "",
    allocated_ips: "",
    allowed_ips: "0.0.0.0/0",
    use_server_dns: true,
    enabled: true,
    preshared_key: "",
    send_email: false,
    email_language: "en",
  };
  readonly clientModel = signal({ ...this.clientInit });
  readonly clientForm = form(
    this.clientModel,
    (f) => {
      required(f.name, { message: "The name is required" });
      required(f.email, { message: "The email is required" });
      required(f.allocated_ips, { message: "Allocated ips are required" });
      required(f.allowed_ips, { message: "Allowed ips are required" });
      required(f.email_language);
      email(f.email, { message: "Invalid email address" });
    },
    {
      submission: {
        action: async (f) => this.saveClient(f),
      },
    },
  );

  ngOnInit(): void {
    this.loadClients();
    this.loadDefaultEmailLanguage();
  }

  loadDefaultEmailLanguage(): void {
    this.smtpService.get().subscribe({
      next: (settings) => {
        const language = settings.default_email_language ?? "en";
        this.defaultEmailLanguage.set(language);
        this.selectedEmailLang.set(language);
      },
      error: () => {
        this.defaultEmailLanguage.set("en");
      },
    });
  }

  loadClients(): void {
    this.loading.set(true);
    this.error.set(null);

    this.clientsService.list().subscribe({
      next: (clients) => {
        this.clients.set(clients);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set((err as ApiError) ?? "Failed to load clients");
        this.loading.set(false);
      },
    });
  }

  /** Open the creation modal and pre-fill the suggested IP */
  openCreateModal(): void {
    this.clientForm().reset({ ...this.clientInit });
    this.formError.set(null);
    this.modalMode.set("create");

    // Fetch the suggested IP from the server
    this.getSuggestIp();
  }

  getSuggestIp(): void {
    this.clientsService.suggestIp().subscribe({
      next: (response) => {
        if (response.suggested_ip) {
          this.suggestedIp.set(response.suggested_ip);
          this.clientForm.allocated_ips().value.set(response.suggested_ip);
        }
      },
      error: () => {
        this.suggestedIp.set(null);
      },
    });
  }

  openEditModal(client: any): void {
    this.selectedClient.set(client);
    client.email_language = client.email_language || this.defaultEmailLanguage();
    this.clientModel.set({ ...client });
    this.formError.set(null);
    this.modalMode.set("edit");
  }

  closeModal(): void {
    this.modalMode.set(null);
    this.selectedClient.set(null);
    this.formError.set(null);
    this.suggestedIp.set(null);
  }

  async saveClient(f: any): Promise<void> {
    this.formError.set(null);

    const formData = f().value();
    const mode = this.modalMode();

    try {
      if (mode === "create") {
        const createData: ClientCreate = {
          ...formData,
          email_language: formData.email_language ?? this.defaultEmailLanguage(),
        };
        await firstValueFrom(this.clientsService.create(createData));
        this.closeModal();
        this.loadClients();
      } else if (mode === "edit") {
        const clientId = this.selectedClient()!.id;
        await firstValueFrom(this.clientsService.update(clientId, formData as ClientUpdate));
        this.closeModal();
        this.loadClients();
      } else {
        this.formError.set({ code: "state", message: "Invalid form state" } as ApiError);
      }
    } catch (err: unknown) {
      const errMsg = (err instanceof HttpErrorResponse && err.error.detail) || `Failed to ${mode} client`;
      this.formError.set(errMsg);
    }
  }

  toggleEnabled(client: WireGuardClient): void {
    this.clientsService.update(client.id, { enabled: !client.enabled }).subscribe({ next: () => this.loadClients() });
  }

  openDeleteConfirm(client: WireGuardClient): void {
    this.deleteTarget.set(client);
  }

  confirmDelete(): void {
    const target = this.deleteTarget();
    if (!target) return;

    this.clientsService.delete(target.id).subscribe({
      next: () => {
        this.deleteTarget.set(null);
        this.loadClients();
      },
      error: (err) => this.error.set((err as ApiError) ?? "Failed to delete client"),
    });
  }

  // ── Config viewer ─────────────────────────────────────────────────────────

  viewConfig(client: WireGuardClient): void {
    this.clientsService.getConfig(client.id, false).subscribe({
      next: (data) => {
        this.configContent.set(data.config);
        this.showConfig.set(true);
      },
      error: (err) => this.error.set((err as ApiError) ?? "Failed to load configuration"),
    });
  }

  downloadConfig(client: WireGuardClient): void {
    this.clientsService.getConfig(client.id, false).subscribe({
      next: (data) => {
        const blob = new Blob([data.config], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${client.name}.conf`;
        a.click();
        URL.revokeObjectURL(url);
      },
    });
  }

  closeConfig(): void {
    this.showConfig.set(false);
    this.configContent.set(null);
  }

  // ── QR Code modal ─────────────────────────────────────────────────────────

  openQrModal(client: WireGuardClient): void {
    this.qrClient.set(client);
    this.qrCodeBase64.set(null);
    this.qrLoading.set(true);

    this.clientsService.getConfig(client.id, true).subscribe({
      next: (data) => {
        this.qrCodeBase64.set(data.qr_code_base64 ?? null);
        this.qrLoading.set(false);
      },
      error: (err) => {
        this.error.set((err as ApiError) ?? "Failed to generate QR code");
        this.qrLoading.set(false);
        this.qrClient.set(null);
      },
    });
  }

  closeQrModal(): void {
    this.qrClient.set(null);
    this.qrCodeBase64.set(null);
    this.qrLoading.set(false);
  }

  downloadQrCode(): void {
    const qr = this.qrCodeBase64();
    const client = this.qrClient();
    if (!qr || !client) return;

    const link = document.createElement("a");
    link.href = `data:image/png;base64,${qr}`;
    link.download = `${client.name}-qrcode.png`;
    link.click();
  }

  // ── Email sending modal ───────────────────────────────────────────────────

  openEmailModal(client: WireGuardClient): void {
    this.emailTarget.set(client);
    this.emailSuccess.set(null);
    this.emailError.set(null);
    this.selectedEmailLang.set(this.defaultEmailLanguage());
  }

  closeEmailModal(): void {
    this.emailTarget.set(null);
    this.emailSuccess.set(null);
    this.emailError.set(null);
    this.sendingEmail.set(false);
  }

  sendEmail(): void {
    const client = this.emailTarget();
    if (!client || this.sendingEmail()) return;

    this.sendingEmail.set(true);
    this.emailSuccess.set(null);
    this.emailError.set(null);

    this.clientsService.sendEmail(client.id, this.selectedEmailLang()).subscribe({
      next: () => {
        this.sendingEmail.set(false);
        this.emailSuccess.set(`Email successfully sent to ${client.email}`);
        setTimeout(() => this.closeEmailModal(), 2500);
      },
      error: (err) => {
        this.sendingEmail.set(false);
        this.emailError.set((err as ApiError) ?? "Failed to send email. Check SMTP configuration.");
      },
    });
  }
}
