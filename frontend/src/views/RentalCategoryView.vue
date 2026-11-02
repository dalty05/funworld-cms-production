<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import WhatsAppButton from "../components/WhatsAppButton.vue";
import { listRentalItems, type RentalItem } from "../api";
import { useHireListStore } from "../stores/hireList";

const props = defineProps<{ category?: string }>();

const route = useRoute();
const store = useHireListStore();

const items = ref<RentalItem[]>([]);
const categoryName = ref<string>("");
const categoryDescription = ref<string | null>(null);
const loading = ref(true);
const notFound = ref(false);

const activeItem = ref<RentalItem | null>(null);
const closeButtonRef = ref<HTMLButtonElement | null>(null);
let previousFocus: HTMLElement | null = null;

const slug = computed(() => String(props.category ?? route.params.category ?? ""));

// Pick the first item with an image to use as the hero image
const heroImage = computed(() => {
  const withImage = items.value.find((i) => i.featured_image_url);
  return withImage ? withImage.featured_image_url : null;
});

async function load(slugValue: string) {
  loading.value = true;
  notFound.value = false;

  try {
    const result = await listRentalItems(slugValue);
    items.value = result.items ?? [];
    categoryName.value = result.category?.name ?? slugValue;
    categoryDescription.value = result.category?.short_description ?? null;
    if (!result.category) notFound.value = true;
  } catch (error) {
    console.error("Rental category loading failed:", error);
    notFound.value = true;
    items.value = [];
  } finally {
    loading.value = false;
  }
}

// ── Quantity helpers ────────────────────────────────────────────
function quantityOf(id: string): number {
  return store.items.find((i) => i.id === id)?.quantity ?? 0;
}

function addFirst(item: RentalItem) {
  store.addItem(item);
}

function increment(item: RentalItem) {
  const current = quantityOf(item.id);
  if (current === 0) store.addItem(item);
  else store.updateQuantity(item.id, current + 1);
}

function decrement(item: RentalItem) {
  const current = quantityOf(item.id);
  if (current <= 1) store.removeItem(item.id);
  else store.updateQuantity(item.id, current - 1);
}

function setQuantity(item: RentalItem, raw: string | number) {
  const n = Math.max(0, Math.min(9999, Math.floor(Number(raw) || 0)));
  if (n === 0) {
    store.removeItem(item.id);
  } else if (quantityOf(item.id) === 0) {
    store.addItem(item);
    if (n > 1) store.updateQuantity(item.id, n);
  } else {
    store.updateQuantity(item.id, n);
  }
}

// ── Modal ───────────────────────────────────────────────────────
function openItem(item: RentalItem) {
  previousFocus = document.activeElement as HTMLElement;
  activeItem.value = item;
  document.body.style.overflow = "hidden";
  nextTick(() => closeButtonRef.value?.focus());
}

function closeModal() {
  activeItem.value = null;
  document.body.style.overflow = "";
  nextTick(() => previousFocus?.focus());
}

function onKeydown(e: KeyboardEvent) {
  if (!activeItem.value) return;
  if (e.key === "Escape") closeModal();
}

onMounted(() => {
  if (slug.value) load(slug.value);
  window.addEventListener("keydown", onKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  document.body.style.overflow = "";
});

watch(slug, (next) => { if (next) load(next); });
</script>

<template>
  <div class="rental-category">
    <!-- HERO — Split layout with featured image -->
    <section class="cat-hero">
      <div class="cat-hero__inner">
        <div class="cat-hero__content">
          <p class="eyebrow">
            <RouterLink to="/rentals" class="eyebrow__crumb">Rentals</RouterLink>
            <span aria-hidden="true"> / </span>
            <span>{{ categoryName || "Category" }}</span>
          </p>
          <h1 class="cat-hero__title">{{ categoryName || "Items for hire" }}</h1>
          <p v-if="categoryDescription" class="cat-hero__lead">
            {{ categoryDescription }}
          </p>
        </div>
        <div class="cat-hero__media">
          <img
            v-if="heroImage"
            :src="heroImage"
            :alt="`${categoryName} highlight`"
          />
          <div v-else class="cat-hero__placeholder" />
        </div>
      </div>
    </section>

    <!-- CATALOGUE -->
    <section class="cat-body">
      <div class="cat-body__inner">
        <!-- Loading -->
        <div v-if="loading" class="item-grid">
          <div v-for="i in 6" :key="i" class="skeleton" aria-hidden="true" />
        </div>

        <!-- Not found -->
        <div v-else-if="notFound" class="empty-state">
          <h2>Category not found</h2>
          <RouterLink to="/rentals" class="btn btn--primary">
            ← Back to all rentals
          </RouterLink>
        </div>

        <!-- Cards -->
        <div v-else-if="items.length" class="item-grid">
          <article
            v-for="item in items"
            :key="item.id"
            class="product-card"
            :class="{ 'product-card--in-list': quantityOf(item.id) > 0 }"
          >
            <button
              type="button"
              class="product-card__media"
              @click="openItem(item)"
              :aria-label="`View details for ${item.name}`"
            >
              <img
                v-if="item.featured_image_url"
                :src="item.featured_image_url"
                :alt="item.name"
                loading="lazy"
              />
              <div v-else class="product-card__placeholder" />
              <span class="product-card__view">View details</span>
            </button>

            <div class="product-card__body">
              <h3 class="product-card__title">{{ item.name }}</h3>
              <p v-if="item.short_description" class="product-card__desc">
                {{ item.short_description }}
              </p>
            </div>

            <!-- Card footer: price + hire control -->
            <div class="product-footer">
              <div class="product-footer__price">
                <template v-if="item.from_price != null">
                  {{ item.currency }} {{ item.from_price.toLocaleString() }}
                  <small>/ {{ item.unit }}</small>
                </template>
                <template v-else>Contact for price</template>
              </div>

              <!-- Quantity 0 → Add Button -->
              <button
                v-if="quantityOf(item.id) === 0"
                type="button"
                class="hire-btn"
                @click="addFirst(item)"
                :aria-label="`Add ${item.name} to hire list`"
              >
                Add
              </button>

              <!-- Quantity > 0 → Sleek stepper -->
              <div
                v-else
                class="qty-stepper"
                role="group"
                :aria-label="`Quantity for ${item.name}`"
              >
                <button
                  type="button"
                  class="qty-stepper__btn"
                  @click="decrement(item)"
                  :aria-label="`Decrease quantity of ${item.name}`"
                >
                  −
                </button>
                <input
                  type="number"
                  class="qty-stepper__input"
                  min="0"
                  max="9999"
                  inputmode="numeric"
                  :value="quantityOf(item.id)"
                  :aria-label="`Quantity of ${item.name}`"
                  @change="setQuantity(item, ($event.target as HTMLInputElement).value)"
                />
                <button
                  type="button"
                  class="qty-stepper__btn"
                  @click="increment(item)"
                  :aria-label="`Increase quantity of ${item.name}`"
                >
                  +
                </button>
              </div>
            </div>
          </article>
        </div>

        <!-- Empty -->
        <div v-else class="empty-state">
          <p>No items published in this category yet.</p>
        </div>
      </div>
    </section>
  </div>

  <!-- ═══════════ MODAL ═══════════ -->
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="activeItem" class="modal-overlay" @click.self="closeModal">
        <div
          class="modal"
          role="dialog"
          aria-modal="true"
          :aria-label="activeItem.name"
        >
          <button
            ref="closeButtonRef"
            type="button"
            class="modal__close"
            @click="closeModal"
            aria-label="Close"
          >
            ✕
          </button>

          <div class="modal__image">
            <img
              v-if="activeItem.featured_image_url"
              :src="activeItem.featured_image_url"
              :alt="activeItem.name"
            />
          </div>

          <div class="modal__body">
            <p class="modal__eyebrow">{{ categoryName }}</p>
            <h2 class="modal__title">{{ activeItem.name }}</h2>

            <p v-if="activeItem.short_description" class="modal__description">
              {{ activeItem.short_description }}
            </p>

            <dl class="modal__specs">
              <div class="modal__spec">
                <dt>From</dt>
                <dd>
                  <template v-if="activeItem.from_price != null">
                    {{ activeItem.currency }}
                    {{ activeItem.from_price.toLocaleString() }}
                  </template>
                  <template v-else>On request</template>
                </dd>
              </div>
              <div class="modal__spec">
                <dt>Unit</dt>
                <dd>{{ activeItem.unit || "—" }}</dd>
              </div>
              <div v-if="activeItem.availability_note" class="modal__spec">
                <dt>Availability</dt>
                <dd>{{ activeItem.availability_note }}</dd>
              </div>
            </dl>

            <div class="modal__qty">
              <span class="modal__qty-label">Quantity</span>

              <button
                v-if="quantityOf(activeItem.id) === 0"
                type="button"
                class="hire-btn"
                @click="addFirst(activeItem)"
              >
                Add
              </button>

              <div
                v-else
                class="qty-stepper"
                role="group"
                aria-label="Quantity"
              >
                <button
                  type="button"
                  class="qty-stepper__btn"
                  @click="decrement(activeItem)"
                  aria-label="Decrease quantity"
                >
                  −
                </button>
                <input
                  type="number"
                  class="qty-stepper__input"
                  min="0"
                  max="9999"
                  inputmode="numeric"
                  :value="quantityOf(activeItem.id)"
                  aria-label="Quantity"
                  @change="setQuantity(activeItem, ($event.target as HTMLInputElement).value)"
                />
                <button
                  type="button"
                  class="qty-stepper__btn"
                  @click="increment(activeItem)"
                  aria-label="Increase quantity"
                >
                  +
                </button>
              </div>
            </div>

            <div class="modal__actions">
              <WhatsAppButton
                :message="`Hello Funworld Events! I'd like to enquire about hiring the ${activeItem.name}.`"
                :source-ref="`rental_item:${activeItem.slug}`"
                variant="ghost"
                label="WhatsApp enquiry"
              />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── Wrapper ──────────────────────────────────────────────── */
.rental-category {
  display: block;
  background: var(--color-ivory);
  min-height: 100vh;
}

/* ── HERO (Split Layout) ──────────────────────────────────── */
.cat-hero {
  border-bottom: 1px solid var(--color-clay);
  background: var(--color-ivory);
}

.cat-hero__inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 4rem 1.25rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
}

.cat-hero__content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.cat-hero__title {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3.2rem);
  font-weight: 400;
  line-height: 1.1;
  color: var(--color-charcoal);
  margin: 0.75rem 0 1rem;
}

.cat-hero__lead {
  max-width: 50ch;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: 1.05rem;
  line-height: 1.6;
  margin: 0;
}

.cat-hero__media {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(26, 20, 23, 0.03);
  box-shadow: 0 12px 32px rgba(26, 20, 23, 0.06);
}

.cat-hero__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cat-hero__placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(26, 20, 23, 0.05), rgba(26, 20, 23, 0.02));
}

.eyebrow {
  font-family: var(--font-body);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-clay);
  margin: 0;
}

.eyebrow__crumb {
  color: var(--color-text-muted);
  text-decoration: none;
}
.eyebrow__crumb:hover {
  color: var(--color-plum);
}

/* ── CATALOGUE BODY ───────────────────────────────────────── */
.cat-body {
  padding: 3.5rem 0 5rem;
}

.cat-body__inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 1.25rem;
}

/* ── Card grid ─────────────────────────────────────────────── */
.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.product-card {
  display: flex;
  flex-direction: column;
  background: var(--color-ivory);
  border: 1px solid var(--color-clay);
  border-radius: 4px;
  overflow: hidden;
  transition: box-shadow 200ms ease, transform 200ms ease, border-color 200ms ease;
}

.product-card:hover {
  box-shadow: 0 12px 32px rgba(26, 20, 23, 0.08);
  transform: translateY(-2px);
}

.product-card--in-list {
  border-color: var(--color-plum);
}

.product-card__media {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  padding: 0;
  border: none;
  background: rgba(26, 20, 23, 0.05);
  cursor: pointer;
  overflow: hidden;
}

.product-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.product-card__media:hover img {
  transform: scale(1.04);
}

.product-card__placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(26, 20, 23, 0.05), rgba(26, 20, 23, 0.02));
}

.product-card__view {
  position: absolute;
  bottom: 0.75rem;
  left: 0.75rem;
  padding: 0.35rem 0.75rem;
  font-family: var(--font-body);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: rgba(252, 249, 244, 0.95);
  color: var(--color-plum);
  border-radius: 2px;
  opacity: 0;
  transform: translateY(4px);
  transition: opacity 200ms ease, transform 200ms ease;
}

.product-card__media:hover .product-card__view,
.product-card__media:focus-visible .product-card__view {
  opacity: 1;
  transform: translateY(0);
}

.product-card__body {
  padding: 1.25rem 1.25rem 1rem;
  flex: 1;
}

.product-card__title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 500;
  line-height: 1.3;
  color: var(--color-charcoal);
  margin: 0 0 0.35rem;
}

.product-card__desc {
  font-family: var(--font-body);
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--color-text-muted);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Card footer ──────────────────────────────────────────── */
.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: 0 1.25rem 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-clay);
}

.product-footer__price {
  font-family: var(--font-body);
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-charcoal);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.product-footer__price small {
  display: block;
  font-weight: 400;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
}

/* ── Hire button (Clean, pill-shaped) ─────────────────────── */
.hire-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1.25rem;
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--color-ivory);
  background: var(--color-plum);
  border: 1px solid var(--color-plum);
  border-radius: 50px; /* Pill shape */
  cursor: pointer;
  white-space: nowrap;
  transition: background 180ms ease, border-color 180ms ease;
}

.hire-btn:hover {
  background: var(--color-charcoal);
  border-color: var(--color-charcoal);
}

.hire-btn:focus-visible {
  outline: 2px solid var(--color-gold);
  outline-offset: 2px;
}

/* ── Quantity stepper (Sleek, borderless look) ────────────── */
.qty-stepper {
  display: inline-flex;
  align-items: center;
  background: rgba(26, 20, 23, 0.04);
  border-radius: 50px;
  padding: 0.25rem;
}

.qty-stepper__btn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-charcoal);
  border: none;
  border-radius: 50%;
  font-family: var(--font-body);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 160ms ease;
}

.qty-stepper__btn:hover:not(:disabled) {
  background: rgba(26, 20, 23, 0.08);
}

.qty-stepper__btn:focus-visible {
  outline: 2px solid var(--color-gold);
}

.qty-stepper__input {
  width: 32px;
  border: none;
  background: transparent;
  color: var(--color-charcoal);
  text-align: center;
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  -moz-appearance: textfield;
  appearance: textfield;
}

.qty-stepper__input::-webkit-outer-spin-button,
.qty-stepper__input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.qty-stepper__input:focus-visible {
  outline: 2px solid var(--color-gold);
  border-radius: 2px;
}

/* ── Skeleton + empty ─────────────────────────────────────── */
.skeleton {
  aspect-ratio: 4 / 3;
  background: linear-gradient(90deg, rgba(26, 20, 23, 0.05), rgba(26, 20, 23, 0.09), rgba(26, 20, 23, 0.05));
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
  border-radius: 4px;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  text-align: center;
  padding: 5rem 1rem;
  color: var(--color-text-muted);
}

.empty-state h2 {
  font-family: var(--font-display);
  font-weight: 400;
  color: var(--color-charcoal);
  margin: 0 0 1rem;
}

/* ── Modal ────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: rgba(26, 20, 23, 0.55);
  backdrop-filter: blur(4px);
}

.modal {
  position: relative;
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
  background: var(--color-ivory);
  border-radius: 6px;
  box-shadow: 0 24px 64px rgba(26, 20, 23, 0.28);
}

.modal__close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 2;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(252, 249, 244, 0.92);
  border: none;
  font-size: 1.1rem;
  color: var(--color-charcoal);
  cursor: pointer;
  border-radius: 50%;
}

.modal__close:hover {
  background: var(--color-ivory);
}

.modal__close:focus-visible {
  outline: 2px solid var(--color-gold);
}

.modal__image {
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: rgba(26, 20, 23, 0.05);
}

.modal__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.modal__body {
  padding: 1.75rem 2rem 2rem;
}

.modal__eyebrow {
  font-family: var(--font-body);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-clay);
  margin: 0 0 0.5rem;
}

.modal__title {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 400;
  line-height: 1.2;
  color: var(--color-charcoal);
  margin: 0 0 0.75rem;
}

.modal__description {
  font-family: var(--font-body);
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--color-text-muted);
  margin: 0 0 1.5rem;
}

.modal__specs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem 1.5rem;
  margin: 0 0 1.5rem;
  padding: 1.25rem 0;
  border-top: 1px solid var(--color-clay);
  border-bottom: 1px solid var(--color-clay);
}

.modal__spec {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.modal__spec dt {
  font-family: var(--font-body);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.modal__spec dd {
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: var(--color-charcoal);
  margin: 0;
  font-variant-numeric: tabular-nums;
}

.modal__qty {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: 0 0 1.5rem;
}

.modal__qty-label {
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-charcoal);
}

.modal__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.modal__actions :deep(.whatsapp-btn),
.modal__actions .btn {
  flex: 1 1 auto;
  min-width: 140px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.25rem;
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 4px;
  border: 1px solid transparent;
  cursor: pointer;
  text-decoration: none;
  transition: background 180ms ease, color 180ms ease, border-color 180ms ease;
}

.btn--primary {
  background: var(--color-plum);
  color: var(--color-ivory);
}

.btn--primary:hover:not(:disabled) {
  background: var(--color-charcoal);
}

/* ── Modal transition ─────────────────────────────────────── */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 240ms ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal,
.modal-fade-leave-active .modal {
  transition: transform 240ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.modal-fade-enter-from .modal,
.modal-fade-leave-to .modal {
  transform: translateY(12px) scale(0.98);
}

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 860px) {
  .cat-hero__inner {
    grid-template-columns: 1fr;
    gap: 2rem;
    padding: 3rem 1.25rem;
  }
  
  .cat-hero__media {
    aspect-ratio: 16 / 9;
  }
}

@media (max-width: 600px) {
  .item-grid {
    grid-template-columns: 1fr;
  }

  .product-footer {
    flex-direction: row;
    align-items: center;
  }

  .hire-btn {
    width: auto;
  }

  .qty-stepper {
    align-self: auto;
  }

  .modal-overlay {
    padding: 0;
    align-items: flex-end;
  }

  .modal {
    max-width: 100%;
    max-height: 94vh;
    border-radius: 16px 16px 0 0;
  }

  .modal__body {
    padding: 1.25rem 1.25rem 1.5rem;
  }

  .modal-fade-enter-from .modal,
  .modal-fade-leave-to .modal {
    transform: translateY(100%);
  }
}

/* ── Reduced motion ───────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .product-card,
  .product-card__media img,
  .product-card__view,
  .qty-stepper__btn,
  .hire-btn,
  .btn,
  .modal {
    transition: none;
  }

  .product-card:hover { transform: none; }
  .product-card__media:hover img { transform: none; }

  .modal-fade-enter-from .modal,
  .modal-fade-leave-to .modal {
    transform: none;
  }

  .skeleton { animation: none; }
}
</style>