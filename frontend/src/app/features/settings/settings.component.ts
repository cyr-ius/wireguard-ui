import {
  Component,
  signal,
  inject,
  OnInit,
  ChangeDetectionStrategy,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { SettingsService } from '../../core/services/api.service';
import { SettingsUpdate } from '../../shared/models/api.models';

const SETTINGS_DEFAULTS = {
  endpoint_address: '',
  dns_servers: '1.1.1.1',
  mtu: null as number | null,
  persistent_keepalive: null as number | null,
  config_file_path: '/etc/wireguard/wg0.conf',
  maintenance_mode: false,
};

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
})
export class SettingsComponent implements OnInit {
  private readonly settingsService = inject(SettingsService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly resetting = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly settingsForm = this.fb.group({
    endpoint_address: [SETTINGS_DEFAULTS.endpoint_address, [Validators.required]],
    dns_servers: [SETTINGS_DEFAULTS.dns_servers],
    mtu: [SETTINGS_DEFAULTS.mtu],
    persistent_keepalive: [SETTINGS_DEFAULTS.persistent_keepalive],
    config_file_path: [SETTINGS_DEFAULTS.config_file_path, [Validators.required]],
    maintenance_mode: [SETTINGS_DEFAULTS.maintenance_mode],
  });

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings(): void {
    this.settingsService.get().subscribe({
      next: (s) => {
        this.settingsForm.reset({
          endpoint_address: s.endpoint_address ?? SETTINGS_DEFAULTS.endpoint_address,
          dns_servers: s.dns_servers ?? SETTINGS_DEFAULTS.dns_servers,
          mtu: s.mtu ?? SETTINGS_DEFAULTS.mtu,
          persistent_keepalive:
            s.persistent_keepalive ?? SETTINGS_DEFAULTS.persistent_keepalive,
          config_file_path: s.config_file_path ?? SETTINGS_DEFAULTS.config_file_path,
          maintenance_mode: s.maintenance_mode ?? SETTINGS_DEFAULTS.maintenance_mode,
        });
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status !== 404) {
          this.error.set(err?.error?.detail ?? 'Failed to load settings');
        } else {
          this.resetForm();
        }
        this.loading.set(false);
      },
    });
  }

  save(): void {
    if (this.settingsForm.invalid || this.saving()) return;

    this.saving.set(true);
    this.saveError.set(null);

    const value = this.settingsForm.getRawValue() as SettingsUpdate;

    this.settingsService.update(value).subscribe({
      next: () => {
        this.saving.set(false);
        this.successMessage.set('Settings saved successfully');
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.saving.set(false);
        this.saveError.set(err?.error?.detail ?? 'Failed to save settings');
      },
    });
  }

  resetSettings(): void {
    if (this.resetting()) return;

    this.resetting.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);

    this.settingsService.reset().subscribe({
      next: (settings) => {
        this.resetting.set(false);
        this.settingsForm.reset({
          endpoint_address: settings.endpoint_address ?? SETTINGS_DEFAULTS.endpoint_address,
          dns_servers: settings.dns_servers ?? SETTINGS_DEFAULTS.dns_servers,
          mtu: settings.mtu ?? SETTINGS_DEFAULTS.mtu,
          persistent_keepalive:
            settings.persistent_keepalive ?? SETTINGS_DEFAULTS.persistent_keepalive,
          config_file_path:
            settings.config_file_path ?? SETTINGS_DEFAULTS.config_file_path,
          maintenance_mode:
            settings.maintenance_mode ?? SETTINGS_DEFAULTS.maintenance_mode,
        });
        this.successMessage.set('Global settings reset successfully');
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.resetting.set(false);
        this.saveError.set(err?.error?.detail ?? 'Failed to reset settings');
      },
    });
  }

  isInvalid(field: string): boolean {
    const c = this.settingsForm.get(field);
    return !!(c?.invalid && c?.touched);
  }

  private resetForm(): void {
    this.settingsForm.reset({ ...SETTINGS_DEFAULTS });
    this.settingsForm.markAsPristine();
    this.settingsForm.markAsUntouched();
  }
}
