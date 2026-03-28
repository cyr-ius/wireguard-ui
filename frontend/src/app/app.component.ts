/**
 * Root application component.
 * Minimal shell - routing handles everything.
 */

import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class AppComponent {
  // Initializes theme handling globally at app startup.
  private readonly _theme = inject(ThemeService);
}
