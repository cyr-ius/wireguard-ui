import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  OnInit,
  signal,
} from "@angular/core";
import { FormBuilder, ReactiveFormsModule, Validators } from "@angular/forms";
import { ClientsService } from "../../core/services/api.service";
import {
  ClientCreate,
  ClientUpdate,
  WireGuardClient,
} from "../../shared/models/api.models";

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
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./clients.component.html",
  styleUrls: ["./clients.component.css"],
})
export class ClientsComponent implements OnInit {
  private readonly clientsService = inject(ClientsService);
  private readonly fb = inject(FormBuilder);

  // ── Available language options for email ──────────────────────────────────
  readonly emailLanguages = EMAIL_LANGUAGES;

  // ── Data signals ──────────────────────────────────────────────────────────
  readonly clients = signal<WireGuardClient[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly saving = signal(false);
  readonly formError = signal<string | null>(null);

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
  readonly emailError = signal<string | null>(null);
  readonly selectedEmailLang = signal<string>("en");

  // ── IP suggestion signal ──────────────────────────────────────────────────
  readonly suggestedIp = signal<string | null>(null);

  // ── Computed values ───────────────────────────────────────────────────────
  readonly filteredClients = computed(() => this.clients());
  readonly enabledCount = computed(
    () => this.clients().filter((c) => c.enabled).length,
  );

  // ── Client creation form ──────────────────────────────────────────────────
  readonly clientForm = this.fb.group({
    name: ["", [Validators.required, Validators.minLength(1)]],
    email: ["", [Validators.required, Validators.email]],
    allocated_ips: ["", [Validators.required]],
    allowed_ips: ["0.0.0.0/0", [Validators.required]],
    use_server_dns: [true],
    enabled: [true],
    preshared_key: [""],
    send_email: [false],
    email_language: ["en"],
  });

  ngOnInit(): void {
    this.loadClients();
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
        this.error.set(err?.error?.detail ?? "Failed to load clients");
        this.loading.set(false);
      },
    });
  }

  /** Open the creation modal and pre-fill the suggested IP */
  openCreateModal(): void {
    this.clientForm.reset({
      allowed_ips: "0.0.0.0/0",
      use_server_dns: true,
      enabled: true,
      send_email: false,
      email_language: "en",
    });
    this.formError.set(null);
    this.modalMode.set("create");

    // Fetch the suggested IP from the server
    this.clientsService.suggestIp().subscribe({
      next: (response) => {
        if (response.suggested_ip) {
          this.suggestedIp.set(response.suggested_ip);
          this.clientForm.patchValue({ allocated_ips: response.suggested_ip });
        }
      },
      error: () => {
        // Non-critical: just skip IP suggestion if it fails
        this.suggestedIp.set(null);
      },
    });
  }

  openEditModal(client: WireGuardClient): void {
    this.selectedClient.set(client);
    this.clientForm.patchValue({
      name: client.name,
      email: client.email,
      allocated_ips: client.allocated_ips,
      allowed_ips: client.allowed_ips,
      use_server_dns: client.use_server_dns,
      enabled: client.enabled,
      preshared_key: client.preshared_key ?? "",
      send_email: false,
      email_language: "en",
    });
    this.formError.set(null);
    this.modalMode.set("edit");
  }

  closeModal(): void {
    this.modalMode.set(null);
    this.selectedClient.set(null);
    this.formError.set(null);
    this.suggestedIp.set(null);
  }

  saveClient(): void {
    if (this.clientForm.invalid || this.saving()) return;

    this.saving.set(true);
    this.formError.set(null);

    const value = this.clientForm.value;
    const mode = this.modalMode();

    if (mode === "create") {
      const createData: ClientCreate = {
        name: value.name!,
        email: value.email!,
        allocated_ips: value.allocated_ips!,
        allowed_ips: value.allowed_ips!,
        use_server_dns: value.use_server_dns ?? true,
        enabled: value.enabled ?? true,
        preshared_key: value.preshared_key || "",
        send_email: value.send_email ?? false,
        email_language: value.email_language ?? "en",
      };

      this.clientsService.create(createData).subscribe({
        next: () => {
          this.saving.set(false);
          this.closeModal();
          this.loadClients();
        },
        error: (err) => {
          this.saving.set(false);
          this.formError.set(err?.error?.detail ?? "Failed to create client");
        },
      });
    } else if (mode === "edit") {
      const clientId = this.selectedClient()!.id;
      const updateData: ClientUpdate = {
        name: value.name ?? undefined,
        email: value.email ?? undefined,
        allocated_ips: value.allocated_ips ?? undefined,
        allowed_ips: value.allowed_ips ?? undefined,
        use_server_dns: value.use_server_dns ?? undefined,
        enabled: value.enabled ?? undefined,
        preshared_key: value.preshared_key ?? undefined,
      };

      this.clientsService.update(clientId, updateData).subscribe({
        next: () => {
          this.saving.set(false);
          this.closeModal();
          this.loadClients();
        },
        error: (err) => {
          this.saving.set(false);
          this.formError.set(err?.error?.detail ?? "Failed to update client");
        },
      });
    }
  }

  toggleEnabled(client: WireGuardClient): void {
    this.clientsService
      .update(client.id, { enabled: !client.enabled })
      .subscribe({ next: () => this.loadClients() });
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
      error: (err) =>
        this.error.set(err?.error?.detail ?? "Failed to delete client"),
    });
  }

  // ── Config viewer ─────────────────────────────────────────────────────────

  viewConfig(client: WireGuardClient): void {
    this.clientsService.getConfig(client.id, false).subscribe({
      next: (data) => {
        this.configContent.set(data.config);
        this.showConfig.set(true);
      },
      error: (err) =>
        this.error.set(err?.error?.detail ?? "Failed to load configuration"),
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
        this.error.set(err?.error?.detail ?? "Failed to generate QR code");
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
    this.selectedEmailLang.set("en");
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

    this.clientsService
      .sendEmail(client.id, this.selectedEmailLang())
      .subscribe({
        next: () => {
          this.sendingEmail.set(false);
          this.emailSuccess.set(`Email successfully sent to ${client.email}`);
          setTimeout(() => this.closeEmailModal(), 2500);
        },
        error: (err) => {
          this.sendingEmail.set(false);
          this.emailError.set(
            err?.error?.detail ??
              "Failed to send email. Check SMTP configuration.",
          );
        },
      });
  }

  isInvalid(field: string): boolean {
    const control = this.clientForm.get(field);
    return !!(control?.invalid && control?.touched);
  }
}
