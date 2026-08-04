import { ChangeDetectionStrategy, Component, inject } from "@angular/core";
import { Router } from "@angular/router";
import { SessionExpiredService } from "../../../core/services/session-expired.service";

@Component({
  selector: "app-session-expired-modal",
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./session-expired-modal.component.html",
  styleUrl: "./session-expired-modal.component.css",
})
export class SessionExpiredModalComponent {
  private readonly sessionExpired = inject(SessionExpiredService);
  private readonly router = inject(Router);

  readonly isVisible = this.sessionExpired.isVisible;

  backToLogin(): void {
    this.sessionExpired.hide();
    this.router.navigate(["/login"]);
  }
}
