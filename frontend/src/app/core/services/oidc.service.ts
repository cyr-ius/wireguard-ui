import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";
import { ApiService } from "./api.service";
import {
  OidcAdminSettings,
  OidcPublicConfig,
  TokenResponse,
} from "../../shared/models/api.models";

@Injectable({ providedIn: "root" })
export class OidcService {
  private readonly api = inject(ApiService);

  getAdminSettings(): Observable<OidcAdminSettings> {
    return this.api.getOidcSettings();
  }

  saveAdminSettings(data: OidcAdminSettings): Observable<OidcAdminSettings> {
    return this.api.updateOidcSettings(data);
  }

  getPublicConfig(): Observable<OidcPublicConfig> {
    return this.api.getOidcPublicConfig();
  }

  callback(code: string): Observable<TokenResponse> {
    return this.api.oidcCallback(code);
  }
}
