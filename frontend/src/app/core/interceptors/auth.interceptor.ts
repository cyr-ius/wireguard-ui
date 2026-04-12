/**
 * HTTP interceptor: attaches the JWT Bearer token to every outgoing API request.
 * Handles 401 responses by logging the user out.
 */

import { HttpErrorResponse, HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { catchError, throwError } from "rxjs";
import { AuthService } from "../services/auth.service";

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();
  const isApiRequest = req.url.startsWith("/api");

  const authReq = token && isApiRequest ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Auto-logout on 401 Unauthorized (expired or invalid token)
      if (error.status === 401 && isApiRequest) {
        authService.logout();
      }
      return throwError(() => error);
    }),
  );
};
