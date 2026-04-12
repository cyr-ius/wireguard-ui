import { Injectable, signal } from "@angular/core";

@Injectable({ providedIn: "root" })
export class SessionExpiredService {
  /** True when the session-expired modal should be visible */
  readonly isVisible = signal(false);

  show() {
    if (!this.isVisible()) {
      this.isVisible.set(true);
    }
  }

  hide() {
    this.isVisible.set(false);
  }
}
