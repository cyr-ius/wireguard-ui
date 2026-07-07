import { provideHttpClient, withFetch, withInterceptors } from "@angular/common/http";
import { ApplicationConfig, provideZonelessChangeDetection } from "@angular/core";
import { provideRouter } from "@angular/router";

import { FormFieldBinding, provideSignalFormsConfig } from "@angular/forms/signals";
import { routes } from "./app.routes";
import { authInterceptor } from "./core/interceptors/auth.interceptor";
import { errorInterceptor } from "./core/interceptors/error.interceptor";

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor, errorInterceptor])),
    provideRouter(routes),
    provideSignalFormsConfig({
      classes: {
        "is-invalid": (binding: FormFieldBinding) => binding.state().touched() && binding.state().invalid(),
        "is-valid": (binding: FormFieldBinding) => binding.state().touched() && binding.state().valid(),
      },
    }),
  ],
};
