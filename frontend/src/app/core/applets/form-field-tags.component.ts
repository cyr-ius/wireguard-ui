import { CommonModule } from "@angular/common";
import { Component, effect, input, model, signal } from "@angular/core";
import { FormValueControl, ValidationError, WithOptionalField } from "@angular/forms/signals";

@Component({
  selector: "form-tags-field",
  imports: [CommonModule],
  template: `
    <div [class]="containerClass()">
      <div
        class="flex-wrap align-items-start gap-2 p-2 border rounded"
        [class.is-invalid]="touched() && invalid()"
        [class.is-valid]="touched() && !invalid()"
      >
        <!-- Tags inside the field -->
        @for (tag of value(); track tag) {
          <span class="badge bg-primary mt-1 mx-1">
            {{ tag }}
            <button
              type="button"
              class="btn-close btn-close-white p-0"
              (click)="removeTag(tag)"
              [disabled]="disabled() || readonly()"
              aria-label="Delete"
            ></button>
          </span>
        }

        <!-- Input at the same level as tags -->
        <input
          type="text"
          class="form-control border-0 flex-grow-1 p-0"
          [placeholder]="value().length === 0 ? label() : ''"
          [value]="inputValue()"
          (input)="onInputChange($event)"
          (keydown.enter)="onEnter($event)"
          (blur)="onBlur()"
          [disabled]="disabled() || readonly()"
          [attr.aria-label]="label()"
          style="min-width: 150px; outline: none; box-shadow: none; width: auto; display: inline; background-color: transparent; border: none;"
        />
      </div>

      <!-- Suggestions below -->
      @if (selectOptions().length > 0 && suggestionEnable() && !readonly()) {
        <div class="mt-2 small text-muted">
          Suggestions :
          @for (option of selectOptions(); track option) {
            @if (!value().includes(option)) {
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary ms-1"
                (click)="addTagFromSuggestion(option)"
                [disabled]="disabled() || readonly()"
              >
                + {{ option }}
              </button>
            }
          }
        </div>
      }
    </div>
  `,
  styles: `
    .input-group {
      background-color: white;
      border: 1px solid #dee2e6;
      transition:
        border-color 0.15s ease-in-out,
        box-shadow 0.15s ease-in-out;
    }

    .input-group:focus-within {
      border-color: #86b7fe;
      box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
    }

    .input-group.is-invalid {
      border-color: #dc3545;
    }

    .input-group.is-invalid:focus-within {
      box-shadow: 0 0 0 0.25rem rgba(220, 53, 69, 0.25);
    }

    .input-group.is-valid {
      border-color: #198754;
    }

    .input-group.is-valid:focus-within {
      box-shadow: 0 0 0 0.25rem rgba(25, 135, 84, 0.25);
    }

    .input-group input {
      padding: 0.375rem 0.75rem !important;
    }

    .badge {
      white-space: nowrap;
    }
  `,
})
export class FormTagsField implements FormValueControl<string[]> {
  value = model<string[]>([]);
  errors = input<readonly WithOptionalField<ValidationError>[]>([]);
  disabled = input<boolean>(false);
  touched = model<boolean>(false);
  required = model<boolean>(false);
  invalid = model<boolean>(false);
  readonly = model<boolean>(false);

  readonly selectOptions = input<string[]>([]);
  readonly label = input.required<string>();
  readonly suggestionEnable = input<boolean>(false);
  readonly stopPropagation = input<boolean>(true);

  class = input<string>();
  inputValue = signal<string>("");
  containerClass = signal<string>("");

  constructor() {
    effect(() => {
      if (this.disabled()) {
        this.value.set([]);
        this.inputValue.set("");
      }
      this.updateContainerClass();
    });

    effect(() => {
      this.updateContainerClass();
    });
  }

  private updateContainerClass() {
    let classes = this.class() || "";
    if (this.touched() && this.invalid()) {
      classes += " is-invalid";
    } else if (this.touched() && !this.invalid()) {
      classes += " is-valid";
    }
    this.containerClass.set(classes);
  }

  onInputChange(event: Event) {
    event.stopPropagation();
    const target = event.target as HTMLInputElement;
    this.inputValue.set(target.value);
  }

  onEnter(event: Event) {
    event.preventDefault();
    if (this.stopPropagation()) {
      event.stopPropagation();
    }
    this.addTag();
  }

  onBlur() {
    this.touched.set(true);
    this.addTag();
  }

  addTag() {
    const newValue = this.inputValue().trim();
    if (newValue && !this.value().includes(newValue)) {
      this.value.update((v) => [...v, newValue]);
      this.inputValue.set("");
    }
  }

  addTagFromSuggestion(option: string) {
    if (!this.value().includes(option)) {
      this.value.update((v) => [...v, option]);
    }
  }

  removeTag(tag: string) {
    this.value.update((v) => v.filter((t) => t !== tag));
  }
}
