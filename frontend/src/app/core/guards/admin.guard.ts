/**
 * Route guard: restricts access to admin-only routes.
 * Frontend counterpart to require_admin backend dependency.
 * Backend will still return 403 even if this guard is bypassed.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated() && auth.isAdmin()) {
    return true;
  }
  // Redirect non-admin users to status page
  return router.createUrlTree(['/status']);
};
