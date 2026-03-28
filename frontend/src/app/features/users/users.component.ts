import {
  Component,
  signal,
  computed,
  inject,
  OnInit,
  ChangeDetectionStrategy,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { UsersService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { User, Role, UserCreate, UserUpdate } from '../../shared/models/api.models';

type ModalMode = 'create' | 'edit' | null;

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css'],
})
export class UsersComponent implements OnInit {
  private readonly usersService = inject(UsersService);
  private readonly authService = inject(AuthService);
  private readonly fb = inject(FormBuilder);

  readonly users = signal<User[]>([]);
  readonly roles = signal<Role[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly formError = signal<string | null>(null);
  readonly modalMode = signal<ModalMode>(null);
  readonly selectedUser = signal<User | null>(null);
  readonly deleteTarget = signal<User | null>(null);

  readonly currentUsername = computed(() => this.authService.currentUser()?.username ?? '');

  readonly userForm = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    first_name: [''],
    last_name: [''],
    password: ['', [Validators.minLength(8)]],
    active: [true],
    role_ids: [[] as number[]],
  });

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading.set(true);
    this.usersService.list().subscribe({
      next: (users) => {
        this.users.set(users);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Failed to load users');
        this.loading.set(false);
      },
    });
    this.usersService.getRoles().subscribe({
      next: (roles) => this.roles.set(roles),
    });
  }

  openCreateModal(): void {
    this.userForm.reset({ active: true, role_ids: [] });
    this.userForm.get('password')?.setValidators([Validators.required, Validators.minLength(8)]);
    this.userForm.get('password')?.updateValueAndValidity();
    this.formError.set(null);
    this.modalMode.set('create');
  }

  openEditModal(user: User): void {
    this.selectedUser.set(user);
    this.userForm.get('password')?.clearValidators();
    this.userForm.get('password')?.updateValueAndValidity();
    this.userForm.patchValue({
      username: user.username,
      email: user.email,
      first_name: user.first_name ?? '',
      last_name: user.last_name ?? '',
      active: user.active,
      role_ids: user.roles.map((r) => r.id),
      password: '',
    });
    this.formError.set(null);
    this.modalMode.set('edit');
  }

  closeModal(): void {
    this.modalMode.set(null);
    this.selectedUser.set(null);
    this.formError.set(null);
  }

  saveUser(): void {
    if (this.userForm.invalid || this.saving()) return;

    this.saving.set(true);
    this.formError.set(null);
    const value = this.userForm.value;
    const mode = this.modalMode();

    if (mode === 'create') {
      this.usersService.create(value as UserCreate).subscribe({
        next: () => { this.saving.set(false); this.closeModal(); this.loadData(); },
        error: (err) => { this.saving.set(false); this.formError.set(err?.error?.detail ?? 'Failed to create user'); },
      });
    } else {
      const id = this.selectedUser()!.id;
      const update: UserUpdate = {
        email: value.email ?? undefined,
        first_name: value.first_name ?? undefined,
        last_name: value.last_name ?? undefined,
        active: value.active ?? undefined,
        role_ids: value.role_ids ?? undefined,
      };
      this.usersService.update(id, update).subscribe({
        next: () => { this.saving.set(false); this.closeModal(); this.loadData(); },
        error: (err) => { this.saving.set(false); this.formError.set(err?.error?.detail ?? 'Failed to update user'); },
      });
    }
  }

  confirmDelete(): void {
    const target = this.deleteTarget();
    if (!target) return;
    this.usersService.delete(target.id).subscribe({
      next: () => { this.deleteTarget.set(null); this.loadData(); },
      error: (err) => this.error.set(err?.error?.detail ?? 'Failed to delete user'),
    });
  }

  isRoleSelected(roleId: number): boolean {
    return (this.userForm.get('role_ids')?.value as number[])?.includes(roleId) ?? false;
  }

  toggleRole(roleId: number): void {
    const current = (this.userForm.get('role_ids')?.value as number[]) ?? [];
    const updated = current.includes(roleId)
      ? current.filter((id) => id !== roleId)
      : [...current, roleId];
    this.userForm.get('role_ids')?.setValue(updated);
  }

  isInvalid(field: string): boolean {
    const c = this.userForm.get(field);
    return !!(c?.invalid && c?.touched);
  }
}
