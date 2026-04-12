import { Injectable, computed, effect, signal } from "@angular/core";

export type ThemeMode = "auto" | "light" | "dark";
type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "wg_theme_mode";

@Injectable({ providedIn: "root" })
export class ThemeService {
  private readonly mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  private readonly _systemTheme = signal<ResolvedTheme>(this.mediaQuery.matches ? "dark" : "light");
  private readonly _mode = signal<ThemeMode>(this.loadMode());

  readonly mode = this._mode.asReadonly();
  readonly resolvedTheme = computed<ResolvedTheme>(() => {
    const mode = this._mode();
    if (mode === "auto") return this._systemTheme();
    return mode;
  });

  constructor() {
    this.mediaQuery.addEventListener("change", (event) => {
      this._systemTheme.set(event.matches ? "dark" : "light");
    });

    effect(() => {
      const mode = this._mode();
      const resolved = this.resolvedTheme();

      document.documentElement.setAttribute("data-theme", resolved);
      document.documentElement.setAttribute("data-theme-mode", mode);
      document.documentElement.setAttribute("data-bs-theme", resolved);

      localStorage.setItem(STORAGE_KEY, mode);
    });
  }

  setMode(mode: ThemeMode): void {
    this._mode.set(mode);
  }

  private loadMode(): ThemeMode {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === "dark" || raw === "light" || raw === "auto") {
      return raw;
    }
    return "auto";
  }
}
