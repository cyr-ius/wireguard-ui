import {
  ChangeDetectionStrategy,
  Component,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ServerService } from '../../core/services/api.service';
import { ServerCreate } from '../../shared/models/api.models';

const SERVER_DEFAULTS: ServerCreate = {
  address: '192.168.1.0/24',
  listen_port: 51820,
  private_key: '',
  public_key: '',
  postup:
    'iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE',
  postdown:
    'iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE',
};

@Component({
  selector: 'app-server',
  standalone: true,
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './server.component.html',
  styleUrls: ['./server.component.css'],
})
export class ServerComponent implements OnInit {
  private readonly serverService = inject(ServerService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly applying = signal(false);
  readonly resetting = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly showPrivateKey = signal(false);

  readonly serverForm = this.fb.group({
    address: [SERVER_DEFAULTS.address, [Validators.required]],
    listen_port: [
      SERVER_DEFAULTS.listen_port,
      [Validators.required, Validators.min(1), Validators.max(65535)],
    ],
    private_key: [SERVER_DEFAULTS.private_key, [Validators.required]],
    public_key: [SERVER_DEFAULTS.public_key, [Validators.required]],
    postup: [SERVER_DEFAULTS.postup ?? ''],
    postdown: [SERVER_DEFAULTS.postdown ?? ''],
  });

  ngOnInit(): void {
    this.loadServer();
  }

  loadServer(): void {
    this.loading.set(true);
    this.serverService.get().subscribe({
      next: (server) => {
        this.serverForm.reset({
          address: server.address,
          listen_port: server.listen_port,
          private_key: '',
          public_key: server.public_key,
          postup: server.postup ?? SERVER_DEFAULTS.postup ?? '',
          postdown: server.postdown ?? SERVER_DEFAULTS.postdown ?? '',
        });
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status !== 404) {
          this.error.set(err?.error?.detail ?? 'Failed to load server configuration');
        } else {
          this.resetServerForm();
        }
        this.loading.set(false);
      },
    });
  }

  generateKeypair(): void {
    this.serverService.generateKeypair().subscribe({
      next: (keys) => {
        this.serverForm.patchValue({
          private_key: keys.private_key,
          public_key: keys.public_key,
        });
      },
      error: (err) => this.saveError.set(err?.error?.detail ?? 'Failed to generate keys'),
    });
  }

  saveServer(): void {
    if (this.serverForm.invalid || this.saving()) return;

    this.saving.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);

    this.serverService.upsert(this.serverForm.getRawValue() as ServerCreate).subscribe({
      next: () => {
        this.saving.set(false);
        this.successMessage.set('Server configuration saved successfully');
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.saving.set(false);
        this.saveError.set(err?.error?.detail ?? 'Failed to save configuration');
      },
    });
  }

  resetServerConfig(): void {
    if (this.resetting()) return;

    this.resetting.set(true);
    this.saveError.set(null);
    this.successMessage.set(null);

    this.serverService.reset().subscribe({
      next: () => {
        this.resetting.set(false);
        this.resetServerForm();
        this.successMessage.set('Server configuration reset successfully');
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.resetting.set(false);
        this.saveError.set(err?.error?.detail ?? 'Failed to reset configuration');
      },
    });
  }

  applyConfig(): void {
    this.applying.set(true);
    this.saveError.set(null);

    this.serverService.applyConfig().subscribe({
      next: () => {
        this.applying.set(false);
        this.successMessage.set('Configuration applied and WireGuard restarted');
        setTimeout(() => this.successMessage.set(null), 4000);
      },
      error: (err) => {
        this.applying.set(false);
        this.saveError.set(err?.error?.detail ?? 'Failed to apply configuration');
      },
    });
  }

  controlService(action: 'start' | 'stop' | 'restart'): void {
    this.serverService.controlService(action).subscribe({
      next: () => this.successMessage.set(`Service ${action}ed successfully`),
      error: (err) => this.saveError.set(err?.error?.detail ?? `Failed to ${action} service`),
    });
  }

  isInvalid(field: string): boolean {
    const control = this.serverForm.get(field);
    return !!(control?.invalid && control?.touched);
  }

  private resetServerForm(): void {
    this.serverForm.reset({ ...SERVER_DEFAULTS });
    this.serverForm.markAsPristine();
    this.serverForm.markAsUntouched();
  }
}
