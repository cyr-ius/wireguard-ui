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
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly settingsForm = this.fb.group({
    endpoint_address: ['', [Validators.required]],
    dns_servers: ['1.1.1.1,8.8.8.8'],
    mtu: [null as number | null],
    persistent_keepalive: [null as number | null],
    config_file_path: ['/etc/wireguard/wg0.conf', [Validators.required]],
    maintenance_mode: [false],
  });

  ngOnInit(): void {
    this.settingsService.get().subscribe({
      next: (s) => {
        this.settingsForm.patchValue({
          endpoint_address: s.endpoint_address ?? '',
          dns_servers: s.dns_servers ?? '',
          mtu: s.mtu ?? null,
          persistent_keepalive: s.persistent_keepalive ?? null,
          config_file_path: s.config_file_path,
          maintenance_mode: s.maintenance_mode,
        });
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status !== 404) {
          this.error.set(err?.error?.detail ?? 'Failed to load settings');
        }
        this.loading.set(false);
      },
    });
  }

  save(): void {
    if (this.settingsForm.invalid || this.saving()) return;

    this.saving.set(true);
    this.saveError.set(null);

    const value = this.settingsForm.value as SettingsUpdate;

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

  isInvalid(field: string): boolean {
    const c = this.settingsForm.get(field);
    return !!(c?.invalid && c?.touched);
  }
}
