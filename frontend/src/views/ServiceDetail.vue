<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { http } from "../api";
import WhatsAppButton from "../components/WhatsAppButton.vue";

// ─── Types ──────────────────────────────────────────────────────
interface ServiceItem {
  slug: string;
  name: string;
  short_description: string | null;
  long_description: string | null;
  featured_image_url: string | null;
  gallery: string[] | null;
  price_note: string | null;
  tags: string[] | null;
  seo_title: string | null;
  seo_description: string | null;
}

interface ServiceCategory {
  slug: string;
  name: string;
  short_description: string | null;
  long_description: string | null;
  hero_image_url: string | null;
  seo_title: string | null;
  seo_description: string | null;
  services: ServiceItem[];
}

// ─── State ──────────────────────────────────────────────────────
const route = useRoute();
const category = ref<ServiceCategory | null>(null);
const loading = ref(true);
const error = ref("");

const slug = computed(() => route.params.slug as string);
const initialServiceSlug = computed(() => route.params.serviceSlug as string | undefined);

// ─── Category hero image ────────────────────────────────────────

// Priority:
// 1. Dedicated category hero image.
// 2. First service with a featured image.
// 3. No image (show placeholder).

const heroImage = computed(() => {
  if (!category.value) return null;

  return (
    category.value.hero_image_url ||
    category.value.services?.find(
      (service) => service.featured_image_url
    )?.featured_image_url ||
    null
  );
});


// Modal state
const activeService = ref<ServiceItem | null>(null);
const modalOpen = computed(() => activeService.value !== null);
const modalRef = ref<HTMLElement | null>(null);
const closeButtonRef = ref<HTMLElement | null>(null);
let previousFocus: HTMLElement | null = null;

// ─── Data loading ───────────────────────────────────────────────
async function load() {
  loading.value = true;
  error.value = "";
  category.value = null;
  try {
    const { data } = await http.get(`/services/categories/${slug.value}`);
    category.value = data.data;
  } catch {
    error.value = "Category not found.";
  } finally {
    loading.value = false;
  }
}

// ─── Modal controls ─────────────────────────────────────────────
function openService(s: ServiceItem) {
  previousFocus = document.activeElement as HTMLElement;
  activeService.value = s;
  document.body.style.overflow = "hidden"; // prevent background scroll
  nextTick(() => closeButtonRef.value?.focus());
}

function closeModal() {
  activeService.value = null;
  document.body.style.overflow = "";
  // Restore focus for keyboard users
  nextTick(() => previousFocus?.focus());
}

function onKeydown(e: KeyboardEvent) {
  if (!modalOpen.value) return;
  if (e.key === "Escape") closeModal();
  if (e.key === "Tab") trapFocus(e);
}

function trapFocus(e: KeyboardEvent) {
  if (!modalRef.value) return;
  const focusable = modalRef.value.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}

// ─── Lifecycle ──────────────────────────────────────────────────
onMounted(async () => {
  await load();
  window.addEventListener("keydown", onKeydown);
  // If a service was in the URL, open its modal directly
  if (initialServiceSlug.value && category.value) {
    const match = category.value.services.find(
      (s) => s.slug === initialServiceSlug.value
    );
    if (match) openService(match);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  document.body.style.overflow = "";
});

watch(slug, () => load());

// ─── Helpers ────────────────────────────────────────────────────
function priceDisplay(price: string | null): string | null {
  if (!price) return null;
  return price;
}
</script>

<template>
  <div class="sdp">
    <!-- ═══════════ LOADING / ERROR ═══════════ -->
    <div v-if="loading" class="state-msg">
      <p>Loading…</p>
    </div>

    <div v-else-if="error || !category" class="state-msg state-msg--error">
      <p>{{ error || "Category not found." }}</p>
      <RouterLink to="/services" class="btn btn--dark">← Back to services</RouterLink>
    </div>

    <!-- ═══════════ CONTENT ═══════════ -->
    <template v-else>
      <!-- ── HERO SPLIT ── -->
      <section class="hero">
        <div class="container container--editorial">
          <div class="hero__grid">
            <!-- Left: text -->
            <div class="hero__copy">
              <p class="eyebrow">
                <RouterLink to="/services" class="crumb">Services</RouterLink>
                <span class="crumb-sep">/</span>
                <span>{{ category.name }}</span>
              </p>
              <h1 class="hero__title">{{ category.name }}</h1>
              <p v-if="category.short_description" class="lead">
                {{ category.short_description }}
              </p>
              <p v-if="category.long_description" class="hero__long">
                {{ category.long_description }}
              </p>

              <div class="hero__actions">
                <a href="#catalog" class="btn btn--dark">Browse services ↓</a>
                <WhatsAppButton
                  :message="`Hello Funworld Events! I'd like to enquire about your ${category.name} services.`"
                  :source-ref="`svc_category_${category.slug}`"
                  variant="ghost"
                  label="WhatsApp us"
                />
              </div>
            </div>

            <!-- hero image -->

            <!-- Right: dynamically selected hero image -->
            <div
              v-if="heroImage"
              class="hero__media"
            >
              <img
                :src="heroImage"
                :alt="category.name"
                loading="eager"
                fetchpriority="high"
              />
            </div>

            <div
              v-else
              class="hero__media hero__media--placeholder"
            >
              <span>{{ category.name }}</span>
            </div>

          </div>
        </div>
      </section>

      <!-- ── SERVICES CATALOG ── -->
      <section id="catalog" class="section-catalog">
        <div class="container container--editorial">
          <header class="section-head">
            <p class="eyebrow">What's included</p>
            <h2 class="section-title">
              {{ category.services.length }} service{{ category.services.length === 1 ? "" : "s" }} in {{ category.name }}.
            </h2>
          </header>

          <p v-if="!category.services.length" class="empty-msg">
            No services published in this category yet.
          </p>

          <div v-else class="svc-grid">
            <button
              v-for="(s, i) in category.services"
              :key="s.slug"
              class="svc-card"
              type="button"
              :aria-label="`View details for ${s.name}`"
              @click="openService(s)"
            >
              <div class="svc-card__media">
                <img
                  v-if="s.featured_image_url"
                  :src="s.featured_image_url"
                  :alt="s.name"
                  loading="lazy"
                />
                <div v-else class="svc-card__placeholder" />
                <span class="svc-card__num">{{ String(i + 1).padStart(2, "0") }}</span>
              </div>

              <div class="svc-card__body">
                <h3 class="svc-card__title">{{ s.name }}</h3>
                <p v-if="s.short_description" class="svc-card__desc">
                  {{ s.short_description }}
                </p>
                <div class="svc-card__foot">
                  <span v-if="s.price_note" class="svc-card__price">
                    {{ s.price_note }}
                  </span>
                  <span class="svc-card__cta">View details →</span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </section>
    </template>

    <!-- ═══════════ MODAL ═══════════ -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="modalOpen && activeService"
          class="modal-backdrop"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="`svc-title-${activeService.slug}`"
          @click.self="closeModal"
        >
          <div ref="modalRef" class="modal">
            <button
              ref="closeButtonRef"
              class="modal__close"
              type="button"
              aria-label="Close"
              @click="closeModal"
            >
              ✕
            </button>

            <div class="modal__grid">
              <!-- Left: image -->
              <div class="modal__media">
                <img
                  v-if="activeService.featured_image_url"
                  :src="activeService.featured_image_url"
                  :alt="activeService.name"
                />
                <div v-else class="modal__media-placeholder" />
              </div>

              <!-- Right: content -->
              <div class="modal__content">
                <p class="eyebrow">{{ category?.name }}</p>
                <h2
                  :id="`svc-title-${activeService.slug}`"
                  class="modal__title"
                >
                  {{ activeService.name }}
                </h2>
                <p v-if="activeService.short_description" class="modal__lead">
                  {{ activeService.short_description }}
                </p>

                <div
                  v-if="activeService.long_description"
                  class="modal__body"
                  v-html="activeService.long_description"
                />

                <div
                  v-if="activeService.tags?.length"
                  class="modal__tags"
                >
                  <span
                    v-for="tag in activeService.tags"
                    :key="tag"
                    class="modal__tag"
                  >
                    {{ tag }}
                  </span>
                </div>

                <p v-if="activeService.price_note" class="modal__price">
                  {{ activeService.price_note }}
                </p>

                <div class="modal__actions">
                  <RouterLink
                    :to="`/get-a-quote?service=${activeService.slug}&category=${category?.slug}`"
                    class="btn btn--dark"
                    @click="closeModal"
                  >
                    Request a quote
                  </RouterLink>
                  <WhatsAppButton
                    :message="`Hello Funworld Events! I'd like to enquire about ${activeService.name}.`"
                    :source-ref="`svc_${activeService.slug}`"
                    variant="ghost"
                    label="WhatsApp us"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ═════════════ PAGE SHELL ═════════════ */
.sdp {
  background: #fbfaf7;
  position: relative;
  min-height: 60vh;
}
.container--editorial {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 clamp(1rem, 4vw, 4rem);
}

/* ═════════════ STATES ═════════════ */
.state-msg {
  padding: 6rem 5vw;
  text-align: center;
  font-family: var(--font-body, "Manrope", sans-serif);
  color: var(--color-text-muted, #5a4f56);
}
.state-msg--error {
  color: #b03a2e;
}

/* ═════════════ HERO ═════════════ */
.hero {
  padding: clamp(3rem, 6vw, 5rem) 0 clamp(2rem, 4vw, 3rem);
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: "";
  position: absolute;
  top: -15%;
  right: -10%;
  width: 55vw;
  height: 55vw;
  max-width: 720px;
  max-height: 720px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 40% 40%, rgba(196, 165, 130, 0.16), transparent 70%),
    radial-gradient(circle at 70% 60%, rgba(138, 154, 123, 0.12), transparent 70%);
  pointer-events: none;
  z-index: 0;
}
.hero > .container {
  position: relative;
  z-index: 1;
}

.hero__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(2rem, 5vw, 5rem);
  align-items: center;
}
.hero__copy {
  max-width: 560px;
}

.eyebrow {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-clay, #c4a582);
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.crumb {
  color: inherit;
  text-decoration: none;
  border-bottom: 1px solid currentColor;
  padding-bottom: 1px;
  opacity: 0.8;
}
.crumb:hover { opacity: 1; }
.crumb-sep { opacity: 0.4; }

.hero__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(2.4rem, 4.8vw, 4rem);
  font-weight: 300;
  line-height: 1.04;
  letter-spacing: -0.025em;
  color: var(--color-charcoal, #1a1417);
  margin: 0 0 1.25rem;
}
.lead {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: clamp(1.05rem, 1.2vw, 1.2rem);
  line-height: 1.65;
  color: var(--color-text-muted, #5a4f56);
  margin: 0 0 1rem;
  max-width: 52ch;
}
.hero__long {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.98rem;
  line-height: 1.7;
  color: var(--color-text-muted, #5a4f56);
  margin: 0;
  opacity: 0.85;
}
.hero__actions {
  margin-top: 2rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.hero__media {
  aspect-ratio: 4 / 5;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 30px 60px rgba(26, 20, 23, 0.18);
}
.hero__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.hero__media--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: repeating-linear-gradient(
    45deg,
    rgba(26, 20, 23, 0.04),
    rgba(26, 20, 23, 0.04) 12px,
    rgba(26, 20, 23, 0.08) 12px,
    rgba(26, 20, 23, 0.08) 24px
  );
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.5rem;
  color: var(--color-text-muted, #5a4f56);
  font-style: italic;
}

/* ═════════════ CATALOG ═════════════ */
.section-catalog {
  padding: clamp(3rem, 6vw, 5rem) 0 clamp(4rem, 8vw, 6rem);
  background: #ffffff;
  border-top: 1px solid rgba(26, 20, 23, 0.05);
  border-bottom: 1px solid rgba(26, 20, 23, 0.05);
}
.section-head {
  max-width: 640px;
  margin-bottom: clamp(2rem, 4vw, 3rem);
}
.section-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.9rem, 3.6vw, 2.8rem);
  font-weight: 300;
  line-height: 1.08;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--color-charcoal, #1a1417);
}
.empty-msg {
  font-family: var(--font-body);
  color: var(--color-text-muted, #5a4f56);
  text-align: center;
  padding: 3rem 0;
}

.svc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: clamp(1.25rem, 2.5vw, 2rem);
}

/* Service card (clickable button) */
.svc-card {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(26, 20, 23, 0.06);
  box-shadow:
    0 2px 6px rgba(26, 20, 23, 0.04),
    0 10px 24px rgba(26, 20, 23, 0.04);
  transition:
    transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 400ms ease,
    border-color 400ms ease;
  text-align: left;
  cursor: pointer;
  padding: 0;
  font: inherit;
  color: inherit;
}
.svc-card:hover,
.svc-card:focus-visible {
  transform: translateY(-6px);
  box-shadow:
    0 6px 12px rgba(26, 20, 23, 0.06),
    0 20px 40px rgba(26, 20, 23, 0.1);
  border-color: var(--color-clay, #c4a582);
  outline: none;
}
.svc-card:focus-visible {
  outline: 2px solid var(--color-plum, #2b0f2e);
  outline-offset: 3px;
}
.svc-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: #f4f1ec;
}
.svc-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 700ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.svc-card:hover .svc-card__media img {
  transform: scale(1.06);
}
.svc-card__placeholder {
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    45deg,
    rgba(26, 20, 23, 0.04),
    rgba(26, 20, 23, 0.04) 10px,
    rgba(26, 20, 23, 0.08) 10px,
    rgba(26, 20, 23, 0.08) 20px
  );
}
.svc-card__num {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: var(--color-plum, #2b0f2e);
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 0.35rem 0.65rem;
  border-radius: 4px;
  z-index: 2;
}
.svc-card__body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}
.svc-card__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.2rem, 1.6vw, 1.45rem);
  font-weight: 500;
  line-height: 1.2;
  margin: 0;
  color: var(--color-charcoal, #1a1417);
}
.svc-card__desc {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.92rem;
  line-height: 1.55;
  color: var(--color-text-muted, #5a4f56);
  margin: 0;
  flex: 1;
}
.svc-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(26, 20, 23, 0.06);
  gap: 0.75rem;
}
.svc-card__price {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-clay, #c4a582);
}
.svc-card__cta {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-plum, #2b0f2e);
  margin-left: auto;
  opacity: 0.6;
  transition: opacity 300ms ease;
}
.svc-card:hover .svc-card__cta { opacity: 1; }

/* ═════════════ MODAL ═════════════ */
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(26, 20, 23, 0.55);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(1rem, 3vw, 2rem);
  overflow-y: auto;
}
.modal {
  position: relative;
  width: 100%;
  max-width: 980px;
  background: #fbfaf7;
  border-radius: 16px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
  overflow: hidden;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  animation: modal-in 320ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
@keyframes modal-in {
  from { opacity: 0; transform: translateY(24px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.modal__close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 0;
  background: rgba(26, 20, 23, 0.7);
  color: #fcf9f4;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 200ms ease, transform 200ms ease;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.modal__close:hover {
  background: rgba(26, 20, 23, 0.9);
  transform: scale(1.05);
}
.modal__close:focus-visible {
  outline: 2px solid var(--color-gold, #d4af6a);
  outline-offset: 3px;
}

.modal__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}
.modal__media {
  position: relative;
  background: #f4f1ec;
  min-height: 280px;
}
.modal__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.modal__media-placeholder {
  width: 100%;
  height: 100%;
  min-height: 280px;
  background: repeating-linear-gradient(
    45deg,
    rgba(26, 20, 23, 0.04),
    rgba(26, 20, 23, 0.04) 12px,
    rgba(26, 20, 23, 0.08) 12px,
    rgba(26, 20, 23, 0.08) 24px
  );
}

.modal__content {
  padding: clamp(1.5rem, 3vw, 2.5rem);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.modal__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.6rem, 2.6vw, 2.2rem);
  font-weight: 400;
  line-height: 1.15;
  letter-spacing: -0.015em;
  color: var(--color-charcoal, #1a1417);
  margin: 0;
}
.modal__lead {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 1.02rem;
  line-height: 1.6;
  color: var(--color-text-muted, #5a4f56);
  margin: 0;
}
.modal__body {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--color-text-muted, #5a4f56);
  margin: 0.5rem 0;
}
.modal__body :deep(p) { margin: 0 0 0.75rem; }
.modal__body :deep(ul),
.modal__body :deep(ol) {
  margin: 0 0 0.75rem 1rem;
  padding: 0;
}
.modal__body :deep(li) { margin-bottom: 0.35rem; }
.modal__body :deep(strong) { color: var(--color-charcoal, #1a1417); }

.modal__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.25rem;
}
.modal__tag {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  background: rgba(196, 165, 130, 0.15);
  color: var(--color-plum, #2b0f2e);
}

.modal__price {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.15rem;
  font-weight: 500;
  color: var(--color-clay, #c4a582);
  margin: 0.5rem 0 0;
}

.modal__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(26, 20, 23, 0.08);
}

/* ═════════════ MODAL TRANSITIONS ═════════════ */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 250ms ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 320ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

/* ═════════════ BUTTONS ═════════════ */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.8rem 1.75rem;
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.92rem;
  font-weight: 600;
  border-radius: 2px;
  text-decoration: none;
  transition: all 200ms ease;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn--dark {
  background: var(--color-charcoal, #1a1417);
  color: var(--color-ivory, #fcf9f4);
}
.btn--dark:hover {
  background: var(--color-plum, #2b0f2e);
  transform: translateY(-2px);
}

/* ═════════════ RESPONSIVE ═════════════ */
@media (max-width: 900px) {
  .hero__grid {
    grid-template-columns: 1fr;
    gap: 2.5rem;
  }
  .hero__media {
    aspect-ratio: 16 / 10;
    max-height: 420px;
  }
  .modal__grid {
    grid-template-columns: 1fr;
  }
  .modal__media {
    min-height: 220px;
    max-height: 280px;
  }
}
@media (max-width: 600px) {
  .hero { padding: 2rem 0 1.5rem; }
  .svc-grid { grid-template-columns: 1fr; }
  .modal {
    max-height: 95vh;
    border-radius: 12px;
  }
  .modal__close {
    top: 0.5rem;
    right: 0.5rem;
  }
  .modal__content { padding: 1.25rem; }
}

/* ═════════════ REDUCED MOTION ═════════════ */
@media (prefers-reduced-motion: reduce) {
  .svc-card,
  .svc-card__media img,
  .modal,
  .modal-enter-active .modal,
  .modal-leave-active .modal {
    transition: none;
    animation: none;
  }
  .svc-card:hover { transform: none; }
  .svc-card:hover .svc-card__media img { transform: none; }
}
</style>