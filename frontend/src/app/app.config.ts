/**
 * Angular application configuration.
 * Zoneless change detection using signals.
 * HTTP client with fetch API backend.
 * Router with hash-based navigation.
 */

import {
  ApplicationConfig,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideRouter, withHashLocation } from '@angular/router';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    // Zoneless change detection powered by signals
    provideZonelessChangeDetection(),

    // HTTP client using the modern Fetch API backend + JWT interceptor
    provideHttpClient(withFetch(), withInterceptors([authInterceptor])),

    // Router with hash location for SPA inside static file server
    provideRouter(routes, withHashLocation()),

    // Async animations
    provideAnimationsAsync(),
  ],
};
