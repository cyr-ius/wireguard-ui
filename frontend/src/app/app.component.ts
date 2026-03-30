/**
 * Root application component.
 * Minimal shell - routing handles everything.
 */

import { Component, inject } from "@angular/core";
import { RouterOutlet } from "@angular/router";
import { HealthService } from "./core/services/health.service";
import { ThemeService } from "./core/services/theme.service";
import { HealthlyComponent } from "./shared/components/healthly/healthly.component";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [RouterOutlet, HealthlyComponent],
  template: ` @if (health.isDown()) {
      <app-healthly />
    } @else {
      <router-outlet />
    }`,
})
export class AppComponent {
  // Initializes theme handling globally at app startup.
  private readonly _theme = inject(ThemeService);
  readonly health = inject(HealthService);
}
