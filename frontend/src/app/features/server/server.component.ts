import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from "@angular/core";
import { form, FormField, FormRoot, max, min, readonly, required } from "@angular/forms/signals";
import { firstValueFrom, tap } from "rxjs";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { ApiService, ServerService } from "../../core/services/api.service";

@Component({
  selector: "app-server",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields],
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
  readonly serviceStatus = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly showPrivateKey = signal(false);

  private readonly serverInit = {
    address: "192.168.1.0/24",
    listen_port: 51820,
    private_key: "",
    public_key: "",
    postup: "iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
    postdown: "iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE",
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
  }

  loadServer(): void {
    this.loading.set(true);
    this.serverService
      .get()
      .pipe(tap(() => this.getStatus()))
      .subscribe({
        next: (server: any) => {
          this.serverModel.set(server as any);
          this.loading.set(false);
        },
        error: (err) => {
          if (err.status !== 404) {
            this.error.set(err?.error?.detail ?? "Failed to load server configuration");
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
      error: (err) => this.saveError.set(err?.error?.detail ?? "Failed to generate keys"),
    });
  }

  getStatus() {
    this.apiService.getStatus().subscribe((status) => {
      this.serviceStatus.set(status.is_running === true);
    });
  }

  async resetServerConfig(): Promise<void> {
    if (this.resetting()) return;

    this.resetting.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);

    this.serverForm().reset({ ...this.serverInit });

    try {
      await firstValueFrom(this.serverService.upsert(this.serverForm().value()));
      this.resetting.set(false);
      this.successMessage.set("Server configuration reset successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.resetting.set(false);
      this.saveError.set((err instanceof HttpErrorResponse && err.error.detail) || "Failed to reset configuration");
    }
  }

  async applyConfig(): Promise<void> {
    this.applying.set(true);
    this.saveError.set(null);

    try {
      await firstValueFrom(this.serverService.applyConfig());
      this.getStatus();
      this.applying.set(false);
      this.successMessage.set("Configuration applied and WireGuard restarted");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.applying.set(false);
      this.saveError.set((err instanceof HttpErrorResponse && err.error.detail) || "Failed to apply configuration");
    }
  }

  controlService(action: "start" | "stop" | "restart"): void {
    if (this.serviceActionLoading()) return;

    this.serviceActionLoading.set(action);
    this.saveError.set(null);
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
        this.saveError.set((err instanceof HttpErrorResponse && err.error.detail) || `Failed to ${action} service`);
        this.serviceActionLoading.set(null);
      },
      complete: () => this.serviceActionLoading.set(null),
    });
  }

  async submitToServer(f: any): Promise<void> {
    this.saveError.set(null);
    this.successMessage.set(null);

    try {
      await firstValueFrom(this.serverService.upsert(f().value()));
      this.successMessage.set("Server configuration saved successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.saveError.set((err instanceof HttpErrorResponse && err.error.detail) || "Failed to save configuration");
    }
  }
}
