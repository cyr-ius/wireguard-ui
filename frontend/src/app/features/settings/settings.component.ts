import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from "@angular/core";
import { form, FormField, FormRoot, max, min, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { SettingsService } from "../../core/services/api.service";

@Component({
  selector: "app-settings",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./settings.component.html",
  styleUrls: ["./settings.component.css"],
})
export class SettingsComponent implements OnInit {
  private readonly settingsService = inject(SettingsService);

  readonly loading = signal(true);
  readonly resetting = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  private readonly settingsInit = {
    endpoint_address: "",
    dns_servers: "1.1.1.1,8.8.8.8",
    mtu: null,
    persistent_keepalive: null,
    config_file_path: "/etc/wireguard/wg0.conf",
    maintenance_mode: false,
  };
  readonly settingsModel = signal({ ...this.settingsInit });
  readonly settingsForm = form(
    this.settingsModel,
    (s) => {
      required(s.endpoint_address);
      required(s.config_file_path);
      min(s.mtu, 576, { message: "MTU must be at least 576" });
      min(s.persistent_keepalive, 0, {
        message: "Keepalive must be a positive number",
      });
      max(s.mtu, 9000, { message: "MTU must be at most 9000" });
      max(s.persistent_keepalive, 65535, {
        message: "Keepalive must be at most 65535",
      });
      required(s.dns_servers, {
        message: "At least one DNS server is required",
      });
      required(s.config_file_path, { message: "Config file path is required" });
    },
    {
      submission: {
        action: async (f) => this.save(f),
      },
    },
  );

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings(): void {
    this.settingsService.get().subscribe({
      next: (settings: any) => {
        this.settingsModel.set(settings);
        this.loading.set(false);
      },
      error: (err: any) => {
        if (err.status !== 404) {
          this.error.set(err?.error?.detail ?? "Failed to load settings");
        } else {
          this.settingsForm().reset({ ...this.settingsInit });
        }
        this.loading.set(false);
      },
    });
  }

  async save(f: any): Promise<void> {
    this.saveError.set(null);
    try {
      await firstValueFrom(this.settingsService.update(f().value()));
      this.successMessage.set("Settings saved successfully");
      setTimeout(() => this.successMessage.set(null), 4000);
    } catch (err: unknown) {
      this.saveError.set((err instanceof HttpErrorResponse && err.error.detail) || "Failed to save settings");
    }
  }

  resetSettings(): void {
    if (this.resetting()) return;

    this.resetting.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);

    this.settingsService.reset().subscribe({
      next: (settings) => {
        this.resetting.set(false);
        this.settingsForm().reset({ ...this.settingsInit });
        this.successMessage.set("Global settings reset successfully");
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.resetting.set(false);
        this.saveError.set(err?.error?.detail ?? "Failed to reset settings");
      },
    });
  }
}
