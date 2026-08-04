/**
 * Route guards enforcing the mandatory onboarding wizard for admins:
 * server keys and endpoint address must be configured before any other
 * admin screen becomes reachable.
 */

import { inject } from "@angular/core";
import { CanActivateFn, Router } from "@angular/router";
import { firstValueFrom } from "rxjs";
import { AuthService } from "../services/auth.service";
import { SetupService } from "../services/setup.service";

/** Applied to protected routes: redirects the admin to /setup while onboarding is incomplete. */
export const setupRequiredGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const setup = inject(SetupService);
  const router = inject(Router);

  if (!auth.isAdmin()) {
    return true;
  }

  const status = await firstValueFrom(setup.check());
  return status.complete ? true : router.createUrlTree(["/setup"]);
};

/** Applied to /setup: skip the wizard once onboarding is already complete. */
export const setupCompleteGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const setup = inject(SetupService);
  const router = inject(Router);

  if (!auth.isAdmin()) {
    return router.createUrlTree(["/status"]);
  }

  const status = await firstValueFrom(setup.check());
  return status.complete ? router.createUrlTree(["/status"]) : true;
};
