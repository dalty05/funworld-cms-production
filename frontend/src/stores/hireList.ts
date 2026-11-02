import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { RentalItem } from "../api";

export interface HireItem extends RentalItem {
  quantity: number;
}

const STORAGE_KEY = "funworld_hire_list";

export const useHireListStore = defineStore("hireList", () => {
  // ── hydrate from localStorage ───────────────────────────────
  let parsed: HireItem[] = [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) parsed = JSON.parse(raw);
  } catch {
    parsed = [];
  }

  const items = ref<HireItem[]>(parsed);
  const isOpen = ref(false);       // drawer visibility
  const justAddedId = ref<string | null>(null); // for pulse animation on card

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items.value));
    } catch {
      /* quota — ignore */
    }
  }

  function addItem(item: RentalItem) {
    const existing = items.value.find((i) => i.id === item.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      items.value.push({ ...item, quantity: 1 });
    }
    justAddedId.value = item.id;
    setTimeout(() => { justAddedId.value = null; }, 1200);
    persist();
  }

  function removeItem(id: string) {
    items.value = items.value.filter((i) => i.id !== id);
    persist();
  }

  function updateQuantity(id: string, qty: number) {
    const item = items.value.find((i) => i.id === id);
    if (!item) return;
    if (qty <= 0) { removeItem(id); return; }
    item.quantity = Math.min(qty, 9999);
    persist();
  }

  function clearList() {
    items.value = [];
    persist();
  }

  function openDrawer() { isOpen.value = true; }
  function closeDrawer() { isOpen.value = false; }
  function toggleDrawer() { isOpen.value = !isOpen.value; }

  const totalItems = computed(() =>
    items.value.reduce((acc, i) => acc + i.quantity, 0),
  );
  const totalPrice = computed(() =>
    items.value.reduce(
      (acc, i) => acc + (Number(i.from_price) || 0) * i.quantity,
      0,
    ),
  );
  const currency = computed(() =>
    items.value[0]?.currency ?? "KES",
  );

  return {
    items,
    isOpen,
    justAddedId,
    addItem,
    removeItem,
    updateQuantity,
    clearList,
    openDrawer,
    closeDrawer,
    toggleDrawer,
    totalItems,
    totalPrice,
    currency,
  };
});