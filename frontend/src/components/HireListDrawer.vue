<!-- HireListDrawer.vue -->
<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useHireListStore } from "../stores/hireList";
import { useSettingsStore } from "../stores/settings";

const store = useHireListStore();
const settings = useSettingsStore();

onMounted(() => settings.load());

type Step = "items" | "event" | "contact" | "submitted";
const step = ref<Step>("items");

// ── form state (resets when drawer closes fully) ─────────────────
const event = reactive({
  date: "",
  location: "",
  type: "",
  notes: "",
});
const contact = reactive({
  name: "",
  phone: "",
  email: "",
});

const submitting = ref(false);
const errorMsg = ref<string | null>(null);
const enquiryRef = ref<string | null>(null);
const whatsappLink = ref<string | null>(null);

const canGoToEvent = computed(() => store.totalItems > 0);
const canSubmit = computed(
  () => contact.name.trim().length > 0 && contact.phone.trim().length > 0,
);

const subtotalDisplay = computed(() =>
  new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: store.currency,
    maximumFractionDigits: 0,
  }).format(store.totalPrice),
);

// WhatsApp fallback message — same body as server, pre-filled client-side
const fallbackWhatsAppMsg = computed(() => {
  if (store.items.length === 0) return "";
  const lines = [
    "Hello Funworld Events! I'd like to hire the following items:",
    "",
  ];
  store.items.forEach((i) => {
    lines.push(
      `• ${i.quantity} × ${i.name} — ${i.currency} ${Number(i.from_price).toLocaleString()} / ${i.unit}`,
    );
  });
  lines.push("");
  if (event.date) lines.push(`Event date: ${event.date}`);
  if (event.location) lines.push(`Location: ${event.location}`);
  if (event.type) lines.push(`Event type: ${event.type}`);
  lines.push("");
  lines.push("Could you confirm availability and total pricing?");
  return lines.join("\n");
});

// ── drawer close resets to step 1 but keeps cart contents ────────
function close() {
  store.closeDrawer();
}

watch(
  () => store.isOpen,
  (open) => {
    if (!open) {
      step.value = "items";
      errorMsg.value = null;
    }
  },
);

function goEvent() {
  if (canGoToEvent.value) step.value = "event";
}
function goContact() {
  step.value = "contact";
}
function backToItems() {
  step.value = "items";
}
function backToEvent() {
  step.value = "event";
}

async function submit() {
  if (!canSubmit.value || submitting.value) return;
  submitting.value = true;
  errorMsg.value = null;

  try {
    const res = await fetch(
      `${import.meta.env.VITE_API_BASE_URL ?? "/api/v1"}/enquiries/rentals`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: store.items.map((i) => ({
            id: i.id,
            slug: i.slug,
            name: i.name,
            quantity: i.quantity,
            from_price: Number(i.from_price) || 0,
            unit: i.unit,
            currency: i.currency,
          })),
          event: { ...event },
          contact: { ...contact },
        }),
      },
    );

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.error?.message ?? "Could not submit right now.");
    }

    const data = await res.json();
    enquiryRef.value = data?.data?.enquiry_ref ?? null;
    whatsappLink.value = data?.data?.whatsapp_link ?? null;

    store.clearList();
    step.value = "submitted";
  } catch (e: any) {
    errorMsg.value =
      e?.message ?? "Something went wrong. Please try again or use WhatsApp.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <!-- Floating toggle — hidden when cart empty AND drawer closed -->
  <!-- <button
    v-show="store.totalItems > 0 && !store.isOpen"
    class="cart-toggle"
    @click="store.openDrawer()"
    aria-label="Open Hire List"
  >
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <path d="M16 10a4 4 0 0 1-8 0" />
    </svg>
    <span class="cart-badge">{{ store.totalItems }}</span>
  </button> -->

  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="store.isOpen"
        class="drawer-overlay"
      >
        <aside
          class="drawer-panel"
          role="dialog"
          aria-label="Your Hire List"
        >
          <!-- Header -->
          <header class="drawer-header">
            <div>
              <p class="eyebrow">Your Hire List</p>
              <h2 v-if="step === 'items'">Review items</h2>
              <h2 v-else-if="step === 'event'">Event details</h2>
              <h2 v-else-if="step === 'contact'">Your details</h2>
              <h2 v-else>Enquiry submitted</h2>
            </div>
            <button class="close-btn" @click="close" aria-label="Close">✕</button>
          </header>

          <!-- Progress -->
          <div v-if="step !== 'submitted'" class="progress">
            <span :class="{ active: step === 'items' }">1. Items</span>
            <span :class="{ active: step === 'event' }">2. Event</span>
            <span :class="{ active: step === 'contact' }">3. Contact</span>
          </div>

          <!-- Body -->
          <div class="drawer-content">
            <!-- STEP 1: ITEMS -->
            <div v-if="step === 'items'">
              <div v-if="store.items.length === 0" class="empty-cart">
                <p>Your hire list is empty.</p>
                <p>Browse the catalogue to add items.</p>
              </div>

              <div v-else class="cart-items">
                <div
                  v-for="item in store.items"
                  :key="item.id"
                  class="cart-item"
                >
                  <div class="cart-item__img">
                    <img
                      v-if="item.featured_image_url"
                      :src="item.featured_image_url"
                      :alt="item.name"
                    />
                  </div>
                  <div class="cart-item__info">
                    <h4>{{ item.name }}</h4>
                    <p class="cart-item__price">
                      {{ item.currency }}
                      {{ Number(item.from_price).toLocaleString() }} /
                      {{ item.unit }}
                    </p>
                    <div class="cart-item__controls">
                      <button
                        @click="store.updateQuantity(item.id, item.quantity - 1)"
                        aria-label="Decrease quantity"
                      >−</button>
                      <input
                        type="number"
                        min="1"
                        max="9999"
                        :value="item.quantity"
                        @change="(e) => store.updateQuantity(item.id, Number((e.target as HTMLInputElement).value))"
                        aria-label="Quantity"
                      />
                      <button
                        @click="store.updateQuantity(item.id, item.quantity + 1)"
                        aria-label="Increase quantity"
                      >+</button>
                    </div>
                  </div>
                  <button
                    class="remove-btn"
                    @click="store.removeItem(item.id)"
                    aria-label="Remove item"
                  >✕</button>
                </div>
              </div>
            </div>

            <!-- STEP 2: EVENT DETAILS -->
            <div v-else-if="step === 'event'" class="form-step">
              <label>
                <span>Event date</span>
                <input v-model="event.date" type="date" />
              </label>
              <label>
                <span>Location / venue</span>
                <input
                  v-model="event.location"
                  type="text"
                  placeholder="e.g. Karen, Nairobi"
                />
              </label>
              <label>
                <span>Event type</span>
                <select v-model="event.type">
                  <option value="">Select…</option>
                  <option>Wedding</option>
                  <option>Corporate</option>
                  <option>Kids party</option>
                  <option>School funday</option>
                  <option>Other</option>
                </select>
              </label>
              <label>
                <span>Notes <em>(optional)</em></span>
                <textarea
                  v-model="event.notes"
                  rows="3"
                  placeholder="Any special requirements?"
                />
              </label>
            </div>

            <!-- STEP 3: CONTACT -->
            <div v-else-if="step === 'contact'" class="form-step">
              <label>
                <span>Full name *</span>
                <input v-model="contact.name" type="text" required />
              </label>
              <label>
                <span>Phone *</span>
                <input
                  v-model="contact.phone"
                  type="tel"
                  placeholder="+254 7XX XXX XXX"
                  required
                />
              </label>
              <label>
                <span>Email <em>(optional)</em></span>
                <input v-model="contact.email" type="email" />
              </label>
              <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
            </div>

            <!-- STEP 4: SUBMITTED -->
            <div v-else class="submitted-step">
              <div class="check">✓</div>
              <h3>Enquiry received</h3>
              <p>
                Your hire list has been sent to Funworld Events. We'll reply
                on WhatsApp or by phone to confirm availability and pricing.
              </p>
              <p v-if="enquiryRef" class="ref">
                Reference: <strong>{{ enquiryRef }}</strong>
              </p>
              <a
                v-if="whatsappLink"
                :href="whatsappLink"
                target="_blank"
                rel="noopener noreferrer"
                class="btn btn--primary"
              >
                Open in WhatsApp
              </a>
              <button class="btn btn--ghost" @click="close">
                Close
              </button>
            </div>
          </div>

          <!-- Footer -->
          <footer v-if="step !== 'submitted'" class="drawer-footer">
            <div v-if="store.items.length > 0" class="total-row">
              <span>Estimated subtotal</span>
              <strong>{{ subtotalDisplay }}</strong>
            </div>
            <p v-if="store.items.length > 0" class="disclaimer">
              Final price confirmed on WhatsApp based on dates & delivery.
            </p>

            <!-- Nav buttons per step -->
            <div class="footer-actions">
              <button
                v-if="step === 'event'"
                class="btn btn--ghost"
                @click="backToItems"
              >← Back</button>
              <button
                v-if="step === 'contact'"
                class="btn btn--ghost"
                @click="backToEvent"
              >← Back</button>

              <button
                v-if="step === 'items' && store.items.length > 0"
                class="btn btn--primary"
                @click="goEvent"
              >Continue →</button>
              <button
                v-if="step === 'event'"
                class="btn btn--primary"
                @click="goContact"
              >Continue →</button>
              <button
                v-if="step === 'contact'"
                class="btn btn--primary"
                :disabled="!canSubmit || submitting"
                @click="submit"
              >
                {{ submitting ? "Sending…" : "Submit enquiry" }}
              </button>
            </div>

            <!-- WhatsApp escape hatch, always available -->
            <a
              v-if="store.items.length > 0"
              :href="`https://wa.me/${settings.whatsappPhone()}?text=${encodeURIComponent(fallbackWhatsAppMsg)}`"
              target="_blank"
              rel="noopener noreferrer"
              class="wa-link"
            >
              Or send this list on WhatsApp instead →
            </a>
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Toggle */
/* .cart-toggle {
  position: fixed; bottom: 2rem; left: 2rem;
  width: 60px; height: 60px; border-radius: 50%;
  background: var(--color-plum, #2b0f2e); color: #fff;
  border: none; box-shadow: 0 8px 24px rgba(43, 15, 46, 0.3);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  z-index: 90; transition: transform 200ms;
}
.cart-toggle:hover { transform: scale(1.05); }
.cart-badge {
  position: absolute; top: -5px; right: -5px;
  background: var(--color-gold, #d4af6a);
  color: var(--color-charcoal, #1a1417);
  font-family: var(--font-body, Inter, sans-serif);
  font-weight: 700; font-size: 0.75rem;
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
} */




.drawer-header {
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;

  padding: 1.35rem 1.5rem;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;

  border-bottom: 1px solid rgba(26, 20, 23, 0.1);
}

.drawer-header > div {
  flex: 1;
  min-width: 0;
}

.drawer-header .eyebrow {
  margin: 0 0 0.4rem;
}

.drawer-header h2 {
  margin: 0;
  font-family: var(--font-display, Fraunces, serif);
  font-size: 1.45rem;
  line-height: 1.2;
  font-weight: 400;
  color: var(--color-charcoal, #1a1417);
}

.close-btn {
  flex: 0 0 36px;
  width: 36px;
  height: 36px;

  display: inline-flex;
  align-items: center;
  justify-content: center;

  padding: 0;
  margin: 0;

  background: rgba(43, 15, 46, 0.06);
  border: 1px solid rgba(43, 15, 46, 0.08);
  border-radius: 50%;

  color: var(--color-charcoal, #1a1417);
  font-size: 16px;
  line-height: 1;

  cursor: pointer;
  transition: background 180ms ease;
}

.close-btn:hover {
  background: rgba(43, 15, 46, 0.12);
}

.close-btn:focus-visible {
  outline: 2px solid var(--color-gold);
  outline-offset: 3px;
}

/* Persistent right-side hire panel */

.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;

  display: flex;
  align-items: center;
  justify-content: flex-end;

  padding: 24px;

  background: transparent;
  backdrop-filter: none;

  /* Allow interaction with the website behind the panel */
  pointer-events: none;
}

.drawer-panel {
  width: min(460px, calc(100vw - 48px));
  height: min(720px, calc(100dvh - 48px));
  max-height: calc(100dvh - 48px);

  display: flex;
  flex-direction: column;

  background: var(--color-ivory, #fcf9f4);

  border: 1px solid rgba(26, 20, 23, 0.08);
  border-radius: 16px;

  box-shadow:
    0 18px 60px rgba(26, 20, 23, 0.16),
    0 4px 14px rgba(26, 20, 23, 0.08);

  overflow: hidden;
  pointer-events: auto;
  overscroll-behavior: contain;
}

/* Panel entrance and exit */

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 250ms ease;
}

.drawer-enter-active .drawer-panel,
.drawer-leave-active .drawer-panel {
  transition:
    transform 280ms cubic-bezier(0.2, 0.8, 0.2, 1),
    opacity 280ms ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .drawer-panel,
.drawer-leave-to .drawer-panel {
  transform: translateX(24px);
  opacity: 0;
}

/* Mobile */

@media (max-width: 600px) {
  .drawer-overlay {
    padding: 12px;
  }

  .drawer-panel {
    width: calc(100vw - 24px);
    height: min(720px, calc(100dvh - 24px));
    max-height: calc(100dvh - 24px);
    border-radius: 14px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .drawer-enter-active,
  .drawer-leave-active,
  .drawer-panel {
    transition: none;
  }
}

/* Progress */
.progress {
  display: flex; gap: 0.75rem; padding: 0.75rem 1.5rem;
  border-bottom: 1px solid rgba(26, 20, 23, 0.06);
  font-family: var(--font-body); font-size: 0.72rem;
  color: var(--color-text-muted, #888);
}
.progress span { padding-bottom: 0.25rem; border-bottom: 2px solid transparent; }
.progress span.active { color: var(--color-plum); border-bottom-color: var(--color-gold); }

/* Body */
.drawer-content { flex: 1; overflow-y: auto; padding: 1.5rem; }
.empty-cart { text-align: center; color: var(--color-text-muted); margin-top: 3rem; }

.cart-item {
  display: flex; gap: 1rem; padding-bottom: 1.5rem;
  margin-bottom: 1.5rem; border-bottom: 1px solid rgba(26,20,23,0.08);
}
.cart-item__img {
  width: 70px; height: 70px; border-radius: 6px; overflow: hidden;
  flex-shrink: 0; background: #eee;
}
.cart-item__img img { width: 100%; height: 100%; object-fit: cover; }
.cart-item__info { flex: 1; min-width: 0; }
.cart-item__info h4 {
  margin: 0 0 0.25rem;
  font-family: var(--font-display); font-size: 1.05rem;
}
.cart-item__price {
  font-family: var(--font-body); font-size: 0.85rem;
  color: var(--color-text-muted); margin: 0 0 0.6rem;
}
.cart-item__controls {
  display: inline-flex; align-items: center;
  background: #fff; border: 1px solid rgba(0,0,0,0.1);
  border-radius: 4px; overflow: hidden;
}
.cart-item__controls button {
  width: 30px; height: 30px; border: none; background: transparent;
  cursor: pointer; font-size: 1rem;
}
.cart-item__controls input {
  width: 44px; height: 30px; border: none; text-align: center;
  font-family: var(--font-body); font-size: 0.9rem; font-weight: 600;
  background: transparent;
}
.remove-btn {
  background: none; border: none; color: #c0392b;
  cursor: pointer; font-size: 0.9rem; align-self: flex-start;
}

/* Form */
.form-step { display: flex; flex-direction: column; gap: 1rem; }
.form-step label { display: flex; flex-direction: column; gap: 0.35rem; }
.form-step label span {
  font-family: var(--font-body); font-size: 0.8rem; font-weight: 600;
  color: var(--color-charcoal);
}
.form-step label span em { color: var(--color-text-muted); font-style: normal; font-weight: 400; }
.form-step input,
.form-step select,
.form-step textarea {
  font-family: var(--font-body); font-size: 0.95rem;
  padding: 0.65rem 0.75rem; border: 1px solid rgba(26,20,23,0.15);
  border-radius: 4px; background: #fff; color: var(--color-charcoal);
}
.form-step input:focus,
.form-step select:focus,
.form-step textarea:focus {
  outline: 2px solid var(--color-gold); outline-offset: 1px;
  border-color: transparent;
}
.error { color: #c0392b; font-family: var(--font-body); font-size: 0.85rem; margin: 0; }

/* Submitted */
.submitted-step { text-align: center; padding-top: 1.5rem; }
.check {
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--color-sage, #7a8b6f); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; margin: 0 auto 1rem;
}
.submitted-step h3 {
  font-family: var(--font-display); font-weight: 400;
  font-size: 1.4rem; margin: 0 0 0.75rem;
}
.submitted-step p {
  font-family: var(--font-body); font-size: 0.92rem;
  color: var(--color-text-muted); margin: 0 0 1rem; line-height: 1.55;
}
.submitted-step .ref {
  font-size: 0.85rem; color: var(--color-charcoal);
  background: #fff; display: inline-block; padding: 0.35rem 0.75rem;
  border-radius: 4px; margin-bottom: 1.25rem;
}
.submitted-step .btn { display: block; width: 100%; margin-bottom: 0.5rem; }

/* Footer */
.drawer-footer {
  padding: 1.25rem 1.5rem;
  background: #fff;
  border-top: 1px solid rgba(26, 20, 23, 0.1);
}
.total-row {
  display: flex; justify-content: space-between;
  font-family: var(--font-body); font-size: 1rem; margin-bottom: 0.35rem;
}
.total-row strong { font-variant-numeric: tabular-nums; }
.disclaimer {
  font-size: 0.72rem; color: var(--color-text-muted);
  margin: 0 0 1rem;
}
.footer-actions { display: flex; gap: 0.5rem; }
.footer-actions .btn { flex: 1; }
.wa-link {
  display: block; text-align: center; margin-top: 0.75rem;
  font-family: var(--font-body); font-size: 0.78rem;
  color: var(--color-text-muted); text-decoration: underline;
}

.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0.7rem 1rem; font-family: var(--font-body);
  font-size: 0.88rem; font-weight: 600; border-radius: 2px;
  border: 1px solid transparent; cursor: pointer;
  transition: all 180ms ease; text-decoration: none;
}
.btn--primary { background: var(--color-plum); color: #fff; }
.btn--primary:hover:not(:disabled) { background: var(--color-charcoal); }
.btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn--ghost {
  background: transparent; color: var(--color-plum);
  border-color: var(--color-plum);
}
.btn--ghost:hover { background: var(--color-plum); color: #fff; }
.btn:focus-visible { outline: 2px solid var(--color-gold); outline-offset: 2px; }

/* Transitions */
/* .drawer-enter-active, .drawer-leave-active { transition: opacity 300ms; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-active .drawer-panel,
.drawer-leave-active .drawer-panel {
  transition: transform 300ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.drawer-enter-from .drawer-panel,
.drawer-leave-to .drawer-panel { transform: translateX(-100%); }

@media (max-width: 600px) {
  .cart-toggle { bottom: 1rem; left: 1rem; width: 54px; height: 54px; }
  .drawer-panel { max-width: 100%; }
  .drawer-overlay { align-items: flex-end; }
  .drawer-panel {
    height: 92vh; border-radius: 16px 16px 0 0;
  }
  .drawer-enter-from .drawer-panel,
  .drawer-leave-to .drawer-panel { transform: translateY(100%); }
} */


.drawer-panel,
.drawer-panel * {
  box-sizing: border-box;
}

.drawer-header,
.progress,
.drawer-footer {
  flex-shrink: 0;
}

.progress {
  padding: 0.85rem 1.5rem;
  align-items: center;
}

.drawer-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1.35rem 1.5rem;
  overscroll-behavior: contain;
}

.drawer-footer {
  flex-shrink: 0;
}









@media (prefers-reduced-motion: reduce) {
  .cart-toggle, .drawer-panel, .btn { transition: none; }
}
</style>