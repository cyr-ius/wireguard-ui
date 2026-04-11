import { Component, computed, input } from "@angular/core";
import { createMetadataKey, FieldTree } from "@angular/forms/signals";

export const FIELD_INFO = createMetadataKey<string>();

@Component({
  selector: "form-extra-fields",
  imports: [],
  template: `
    @let state = fieldRef()();
    @if (state.touched() && state.errors().length) {
      <div>
        @for (error of state.errors(); track $index) {
          {{ error.message }}
        }
      </div>
    }
    @if (helpMessage()) {
      <div class="form-text">{{ helpMessage() }}</div>
    }
  `,
})
export class FormExtraFieldsComponent<T> {
  readonly fieldRef = input.required<FieldTree<T>>();

  helpMessage = computed(() => {
    const field = this.fieldRef()();
    return field.metadata(FIELD_INFO)?.()!;
  });
}
