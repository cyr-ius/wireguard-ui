import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from "@angular/core";
import { form, FormField, FormRoot, max, min, readonly, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { ErrorField } from "../../core/applets/error-field.component";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { ApiError } from "../../core/models/api-error.model";
import { ApiService, ServerService } from "../../core/services/api.service";

@Component({
  selector: "app-server",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./server.component.html",
  styleUrls: ["./server.component.css"],
})
export class ServerComponent implements OnInit {
  private readonly serverService = inject(ServerService);
  private readonly apiService = inject(ApiService);

  readonly loading = signal(true);
  readonly applying = signal(false);
  readonly resetting = signal(false);
  readonly serviceActionLoading = signal<"start" | "stop" | "restart" | null>(null);
  readonly error = signal<ApiError | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly showPrivateKey = signal(false);
  readonly status = signal(false);

  private readonly serverInit = {
    address: "192.168.1.0/24",
    listen_port: 51820,
    private_key: "",
    public_key: "",
    postup: "EXT_IF=$(ip route show default | awk '/default/ {print $5; exit}'); iptables -A FORWARD -i wg0 -o $EXT_IF -j ACCEPT; iptables -A FORWARD -i $EXT_IF -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -A POSTROUTING -o $EXT_IF -j MASQUERADE",
    postdown: "EXT_IF=$(ip route show default | awk '/default/ {print $5; exit}'); iptables -D FORWARD -i wg0 -o $EXT_IF -j ACCEPT; iptables -D FORWARD -i $EXT_IF -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -D POSTROUTING -o $EXT_IF -j MASQUERADE",
  };
  };
  readonly serverModel = signal({ ...this.serverInit });
  readonly serverForm = form(
    this.serverModel,
    (p) => {
      required(p.address, { message: "Address is required" });
      (required(p.listen_port), { message: "Listen port is required" });
      min(p.listen_port, 1, { message: "Listen port must be at least 1" });
      max(p.listen_port, 65535, {
        message: "Listen port must be at most 65535",
      });
      required(p.private_key, { message: "Private key is required" });
      (required(p.public_key), { message: "Public key is required" });
      readonly(p.public_key);
    },
    {
      submission: {
        action: async (f) => this.submitToServer(f),
      },
    },
  );

  ngOnInit(): void {
    this.loadServer();
    this.getStatus();
  }

  getStatus(): void {
    this.apiService.getStatus().subscribe({
      next: (status) => this.status.set(status.is_running === true),
      error: (err) => this.error.set((err as ApiError) ?? "Failed to get service status"),
    });
  }

  loadServer(): void {
    this.loading.set(true);
    this.serverService
      .get()
      .subscribe({
        next: (server: any) => {
          this.serverModel.set(server as any);
          this.loading.set(false);
        },
        error: (err) => {
          if (err.status !== 404) {
            this.error.set((err as ApiError) ?? "Failed to load server configuration");
          } else {
            this.serverForm().reset({ ...this.serverInit });
          }
          this.loading.set(false);
        },
      });
  }

  generateKeypair(): void {
    this.serverService.generateKeypair().subscribe({
      next: (keys) => {
        this.serverForm.private_key().value.set(keys.private_key);
        this.serverForm.public_key().value.set(keys.public_key);
      },
      error: (err) => this.error.set((err as ApiError) ?? "Failed to generate keys"),
    });
  }

  async resetServerConfig(): Promise<void> {
    if (this.resetting()) return;

    this.resetting.set(true);
    this.error.set(null);
    this.successMessage.set(null);

    this.serverForm().reset({ ...this.serverInit });

    try {
      await firstValueFrom(this.serverService.upsert(this.serverForm().value()));
      this.resetting.set(false);
      this.successMessage.set("Server configuration reset successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.resetting.set(false);
      this.error.set((err as ApiError) ?? "Failed to reset configuration");
    }
  }

  async applyConfig(): Promise<void> {
    this.applying.set(true);
    this.error.set(null);

    try {
      await firstValueFrom(this.serverService.applyConfig());
      this.applying.set(false);
      this.successMessage.set("Configuration applied and WireGuard restarted");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.applying.set(false);
      this.error.set((err as ApiError) ?? "Failed to apply configuration");
    } finally {
      this.getStatus();
    }
  }

  controlService(action: "start" | "stop" | "restart"): void {
    if (this.serviceActionLoading()) return;

    this.serviceActionLoading.set(action);
    this.error.set(null);
    this.successMessage.set(null);

    this.serverService.controlService(action).subscribe({
      next: () => {
        const pastTense: Record<"start" | "stop" | "restart", string> = {
          start: "started",
          stop: "stopped",
          restart: "restarted",
        };
        this.successMessage.set(`Service ${pastTense[action]} successfully`);
      },
      error: (err: unknown) => {
        this.error.set((err as ApiError) ?? `Failed to ${action} service`);
        this.serviceActionLoading.set(null);
      },
      complete: () => {
        this.serviceActionLoading.set(null),
        this.getStatus();
      }
    });
  }

  async submitToServer(f: any): Promise<void> {
    this.error.set(null);
    this.successMessage.set(null);

    try {
      await firstValueFrom(this.serverService.upsert(f().value()));
      this.successMessage.set("Server configuration saved successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.error.set((err as ApiError) ?? "Failed to save configuration");
    }
  }
}
