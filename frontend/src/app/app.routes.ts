/**
 * Application routes.
 * Guards enforce authentication and admin-only access
 * directly in the routing layer (mirrors backend restrictions).
 */

import { Routes } from "@angular/router";
import { adminGuard } from "./core/guards/admin.guard";
import { authGuard } from "./core/guards/auth.guard";

export const routes: Routes = [
  {
    path: "login",
    loadComponent: () =>
      import("./features/auth/login/login.component").then(
        (m) => m.LoginComponent,
      ),
  },
  {
    path: "auth/callback",
    loadComponent: () =>
      import("./features/auth/oidc-callback/oidc-callback.component").then(
        (m) => m.OidcCallbackComponent,
      ),
  },
  {
    path: "",
    canActivate: [authGuard],
    loadComponent: () =>
      import("./shared/components/layout/layout.component").then(
        (m) => m.LayoutComponent,
      ),
    children: [
      { path: "", redirectTo: "status", pathMatch: "full" },
      {
        path: "status",
        loadComponent: () =>
          import("./features/status/status.component").then(
            (m) => m.StatusComponent,
          ),
      },
      {
        path: "clients",
        canActivate: [adminGuard],
        loadComponent: () =>
          import("./features/clients/clients.component").then(
            (m) => m.ClientsComponent,
          ),
      },
      {
        path: "server",
        canActivate: [adminGuard],
        loadComponent: () =>
          import("./features/server/server.component").then(
            (m) => m.ServerComponent,
          ),
      },
      {
        path: "settings",
        canActivate: [adminGuard],
        loadComponent: () =>
          import("./features/settings/settings.component").then(
            (m) => m.SettingsComponent,
          ),
      },
      {
        path: "users",
        canActivate: [adminGuard],
        loadComponent: () =>
          import("./features/users/users.component").then(
            (m) => m.UsersComponent,
          ),
      },
      {
        path: "oidc",
        canActivate: [adminGuard],
        loadComponent: () =>
          import("./features/oidc/oidc.component").then((m) => m.OidcComponent),
      },
      {
        path: "about",
        loadComponent: () =>
          import("./features/about/about.component").then(
            (m) => m.AboutComponent,
          ),
      },
    ],
  },
  { path: "**", redirectTo: "" },
];
