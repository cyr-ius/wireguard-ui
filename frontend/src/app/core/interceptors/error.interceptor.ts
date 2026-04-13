// src/app/core/interceptors/error.interceptor.ts
import { HttpErrorResponse, HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { catchError, throwError } from "rxjs";

import { ApiError } from "../../shared/models/api-error.model";
import { AuthService } from "../services/auth.service";
// import { NotificationService } from "../services/notification.service";

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  // const notify = inject(NotificationService);
  const auth = inject(AuthService);

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const apiError: ApiError = err.error ?? {
        code: "UNKNOWN_ERROR",
        message: "An unexpected error occurred",
      };

      switch (err.status) {
        case 401:
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
