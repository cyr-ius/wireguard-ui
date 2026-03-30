/**
 * HealthService - Monitors API availability by polling /api/health.
 *
 * The last known state is persisted in sessionStorage so that page refreshes
 * do not trigger a loading flash when the API was previously reachable.
 * The persisted value is always re-validated immediately in the background.
 */

import { HttpClient } from "@angular/common/http";
import { computed, inject, Injectable, signal } from "@angular/core";
import { catchError, interval, of, startWith, switchMap, tap } from "rxjs";

/** Polling interval in milliseconds */
const HEALTH_CHECK_INTERVAL_MS = 30_000;

/** sessionStorage key used to persist the last known health state */
const STORAGE_KEY = "wg_api_health";

/** Response shape from the /api/health endpoint */
interface HealthResponse {
  status: string;
  app: string;
}

@Injectable({ providedIn: "root" })
export class HealthService {
  private readonly http = inject(HttpClient);

  /**
   * Internal mutable signal.
   * Initialised from sessionStorage so that a page refresh does not
   * display the loading screen when the API was healthy before.
   */
  private readonly _isApiAvailable = signal<boolean | null>(
    this._loadFromStorage(),
  );

  /**
   * Public readonly signal.
   * - null  → initial check not yet completed (no prior session data)
   * - true  → API is reachable and healthy
   * - false → API is unreachable or returned an error
   */
  readonly isApiAvailable = this._isApiAvailable.asReadonly();

  /**
   * Computed signal: true when the API is confirmed available.
   * Used by the template to render the router outlet.
   */
  readonly isReady = computed(() => this._isApiAvailable() === true);

  /**
   * Computed signal: true when the API is confirmed unavailable.
   * Used by the template to render the error page.
   */
  readonly isDown = computed(() => this._isApiAvailable() === false);

  constructor() {
    // Start polling immediately, then repeat every HEALTH_CHECK_INTERVAL_MS
    interval(HEALTH_CHECK_INTERVAL_MS)
      .pipe(
        startWith(0),
        switchMap(() =>
          this.http.get<HealthResponse>("/api/health").pipe(
            tap(() => this._setAvailability(true)),
            catchError(() => {
              this._setAvailability(false);
              return of(null);
            }),
          ),
        ),
      )
      .subscribe();
  }

  /**
   * Trigger an immediate health check outside the regular polling cycle.
   * Resets the signal to null (loading state) only when there is no
   * previously cached value, so a "retry" does not cause a full-page flash.
   */
  checkNow(): void {
    // Only show loading state if we have no prior knowledge
    if (this._isApiAvailable() === false) {
      this._isApiAvailable.set(null);
    }

    this.http
      .get<HealthResponse>("/api/health")
      .pipe(
        catchError(() => {
          this._setAvailability(false);
          return of(null);
        }),
      )
      .subscribe((response) => {
        if (response !== null) {
          this._setAvailability(true);
        }
      });
  }

  // ── Private helpers ────────────────────────────────────────────────────────

  /**
   * Updates both the signal and the sessionStorage cache.
   *
   * @param available - Whether the API is currently reachable.
   */
  private _setAvailability(available: boolean): void {
    this._isApiAvailable.set(available);
    try {
      sessionStorage.setItem(STORAGE_KEY, String(available));
    } catch {
      // sessionStorage may be unavailable in some browser contexts; ignore.
    }
  }

  /**
   * Reads the last known health state from sessionStorage.
   * Returns null if no prior value is stored (first visit or new tab).
   */
  private _loadFromStorage(): boolean | null {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw === "true") return true;
      if (raw === "false") return false;
    } catch {
      // sessionStorage unavailable; fall through to null.
    }
    return null;
  }
}
