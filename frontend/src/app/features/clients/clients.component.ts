import {
  Component,
  signal,
  computed,
  inject,
  OnInit,
  ChangeDetectionStrategy,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ClientsService } from '../../core/services/api.service';
import { WireGuardClient, ClientCreate, ClientUpdate } from '../../shared/models/api.models';

type ModalMode = 'create' | 'edit' | null;

@Component({
  selector: 'app-clients',
  standalone: true,
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './clients.component.html',
  styleUrls: ['./clients.component.css'],
})
export class ClientsComponent implements OnInit {
  private readonly clientsService = inject(ClientsService);
  private readonly fb = inject(FormBuilder);

  // Data signals
  readonly clients = signal<WireGuardClient[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly saving = signal(false);
  readonly formError = signal<string | null>(null);

  // Modal state signals
  readonly modalMode = signal<ModalMode>(null);
  readonly selectedClient = signal<WireGuardClient | null>(null);
  readonly configContent = signal<string | null>(null);
  readonly showConfig = signal(false);
  readonly deleteTarget = signal<WireGuardClient | null>(null);

  // Computed
  readonly filteredClients = computed(() => this.clients());
  readonly enabledCount = computed(() =>
    this.clients().filter((c) => c.enabled).length
  );

  // Form using signal-compatible FormBuilder
  readonly clientForm = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(1)]],
    email: ['', [Validators.required, Validators.email]],
    allocated_ips: ['', [Validators.required]],
    allowed_ips: ['0.0.0.0/0', [Validators.required]],
    use_server_dns: [true],
    enabled: [true],
    preshared_key: [''],
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
        this.error.set(err?.error?.detail ?? 'Failed to load clients');
        this.loading.set(false);
      },
    });
  }

  openCreateModal(): void {
    this.clientForm.reset({ allowed_ips: '0.0.0.0/0', use_server_dns: true, enabled: true });
    this.formError.set(null);
    this.modalMode.set('create');
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
      preshared_key: client.preshared_key ?? '',
    });
    this.formError.set(null);
    this.modalMode.set('edit');
  }

  closeModal(): void {
    this.modalMode.set(null);
    this.selectedClient.set(null);
    this.formError.set(null);
  }

  saveClient(): void {
    if (this.clientForm.invalid || this.saving()) return;

    this.saving.set(true);
    this.formError.set(null);

    const value = this.clientForm.value;
    const mode = this.modalMode();

    if (mode === 'create') {
      this.clientsService.create(value as ClientCreate).subscribe({
        next: () => {
          this.saving.set(false);
          this.closeModal();
          this.loadClients();
        },
        error: (err) => {
          this.saving.set(false);
          this.formError.set(err?.error?.detail ?? 'Failed to create client');
        },
      });
    } else if (mode === 'edit') {
      const clientId = this.selectedClient()!.id;
      this.clientsService.update(clientId, value as ClientUpdate).subscribe({
        next: () => {
          this.saving.set(false);
          this.closeModal();
          this.loadClients();
        },
        error: (err) => {
          this.saving.set(false);
          this.formError.set(err?.error?.detail ?? 'Failed to update client');
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
      error: (err) => this.error.set(err?.error?.detail ?? 'Failed to delete client'),
    });
  }

  viewConfig(client: WireGuardClient): void {
    this.clientsService.getConfig(client.id).subscribe({
      next: (data) => {
        this.configContent.set(data.config);
        this.showConfig.set(true);
      },
      error: (err) =>
        this.error.set(err?.error?.detail ?? 'Failed to load configuration'),
    });
  }

  downloadConfig(client: WireGuardClient): void {
    this.clientsService.getConfig(client.id).subscribe({
      next: (data) => {
        const blob = new Blob([data.config], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
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

  isInvalid(field: string): boolean {
    const control = this.clientForm.get(field);
    return !!(control?.invalid && control?.touched);
  }
}
