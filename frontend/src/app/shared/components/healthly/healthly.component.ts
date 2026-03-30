import { Component, inject } from "@angular/core";
import { HealthService } from "../../../core/services/health.service";

@Component({
  selector: "app-healthly",
  standalone: true,
  imports: [],
  templateUrl: "./healthly.component.html",
  styleUrl: "./healthly.component.css",
})
export class HealthlyComponent {
  readonly health = inject(HealthService);

  retry(): void {
    this.health.checkNow();
  }
}
