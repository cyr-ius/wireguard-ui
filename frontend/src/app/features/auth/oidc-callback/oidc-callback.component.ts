import { Component, OnInit, inject, signal } from "@angular/core";
import { ActivatedRoute, Router, RouterLink } from "@angular/router";
import { ErrorField } from "../../../core/applets/error-field.component";
import { ApiError } from "../../../core/models/api-error.model";
import { OidcService } from "../../../core/services/api.service";
import { AuthService } from "../../../core/services/auth.service";

@Component({
  selector: "app-oidc-callback",
  standalone: true,
  imports: [RouterLink, ErrorField],
  templateUrl: "./oidc-callback.component.html",
  styleUrl: "./oidc-callback.component.css",
})
export class OidcCallbackComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly oidc = inject(OidcService);
  private readonly auth = inject(AuthService);

  readonly error = signal<ApiError | null>(null);

  ngOnInit(): void {
    const code = this.route.snapshot.queryParamMap.get("code");
    const state = this.route.snapshot.queryParamMap.get("state");
    const expectedState = sessionStorage.getItem("oidc_state");
    sessionStorage.removeItem("oidc_state");

    if (!code) {
      this.error.set({ code: "oidc", message: "Missing authorization code." } as ApiError);
      return;
    }
    if (!state || !expectedState || state !== expectedState) {
      this.error.set({ code: "oidc", message: "Invalid OIDC state." } as ApiError);
      return;
    }

    this.oidc.callback(code).subscribe({
      next: (response) => {
        this.auth.loginWithTokenResponse(response);
        this.router.navigate(["/"]);
      },
      error: (err) => {
        this.error.set((err as ApiError) ?? "OIDC authentication failed.");
      },
    });
  }
}
