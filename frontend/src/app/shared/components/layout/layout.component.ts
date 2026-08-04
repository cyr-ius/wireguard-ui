/**
 * Main layout shell with sidebar navigation.
 * Sidebar items are conditionally shown based on user role (mirrors backend guards).
 */

import { Component, computed, DestroyRef, inject, signal } from "@angular/core";
import { RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";
import { AuthService } from "../../../core/services/auth.service";
import { ThemeMode, ThemeService } from "../../../core/services/theme.service";

// Below this viewport width the sidebar auto-collapses to the icon rail;
// the user can still expand it manually, and it re-collapses next time the
// breakpoint is crossed. Mirrors the CSS breakpoint in layout.component.css.
const COLLAPSE_BREAKPOINT = "(max-width: 900px)";

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
  private readonly destroyRef = inject(DestroyRef);

  private readonly narrowViewport =
    typeof window !== "undefined" ? window.matchMedia(COLLAPSE_BREAKPOINT) : null;
  readonly sidebarCollapsed = signal(this.narrowViewport?.matches ?? false);

  constructor() {
    if (!this.narrowViewport) return;
    const onChange = (event: MediaQueryListEvent) => this.sidebarCollapsed.set(event.matches);
    this.narrowViewport.addEventListener("change", onChange);
    this.destroyRef.onDestroy(() => this.narrowViewport?.removeEventListener("change", onChange));
  }
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
