// src/app/core/interceptors/error.interceptor.ts
import { HttpErrorResponse, HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { catchError, throwError } from "rxjs";

import { ApiError } from "../models/api-error.model";
import { AuthService } from "../services/auth.service";
import { SessionExpiredService } from "../services/session-expired.service";
// import { NotificationService } from "../services/notification.service";

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  // const notify = inject(NotificationService);
  const auth = inject(AuthService);
  const sessionExpired = inject(SessionExpiredService);

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const apiError: ApiError = err.error ?? {
        code: "UNKNOWN_ERROR",
        message: "An unexpected error occurred",
      };

      switch (err.status) {
        case 401:
          // A 401 while we believed we were logged in means the session
          // expired server-side (cookie/JWT no longer valid); show the modal
          // before returning to the login page. A 401 on an anonymous
          // request (e.g. bad login credentials) is left to the caller.
          if (auth.isAuthenticated()) {
            sessionExpired.show();
          }
          auth.logout();
          break;
        case 403:
          // notify.error("Access denied");
          break;
        case 422:
          // Validation : les détails sont renvoyés au composant
          break;
        case 0:
          // notify.error("Server unreachable. Check your connection.");
          break;
        default:
        // notify.error(apiError.message);
      }

      // On retransmet une erreur typée
      return throwError(() => apiError);
    }),
  );
};
