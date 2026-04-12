/**
 * Main layout shell with sidebar navigation.
 * Sidebar items are conditionally shown based on user role (mirrors backend guards).
 */

import { Component, computed, inject, signal } from "@angular/core";
import { RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";
import { AuthService } from "../../../core/services/auth.service";
import { ThemeMode, ThemeService } from "../../../core/services/theme.service";

@Component({
  selector: "app-layout",
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: "./layout.component.html",
  styleUrl: "./layout.component.css",
})
export class LayoutComponent {
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  readonly sidebarCollapsed = signal(false);
  readonly themeButtonIcon = computed(() => {
    const mode = this.theme.mode();
    if (mode === "dark") {
      return "bi-moon-stars-fill";
    }
    if (mode === "light") {
      return "bi-sun-fill";
    }
    return "bi-circle-half";
  });
  readonly themeButtonLabel = computed(() => {
    const mode = this.theme.mode();
    if (mode === "dark") {
      return "Dark";
    }
    if (mode === "light") {
      return "Light";
    }
    return "Auto";
  });

  toggleSidebar(): void {
    this.sidebarCollapsed.update((v) => !v);
  }

  logout(): void {
    this.auth.logout();
  }

  changeThemeMode(value: string): void {
    if (value === "auto" || value === "light" || value === "dark") {
      this.theme.setMode(value as ThemeMode);
    }
  }

  cycleThemeMode(): void {
    const currentMode = this.theme.mode();
    const nextMode: ThemeMode = currentMode === "auto" ? "dark" : currentMode === "dark" ? "light" : "auto";
    this.theme.setMode(nextMode);
  }
}
