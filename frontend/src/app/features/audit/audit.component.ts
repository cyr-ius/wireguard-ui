import { DatePipe } from "@angular/common";
import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from "@angular/core";
import { ErrorField } from "../../core/applets/error-field.component";
import { ApiError } from "../../core/models/api-error.model";
import { AuditLogEntry } from "../../core/models/api.models";
import { AuditService } from "../../core/services/api.service";

const PAGE_SIZE = 25;

@Component({
  selector: "app-audit",
  standalone: true,
  imports: [ErrorField, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./audit.component.html",
  styleUrls: ["./audit.component.css"],
})
export class AuditComponent implements OnInit {
  private readonly auditService = inject(AuditService);

  readonly entries = signal<AuditLogEntry[]>([]);
  readonly total = signal(0);
  readonly page = signal(0);
  readonly loading = signal(true);
  readonly error = signal<ApiError | null>(null);

  readonly pageCount = computed(() => Math.max(1, Math.ceil(this.total() / PAGE_SIZE)));
  readonly hasPrevious = computed(() => this.page() > 0);
  readonly hasNext = computed(() => (this.page() + 1) * PAGE_SIZE < this.total());

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.auditService.list(PAGE_SIZE, this.page() * PAGE_SIZE).subscribe({
      next: (result) => {
        this.entries.set(result.items);
        this.total.set(result.total);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set((err as ApiError) ?? { code: "UNKNOWN", message: "Failed to load audit log" });
        this.loading.set(false);
      },
    });
  }

  previousPage(): void {
    if (!this.hasPrevious()) return;
    this.page.update((p) => p - 1);
    this.load();
  }

  nextPage(): void {
    if (!this.hasNext()) return;
    this.page.update((p) => p + 1);
    this.load();
  }

  actionLabel(action: string): string {
    return action.replace(/[._]/g, " ");
  }
}
