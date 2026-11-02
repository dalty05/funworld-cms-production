<script setup lang="ts">
import { computed } from "vue";

interface LineItem {
  description: string;
  quantity: number | string;
  unit_price: number | string;
  notes?: string;
}

const props = defineProps<{
  modelValue: LineItem[];
  currency?: string;
  discount?: number | string;
  tax?: number | string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: LineItem[]): void;
  (e: "update:discount", value: number): void;
  (e: "update:tax", value: number): void;
}>();

const currency = computed(() => props.currency ?? "KES");

function addRow() {
  emit("update:modelValue", [
    ...props.modelValue,
    { description: "", quantity: 1, unit_price: 0 },
  ]);
}

function removeRow(i: number) {
  const copy = [...props.modelValue];
  copy.splice(i, 1);
  emit("update:modelValue", copy);
}

function updateField(i: number, key: keyof LineItem, value: any) {
  const copy = [...props.modelValue];
  (copy[i] as any)[key] = value;
  emit("update:modelValue", copy);
}

const subtotal = computed(() =>
  props.modelValue.reduce((sum, row) => {
    const q = Number(row.quantity) || 0;
    const p = Number(row.unit_price) || 0;
    return sum + q * p;
  }, 0)
);

const total = computed(() =>
  subtotal.value - (Number(props.discount) || 0) + (Number(props.tax) || 0)
);

function money(n: number) {
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
</script>

<template>
  <div class="editor">
    <table class="editor__table">
      <thead>
        <tr>
          <th style="width: 44%">Description</th>
          <th style="width: 12%">Qty</th>
          <th style="width: 18%">Unit price</th>
          <th style="width: 18%" class="right">Total</th>
          <th style="width: 8%"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in modelValue" :key="i">
          <td>
            <input v-model="row.description" placeholder="Item description" @input="updateField(i, 'description', row.description)" />
            <input v-model="row.notes" placeholder="Optional notes" class="editor__notes" @input="updateField(i, 'notes', row.notes)" />
          </td>
          <td><input v-model.number="row.quantity" type="number" min="0" step="any" @input="updateField(i, 'quantity', row.quantity)" /></td>
          <td><input v-model.number="row.unit_price" type="number" min="0" step="any" @input="updateField(i, 'unit_price', row.unit_price)" /></td>
          <td class="right">{{ currency }} {{ money((Number(row.quantity) || 0) * (Number(row.unit_price) || 0)) }}</td>
          <td><button class="editor__remove" @click.prevent="removeRow(i)" aria-label="Remove">×</button></td>
        </tr>
      </tbody>
    </table>

    <button type="button" class="editor__add" @click.prevent="addRow">+ Add line item</button>

    <div class="editor__totals">
      <div class="editor__totals-row">
        <span>Subtotal</span>
        <span>{{ currency }} {{ money(subtotal) }}</span>
      </div>
      <div class="editor__totals-row">
        <label>Discount</label>
        <input :value="discount" type="number" min="0" step="any" @input="$emit('update:discount', Number(($event.target as HTMLInputElement).value))" />
      </div>
      <div class="editor__totals-row">
        <label>Tax</label>
        <input :value="tax" type="number" min="0" step="any" @input="$emit('update:tax', Number(($event.target as HTMLInputElement).value))" />
      </div>
      <div class="editor__totals-row editor__totals-row--total">
        <span>Total</span>
        <span>{{ currency }} {{ money(total) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.editor { display: grid; gap: var(--sp-4); }
.editor__table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); }
.editor__table th {
  padding: var(--sp-2) var(--sp-2);
  text-align: left;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-gold);
  border-bottom: 1px solid var(--color-border-soft);
}
.editor__table th.right, .editor__table td.right { text-align: right; }
.editor__table td { padding: var(--sp-2); border-bottom: 1px solid var(--color-border-soft); vertical-align: top; }
.editor__table input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-soft);
  background: #fff;
  font-size: var(--fs-sm);
}
.editor__table input:focus { outline: none; border-color: var(--color-gold); }
.editor__notes { margin-top: 4px; font-size: var(--fs-xs); }
.editor__remove { color: var(--color-coral); font-size: 20px; line-height: 1; padding: 0 6px; }
.editor__add {
  justify-self: start;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  border: 1px dashed var(--color-border);
  color: var(--color-gold);
  font-size: var(--fs-sm);
  font-weight: 500;
}
.editor__add:hover { background: rgba(201, 164, 92, 0.06); }
.editor__totals {
  margin-left: auto;
  min-width: 300px;
  display: grid;
  gap: var(--sp-2);
}
.editor__totals-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--fs-sm);
  padding: var(--sp-2) 0;
  color: var(--color-text-muted);
}
.editor__totals-row input {
  width: 120px;
  padding: 0.4rem 0.6rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-soft);
  text-align: right;
}
.editor__totals-row--total {
  border-top: 2px solid var(--color-gold);
  padding-top: var(--sp-3);
  margin-top: var(--sp-2);
  font-size: var(--fs-lg);
  font-family: var(--font-display);
  color: var(--color-plum);
  font-weight: 600;
}
</style>