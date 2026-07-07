/**
 * HTTP interceptor for cookie-based auth.
 *
 * The JWT lives in an HttpOnly cookie set by the backend, so it is never read
 * by JS. This interceptor enables credentialed requests and, for state-changing
 * methods, mirrors the readable CSRF cookie into the X-CSRF-Token header
 * (double-submit-cookie pattern). It logs the user out on 401 responses.
 */

import { HttpErrorResponse, HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { catchError, throwError } from "rxjs";
import { AuthService } from "../services/auth.service";

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/** Read a non-HttpOnly cookie value by name. */
function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const isApiRequest = req.url.startsWith("/api");

  let authReq = req;
  if (isApiRequest) {
    const setHeaders: Record<string, string> = {};
    const csrf = readCookie("csrf_token");
    if (csrf && MUTATING_METHODS.has(req.method.toUpperCase())) {
      setHeaders["X-CSRF-Token"] = csrf;
    }
    authReq = req.clone({ withCredentials: true, setHeaders });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Auto-logout on 401 Unauthorized (expired or invalid session)
      if (error.status === 401 && isApiRequest) {
        authService.logout();
      }
      return throwError(() => error);
    }),
  );
};
