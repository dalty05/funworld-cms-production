<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { listInventoryCategories, listInventory, type InventoryItem } from "../../api";

export interface InventoryLine {
  inventory_item_id: string;
  quantity: number;
  notes?: string;
}

const props = defineProps<{
  modelValue: InventoryLine[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: InventoryLine[]): void;
}>();

const categories = ref<any[]>([]);
const items = ref<InventoryItem[]>([]);
const search = ref("");
const openPicker = ref(false);

onMounted(async () => {
  categories.value = await listInventoryCategories();
});

const filteredItems = computed(() => {
  const q = search.value.toLowerCase().trim();
  if (!q) return items.value;
  return items.value.filter((i) => i.name.toLowerCase().includes(q));
});

async function loadItems() {
  items.value = await listInventory();
}

function open() {
  openPicker.value = true;
  loadItems();
}

function addItem(item: InventoryItem) {
  const copy = [...props.modelValue];
  const existing = copy.find((x) => x.inventory_item_id === item.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    copy.push({ inventory_item_id: item.id, quantity: 1, notes: "" });
  }
  emit("update:modelValue", copy);
}

function removeLine(idx: number) {
  const copy = [...props.modelValue];
  copy.splice(idx, 1);
  emit("update:modelValue", copy);
}

function updateQuantity(idx: number, value: number) {
  const copy = [...props.modelValue];
  copy[idx].quantity = Math.max(1, value);
  emit("update:modelValue", copy);
}

function itemName(id: string) {
  const found = items.value.find((i) => i.id === id);
  return found?.name ?? id.slice(0, 8) + "…";
}

function itemUnit(id: string) {
  const found = items.value.find((i) => i.id === id);
  return found?.unit ?? "";
}

// Load item names on mount for existing lines
onMounted(async () => {
  if (props.modelValue.length) {
    await loadItems();
  }
});
</script>

<template>
  <div class="inv-picker">
    <div v-if="modelValue.length" class="inv-picker__list">
      <div
        v-for="(line, idx) in modelValue"
        :key="line.inventory_item_id"
        class="inv-line"
      >
        <div class="inv-line__name">
          {{ itemName(line.inventory_item_id) }}
          <span v-if="itemUnit(line.inventory_item_id)" class="inv-line__unit">
            ({{ itemUnit(line.inventory_item_id) }})
          </span>
        </div>
        <input
          :value="line.quantity"
          type="number"
          min="1"
          class="inv-line__qty"
          @input="updateQuantity(idx, Number(($event.target as HTMLInputElement).value))"
        />
        <button class="inv-line__remove" @click.prevent="removeLine(idx)">×</button>
      </div>
    </div>

    <button type="button" class="inv-picker__add" @click.prevent="open">
      + Add inventory item
    </button>

    <Teleport to="body">
      <div v-if="openPicker" class="inv-modal" @click.self="openPicker = false">
        <div class="inv-modal__panel">
          <header class="inv-modal__head">
            <h3>Select inventory</h3>
            <button @click="openPicker = false">×</button>
          </header>
          <input
            v-model="search"
            class="inv-modal__search"
            placeholder="Search items…"
          />
          <ul class="inv-modal__list">
            <li
              v-for="item in filteredItems"
              :key="item.id"
              @click="addItem(item); openPicker = false"
            >
              <div>
                <strong>{{ item.name }}</strong>
                <span class="inv-modal__cat">{{ item.category_slug }}</span>
              </div>
              <span class="inv-modal__qty">
                {{ item.quantity_owned }} in stock
                <span v-if="item.unit_price_hint">
                  · {{ item.currency }} {{ item.unit_price_hint }} {{ item.unit }}
                </span>
              </span>
            </li>
          </ul>
          <p v-if="!filteredItems.length" class="inv-modal__empty">
            No items. Create some in Inventory first.
          </p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.inv-picker { display: grid; gap: var(--sp-3); }
.inv-picker__list { display: grid; gap: var(--sp-2); }
.inv-line {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  background: var(--color-ivory);
  border-radius: var(--radius-md);
}
.inv-line__name { font-size: var(--fs-sm); color: var(--color-plum); }
.inv-line__unit { font-size: var(--fs-xs); color: var(--color-text-muted); }
.inv-line__qty {
  width: 72px;
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-sm);
  text-align: right;
}
.inv-line__remove { color: var(--color-coral); font-size: 18px; padding: 0 6px; }
.inv-picker__add {
  justify-self: start;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  border: 1px dashed var(--color-border);
  color: var(--color-gold);
  font-size: var(--fs-sm);
  font-weight: 500;
}
.inv-picker__add:hover { background: rgba(201, 164, 92, 0.06); }

.inv-modal {
  position: fixed; inset: 0; z-index: 1100;
  background: rgba(43, 15, 46, 0.5);
  backdrop-filter: blur(4px);
  display: grid; place-items: center; padding: var(--sp-5);
}
.inv-modal__panel {
  width: min(620px, 100%);
  max-height: 80vh;
  background: #fff;
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.inv-modal__head {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--color-border-soft);
}
.inv-modal__head h3 { margin: 0; font-family: var(--font-display); font-size: var(--fs-lg); }
.inv-modal__head button { font-size: 24px; color: var(--color-text-muted); }
.inv-modal__search {
  margin: var(--sp-4) var(--sp-5);
  padding: 0.6rem 0.9rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  font-size: var(--fs-sm);
}
.inv-modal__list {
  list-style: none;
  padding: 0 var(--sp-3) var(--sp-5);
  margin: 0;
  overflow-y: auto;
  flex: 1;
}
.inv-modal__list li {
  padding: var(--sp-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-3);
}
.inv-modal__list li:hover { background: rgba(201, 164, 92, 0.06); }
.inv-modal__cat { font-size: var(--fs-xs); color: var(--color-text-muted); margin-left: var(--sp-2); }
.inv-modal__qty { font-size: var(--fs-xs); color: var(--color-text-muted); }
.inv-modal__empty { padding: 0 var(--sp-5) var(--sp-5); color: var(--color-text-muted); font-size: var(--fs-sm); }
</style>