/**
 * Tracks whether the mandatory initial configuration (server keys + endpoint
 * address) has been completed. Used by the setup guards to force the admin
 * through the onboarding wizard before granting access to the rest of the app.
 */

import { inject, Injectable } from "@angular/core";
import { catchError, forkJoin, map, Observable, of } from "rxjs";
import { ApiService } from "./api.service";

export interface SetupStatus {
  serverConfigured: boolean;
  endpointConfigured: boolean;
  complete: boolean;
}

@Injectable({ providedIn: "root" })
export class SetupService {
  private readonly api = inject(ApiService);

  check(): Observable<SetupStatus> {
    return forkJoin({
      server: this.api.getServer().pipe(
        map((server) => !!server.public_key),
        catchError(() => of(false)),
      ),
      settings: this.api.getSettings().pipe(
        map((settings) => !!settings.endpoint_address),
        catchError(() => of(false)),
      ),
    }).pipe(
      map(({ server, settings }) => ({
        serverConfigured: server,
        endpointConfigured: settings,
        complete: server && settings,
      })),
    );
  }
}
