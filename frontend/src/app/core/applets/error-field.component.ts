import { Component, input } from "@angular/core";
import { ApiError } from "../../shared/models/api-error.model";

@Component({
  selector: "div-error",
  imports: [],
  template: `
    @if (errorRef(); as error) {
      @if (error.details && error.details.length > 0) {
        <div class="alert alert-danger">
          <ul class="mb-0">
            @for (detail of error.details; track detail.field) {
              <li>
                @if (detail.field) {
                  <strong>{{ detail.field }}</strong
                  >:
                }
                {{ detail.message }}
              </li>
            }
          </ul>
        </div>
      } @else {
        <div class="alert alert-danger">
          <i class="bi bi-exclamation-triangle"></i>
          {{ error.message }}
        </div>
      }
    }
  `,
})
export class ErrorField {
  readonly errorRef = input<ApiError | null>(null);
}
