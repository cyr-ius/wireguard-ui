/**
 * Angular application configuration.
 * Zoneless change detection using signals.
 * HTTP client with fetch API backend.
 * Router with hash-based navigation.
 */

import { provideHttpClient, withFetch, withInterceptors } from "@angular/common/http";
import { ApplicationConfig, provideZonelessChangeDetection } from "@angular/core";
import { provideRouter, withHashLocation } from "@angular/router";

import { routes } from "./app.routes";
import { authInterceptor } from "./core/interceptors/auth.interceptor";

export const appConfig: ApplicationConfig = {
  providers: [provideZonelessChangeDetection(), provideHttpClient(withFetch(), withInterceptors([authInterceptor])), provideRouter(routes, withHashLocation())],
};
