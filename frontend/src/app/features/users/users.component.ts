import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from "@angular/core";
import { email, form, FormField, FormRoot, minLength, readonly, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { ErrorField } from "../../core/applets/error-field.component";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { UsersService } from "../../core/services/api.service";
import { AuthService } from "../../core/services/auth.service";
import { ApiError } from "../../shared/models/api-error.model";
import { Role, User, UserCreate, UserUpdate } from "../../shared/models/api.models";

type ModalMode = "create" | "edit" | null;

@Component({
  selector: "app-users",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./users.component.html",
  styleUrls: ["./users.component.css"],
})
export class UsersComponent implements OnInit {
  private readonly usersService = inject(UsersService);
  private readonly authService = inject(AuthService);

  readonly users = signal<User[]>([]);
  readonly roles = signal<Role[]>([]);
  readonly loading = signal(true);
  readonly error = signal<ApiError | null>(null);
  readonly formError = signal<ApiError | null>(null);
  readonly modalMode = signal<ModalMode>(null);
  readonly selectedUser = signal<User | null>(null);
  readonly deleteTarget = signal<User | null>(null);

  readonly currentUsername = computed(() => this.authService.currentUser()?.username ?? "");

  private readonly userInit = {
    id: "",
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    active: true,
    role_ids: [] as number[],
  };
  readonly userModel = signal({ ...this.userInit });
  readonly userForm = form(
    this.userModel,
    (p) => {
      required(p.username, { message: "Username is required" });
      required(p.password, { message: "Password is required", when: () => this.modalMode() === "create" });
      required(p.email);
      required(p.role_ids, { message: "At least one role is required" });
      email(p.email, { message: "Invalid email format" });
      minLength(p.username, 3, { message: "String should have at least 3 characters" });
      minLength(p.password, 8, { message: "String should have at least 8 characters" });
      readonly(p.username, () => this.modalMode() === "edit");
    },
    {
      submission: {
        action: async (f) => this.saveUser(f),
      },
    },
  );

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
        this.error.set((err as ApiError) ?? "Failed to load users");
        this.loading.set(false);
      },
    });
    this.usersService.getRoles().subscribe({
      next: (roles) => this.roles.set(roles),
    });
  }

  openCreateModal(): void {
    this.userForm().reset({ ...this.userInit });
    this.formError.set(null);
    this.modalMode.set("create");
  }

  openEditModal(user: User): void {
    this.selectedUser.set(user);
    this.userModel.set(<any>{ ...user, password: "", role_ids: user.roles.map((r) => r.id) });
    this.formError.set(null);
    this.modalMode.set("edit");
  }

  closeModal(): void {
    this.modalMode.set(null);
    this.selectedUser.set(null);
    this.formError.set(null);
  }

  async saveUser(f: any): Promise<void> {
    this.formError.set(null);
    const mode = this.modalMode();
    try {
      if (mode === "create") {
        await firstValueFrom(this.usersService.create(f().value() as UserCreate));
        this.closeModal();
        this.loadData();
      } else {
        const id = this.selectedUser()!.id;
        await firstValueFrom(this.usersService.update(id, f().value() as UserUpdate));
        this.closeModal();
        this.loadData();
      }
    } catch (err: unknown) {
      this.formError.set((err as ApiError) ?? `Failed to ${mode} user`);
    }
  }

  confirmDelete(): void {
    const target = this.deleteTarget();
    if (!target) return;
    this.usersService.delete(target.id).subscribe({
      next: () => {
        this.deleteTarget.set(null);
        this.loadData();
      },
      error: (err: unknown) => this.error.set((err as ApiError) ?? "Failed to delete user"),
    });
  }

  isRoleSelected(roleId: number): boolean {
    return this.userForm.role_ids().value()?.includes(roleId) ?? false;
  }

  toggleRole(roleId: number): void {
    const current = this.userForm.role_ids().value() ?? [];
    const updated = current.includes(roleId) ? current.filter((id) => id !== roleId) : [...current, roleId];
    this.userForm.role_ids().value.set(updated);
  }
}
