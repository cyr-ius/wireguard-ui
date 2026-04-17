import { Component, effect, input, model } from '@angular/core';
import { FormValueControl, ValidationError, WithOptionalField } from '@angular/forms/signals';

@Component({
  selector: 'form-multiselect-field',
  imports: [],
  template: `
    <select
      [class]="class()"
      (input)="onSelected($event)"
      [aria-label]="label()"
      [disabled]="disabled()"
      (blur)="touched.set(true)"
      [attr.aria-invalid]="invalid()"
      [attr.aria-required]="required()"
      [class.is-invalid]="touched() && invalid()"
      [class.is-valid]="touched() && !invalid()"
      multiple
    >
      @for (option of selectOptions(); track $index) {
      <option [value]="option" [selected]="value().includes(option)">
        {{ option }}
      </option>
      }
    </select>
  `,
})
export class FormMultiselectField implements FormValueControl<string[]>{
  value = model<string[]>([]);
  errors = input<readonly WithOptionalField<ValidationError>[]>([]);
  disabled = input<boolean>(false);
  touched = model<boolean>(false);
  required = model<boolean>(false);
  invalid = model<boolean>(false);

  readonly selectOptions = input.required<string[]>();
  readonly label = input.required<string>();
  class = input<string>();

  constructor() {
    effect(() => {
      if (this.disabled()) {
        this.value.set([]);
      }
    });
  }

  onSelected(e: any) {
    const selectedValue = Array.from(e.target!.options)
      .filter((option: any) => option.selected)
      .map((option: any) => option.value);
    this.value.set(selectedValue);
  }
}
