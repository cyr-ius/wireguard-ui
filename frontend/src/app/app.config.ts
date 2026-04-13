import { provideHttpClient, withFetch, withInterceptors } from "@angular/common/http";
import { ApplicationConfig, provideZonelessChangeDetection } from "@angular/core";
import { provideRouter, withHashLocation } from "@angular/router";

import { FormField, provideSignalFormsConfig } from "@angular/forms/signals";
import { routes } from "./app.routes";
import { authInterceptor } from "./core/interceptors/auth.interceptor";
import { errorInterceptor } from "./core/interceptors/error.interceptor";

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor, errorInterceptor])),
    provideRouter(routes, withHashLocation()),
    provideSignalFormsConfig({
      classes: {
        "is-invalid": (state: FormField<unknown>) => state.state().touched() && state.state().invalid(),
        "is-valid": (state: FormField<unknown>) => state.state().touched() && state.state().valid(),
      },
    }),
  ],
};
