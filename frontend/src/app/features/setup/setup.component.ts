import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from "@angular/core";
import { Router } from "@angular/router";
import { form, FormField, FormRoot, max, min, readonly, required } from "@angular/forms/signals";
import { firstValueFrom } from "rxjs";
import { ErrorField } from "../../core/applets/error-field.component";
import { FormExtraFields } from "../../core/applets/form-extra-fields.component";
import { ApiError } from "../../core/models/api-error.model";
import { ServerService, SettingsService } from "../../core/services/api.service";
import { SetupService } from "../../core/services/setup.service";

@Component({
  selector: "app-setup",
  standalone: true,
  imports: [FormRoot, FormField, FormExtraFields, ErrorField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./setup.component.html",
  styleUrls: ["./setup.component.css"],
})
export class SetupComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly setupService = inject(SetupService);
  private readonly serverService = inject(ServerService);
  private readonly settingsService = inject(SettingsService);

  readonly checking = signal(true);
  readonly step = signal<1 | 2>(1);
  readonly error = signal<ApiError | null>(null);
  readonly showPrivateKey = signal(false);

  private readonly serverInit = {
    address: "192.168.1.0/24",
    listen_port: 51820,
    private_key: "",
    public_key: "",
    postup:
      "EXT_IF=$(ip route show default | awk '/default/ {print $5; exit}'); iptables -A FORWARD -i wg0 -o $EXT_IF -j ACCEPT; iptables -A FORWARD -i $EXT_IF -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -A POSTROUTING -o $EXT_IF -j MASQUERADE",
    postdown:
      "EXT_IF=$(ip route show default | awk '/default/ {print $5; exit}'); iptables -D FORWARD -i wg0 -o $EXT_IF -j ACCEPT; iptables -D FORWARD -i $EXT_IF -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -D POSTROUTING -o $EXT_IF -j MASQUERADE",
  };
  readonly serverModel = signal({ ...this.serverInit });
  readonly serverForm = form(
    this.serverModel,
    (p) => {
      required(p.address, { message: "L'adresse réseau est requise" });
      required(p.listen_port, { message: "Le port d'écoute est requis" });
      min(p.listen_port, 1, { message: "Le port doit être supérieur à 0" });
      max(p.listen_port, 65535, { message: "Le port doit être inférieur à 65536" });
      required(p.private_key, { message: "Générez la paire de clés du serveur" });
      required(p.public_key, { message: "Générez la paire de clés du serveur" });
      readonly(p.public_key);
    },
    {
      submission: {
        action: async (f) => this.saveServer(f),
      },
    },
  );

  private readonly endpointModel = signal({ endpoint_address: "" });
  readonly endpointForm = form(
    this.endpointModel,
    (e) => {
      required(e.endpoint_address, {
        message: "L'adresse d'endpoint est requise (nom d'hôte public ou IP)",
      });
    },
    {
      submission: {
        action: async (f) => this.saveEndpoint(f),
      },
    },
  );

  ngOnInit(): void {
    this.setupService.check().subscribe({
      next: (status) => {
        this.step.set(status.serverConfigured ? 2 : 1);
        this.checking.set(false);
      },
      error: () => this.checking.set(false),
    });
  }

  generateKeypair(): void {
    this.serverService.generateKeypair().subscribe({
      next: (keys) => {
        this.serverForm.private_key().value.set(keys.private_key);
        this.serverForm.public_key().value.set(keys.public_key);
      },
      error: (err) => this.error.set((err as ApiError) ?? "Échec de la génération des clés"),
    });
  }

  async saveServer(f: any): Promise<void> {
    this.error.set(null);
    try {
      await firstValueFrom(this.serverService.upsert(f().value()));
      this.step.set(2);
    } catch (err: unknown) {
      this.error.set((err as ApiError) ?? "Échec de l'enregistrement de la configuration serveur");
    }
  }

  async saveEndpoint(f: any): Promise<void> {
    this.error.set(null);
    try {
      await firstValueFrom(this.settingsService.update(f().value()));
      await this.router.navigate(["/status"]);
    } catch (err: unknown) {
      this.error.set((err as ApiError) ?? "Échec de l'enregistrement de l'adresse d'endpoint");
    }
  }

  backToServerStep(): void {
    this.error.set(null);
    this.step.set(1);
  }
}
