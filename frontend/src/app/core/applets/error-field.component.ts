import { Component, input } from "@angular/core";
import { ApiError } from "../models/api-error.model";

@Component({
  selector: "div-error",
  imports: [],
  template: `
    @if (errorRef(); as error) {
      @if (error.details && error.details.length > 0) {
        <div class="alert alert-danger">
          <ul class="mb-0">
            @for (detail of error.details; track detail.kind) {
              <li>
                @if (detail.kind) {
                  <strong>{{ detail.kind }}</strong>:
                }
                {{ detail.message }}
              </li>
            }
          </ul>
        </div>
      } @else {
        <div class="alert alert-danger">
          <i class="bi bi-exclamation-triangle"></i>{{ error.message }}
        </div>
      }
    }
    @if (successRef(); as string) {
      <div class="alert alert-success">
        <i class="bi bi-check-circle-fill me-2"></i>{{ successRef() }}
      </div>
    }
  `,
})
export class ErrorField {
  readonly errorRef = input<ApiError | null>(null);
  readonly successRef = input<string | null>(null);
}
