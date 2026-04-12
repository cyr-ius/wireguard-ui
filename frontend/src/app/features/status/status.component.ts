/**
 * Status page: displays live WireGuard interface and peer stats.
 * Uses signals + toSignal() for reactive data flow.
 */

import { Component, computed, inject, signal } from "@angular/core";
import { toSignal } from "@angular/core/rxjs-interop";
import { interval, startWith, switchMap } from "rxjs";
import { ApiService, WgStatus } from "../../core/services/api.service";

@Component({
  selector: "app-status",
  standalone: true,
  templateUrl: "./status.component.html",
  styleUrl: "./status.component.css",
})
export class StatusComponent {
  private readonly api = inject(ApiService);

  readonly isRefreshing = signal(false);

  // Auto-refresh every 10 seconds
  private readonly status$ = interval(10_000).pipe(
    startWith(0),
    switchMap(() => this.api.getStatus()),
  );

  readonly status = toSignal<WgStatus>(this.status$);

  readonly peerCount = computed(() => this.status()?.peers?.length ?? 0);
  readonly isRunning = computed(() => this.status()?.is_running ?? false);

  refresh(): void {
    this.isRefreshing.set(true);
    this.api.getStatus().subscribe({
      next: () => this.isRefreshing.set(false),
      error: () => this.isRefreshing.set(false),
    });
  }
}
