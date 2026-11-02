<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { http } from "../api";

interface PackageItem {
  id: string;
  slug: string;
  name: string;
  tagline: string | null;
  short_description: string | null;
  hero_image_url: string | null;
  price_amount: number | null;
  price_note: string | null;
  currency: string;
  is_featured: boolean;
}

const packages = ref<PackageItem[]>([]);
const loading = ref(true);
const error = ref("");

// Find the hero package for the split layout
const heroPackage = computed(() => {
  return packages.value.find((p) => p.is_featured) || packages.value[0] || null;
});

// The rest of the packages for the grid
const displayPackages = computed(() => {
  return heroPackage.value
    ? packages.value.filter((p) => p.id !== heroPackage.value?.id)
    : packages.value;
});

onMounted(async () => {
  try {
    const { data } = await http.get("/packages");
    // Handle both { data: [...] } and direct arrays
    packages.value = Array.isArray(data) ? data : data.data || [];
  } catch (err: any) {
    error.value = "Unable to load packages at this time.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="pkg-page">
    <!-- ═══════════ LOADING / ERROR ═══════════ -->
    <div v-if="loading" class="state-msg">
      <p>Loading packages…</p>
    </div>
    <div v-else-if="error" class="state-msg state-msg--error">
      <p>{{ error }}</p>
    </div>

    <!-- ═══════════ CONTENT ═══════════ -->
    <template v-else>
      <!-- HERO SPLIT -->
      <section class="hero">
        <div class="container container--editorial">
          <div class="hero__grid" :class="{ 'hero__grid--no-img': !heroPackage }">
            
            <!-- Left: Copy -->
            <div class="hero__copy">
              <p class="eyebrow">Hosted Events</p>
              <h1 class="hero__title">
                Ready-to-book,<br />
                <em>fully managed.</em>
              </h1>
              <p class="lead">
                Complete events we organise end to end. Book directly, or 
                request a customisation to make it uniquely yours.
              </p>
              <div class="hero__actions">
                <a href="#catalog" class="btn btn--dark">Browse all packages ↓</a>
              </div>
            </div>

            <!-- Right: Featured Hero Image -->
            <div v-if="heroPackage" class="hero__media">
              <RouterLink :to="`/packages/${heroPackage.slug}`" class="hero__card">
                <img
                  v-if="heroPackage.hero_image_url"
                  :src="heroPackage.hero_image_url"
                  :alt="heroPackage.name"
                  loading="eager"
                  fetchpriority="high"
                />
                <div v-else class="hero__placeholder" />
                
                <!-- Overlay details -->
                <div class="hero__card-overlay">
                  <span class="hero__card-badge">Featured Package</span>
                  <h2 class="hero__card-title">{{ heroPackage.name }}</h2>
                  <p v-if="heroPackage.price_amount" class="hero__card-price">
                    From {{ heroPackage.currency }} {{ heroPackage.price_amount.toLocaleString() }}
                  </p>
                </div>
              </RouterLink>
            </div>

          </div>
        </div>
      </section>

      <!-- CATALOG GRID -->
      <section id="catalog" class="section-catalog">
        <div class="container container--editorial">
          <header class="section-head">
            <p class="eyebrow">The Collection</p>
            <h2 class="section-title">Find the perfect fit.</h2>
          </header>

          <div v-if="!packages.length" class="empty-msg">
            No packages available right now. 
            <RouterLink to="/get-a-quote">Request a custom quote →</RouterLink>
          </div>

          <div v-else class="pkg-grid">
            <!-- If there's only 1 package and it's used in the hero, display it in the grid too so the page isn't empty -->
            <RouterLink
              v-for="p in (packages.length === 1 ? packages : displayPackages)"
              :key="p.id"
              :to="`/packages/${p.slug}`"
              class="pkg-card"
            >
              <div class="pkg-card__media">
                <img
                  v-if="p.hero_image_url"
                  :src="p.hero_image_url"
                  :alt="p.name"
                  loading="lazy"
                />
                <div v-else class="pkg-card__placeholder" />
                <span v-if="p.is_featured" class="pkg-card__badge">★ Featured</span>
              </div>

              <div class="pkg-card__body">
                <h3 class="pkg-card__title">{{ p.name }}</h3>
                <p v-if="p.tagline" class="pkg-card__tagline">{{ p.tagline }}</p>
                
                <div class="pkg-card__foot">
                  <div v-if="p.price_amount" class="pkg-card__price-wrap">
                    <span class="pkg-card__price">
                      {{ p.currency }} {{ p.price_amount.toLocaleString() }}
                    </span>
                    <span v-if="p.price_note" class="pkg-card__note">
                      {{ p.price_note }}
                    </span>
                  </div>
                  <div v-else class="pkg-card__price-wrap">
                    <span class="pkg-card__note">Contact for pricing</span>
                  </div>
                  
                  <span class="pkg-card__arrow">→</span>
                </div>
              </div>
            </RouterLink>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
/* ═════════════ PAGE SHELL ═════════════ */
.pkg-page {
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
.state-msg--error { color: #b03a2e; }

/* ═════════════ HERO SPLIT ═════════════ */
.hero {
  padding: clamp(3rem, 6vw, 5rem) 0 clamp(2rem, 4vw, 3rem);
  position: relative;
  overflow: hidden;
}
/* Soft pastel wash for vibrancy */
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
    radial-gradient(circle at 40% 40%, rgba(196, 165, 130, 0.15), transparent 70%),
    radial-gradient(circle at 70% 60%, rgba(138, 154, 123, 0.1), transparent 70%);
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
.hero__grid--no-img {
  grid-template-columns: 1fr;
  text-align: center;
  max-width: 800px;
  margin: 0 auto;
}

.hero__copy {
  max-width: 560px;
}
.eyebrow {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--color-clay, #c4a582);
  margin: 0 0 1rem;
}
.hero__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(2.4rem, 4.8vw, 4rem);
  font-weight: 300; line-height: 1.04; letter-spacing: -0.025em;
  color: var(--color-charcoal, #1a1417);
  margin: 0 0 1.25rem;
}
.hero__title em {
  font-style: italic; color: var(--color-plum, #2b0f2e);
}
.lead {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: clamp(1.05rem, 1.2vw, 1.2rem);
  line-height: 1.65; color: var(--color-text-muted, #5a4f56);
  margin: 0;
  max-width: 52ch;
}
.hero__actions {
  margin-top: 2rem;
}

/* Hero Media (The Featured Package) */
.hero__media {
  display: flex;
  justify-content: center;
}
.hero__card {
  display: block;
  position: relative;
  width: 100%;
  max-width: 500px;
  aspect-ratio: 4 / 5;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 30px 60px rgba(26, 20, 23, 0.2);
  text-decoration: none;
  transition: transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.hero__card:hover {
  transform: translateY(-6px);
}
.hero__card img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 700ms ease;
}
.hero__card:hover img {
  transform: scale(1.04);
}
.hero__placeholder {
  width: 100%; height: 100%;
  background: repeating-linear-gradient(
    45deg,
    rgba(26, 20, 23, 0.04),
    rgba(26, 20, 23, 0.04) 12px,
    rgba(26, 20, 23, 0.08) 12px,
    rgba(26, 20, 23, 0.08) 24px
  );
}
.hero__card-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 2.5rem 1.5rem 1.5rem;
  background: linear-gradient(to top, rgba(26,20,23,0.9) 0%, rgba(26,20,23,0) 100%);
  color: var(--color-ivory, #fcf9f4);
}
.hero__card-badge {
  display: inline-block;
  font-family: var(--font-body); font-size: 0.7rem; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase;
  background: var(--color-gold, #d4af6a); color: var(--color-charcoal, #1a1417);
  padding: 4px 8px; border-radius: 2px; margin-bottom: 0.75rem;
}
.hero__card-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.4rem, 2vw, 1.8rem); font-weight: 500;
  margin: 0 0 0.5rem; line-height: 1.2;
}
.hero__card-price {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 1.05rem; font-weight: 500; margin: 0;
  color: rgba(252, 249, 244, 0.9);
}

/* ═════════════ CATALOG GRID ═════════════ */
.section-catalog {
  padding: clamp(3rem, 6vw, 5rem) 0 clamp(4rem, 8vw, 6rem);
  background: #ffffff;
  border-top: 1px solid rgba(26, 20, 23, 0.05);
  border-bottom: 1px solid rgba(26, 20, 23, 0.05);
}
.section-head {
  max-width: 640px; margin-bottom: clamp(2rem, 4vw, 3rem);
}
.section-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.9rem, 3.6vw, 2.8rem);
  font-weight: 300; line-height: 1.08; letter-spacing: -0.02em;
  margin: 0; color: var(--color-charcoal, #1a1417);
}
.empty-msg {
  font-family: var(--font-body); font-size: 1rem;
  color: var(--color-text-muted, #5a4f56); text-align: center;
  padding: 3rem 0;
}
.empty-msg a {
  color: var(--color-plum, #2b0f2e); font-weight: 600; text-decoration: underline;
}

.pkg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: clamp(1.5rem, 3vw, 2.5rem);
}

/* Individual Card */
.pkg-card {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  border: 1px solid rgba(26, 20, 23, 0.06);
  box-shadow:
    0 2px 6px rgba(26, 20, 23, 0.04),
    0 10px 24px rgba(26, 20, 23, 0.04);
  transition:
    transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 400ms ease,
    border-color 400ms ease;
}
.pkg-card:hover {
  transform: translateY(-6px);
  box-shadow:
    0 6px 12px rgba(26, 20, 23, 0.06),
    0 20px 40px rgba(26, 20, 23, 0.1);
  border-color: var(--color-clay, #c4a582);
}

.pkg-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: #f4f1ec;
}
.pkg-card__media img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 700ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.pkg-card:hover .pkg-card__media img {
  transform: scale(1.06);
}
.pkg-card__placeholder {
  width: 100%; height: 100%;
  background: repeating-linear-gradient(
    45deg,
    rgba(26, 20, 23, 0.04),
    rgba(26, 20, 23, 0.04) 10px,
    rgba(26, 20, 23, 0.08) 10px,
    rgba(26, 20, 23, 0.08) 20px
  );
}
.pkg-card__badge {
  position: absolute;
  top: 1rem; left: 1rem;
  background: var(--color-gold, #d4af6a);
  color: var(--color-charcoal, #1a1417);
  font-family: var(--font-body); font-size: 0.75rem; font-weight: 700;
  padding: 0.35rem 0.6rem; border-radius: 4px;
  letter-spacing: 0.05em;
  z-index: 2;
}

.pkg-card__body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.pkg-card__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.3rem, 1.6vw, 1.5rem);
  font-weight: 500; margin: 0 0 0.5rem;
  color: var(--color-charcoal, #1a1417);
  line-height: 1.2;
}
.pkg-card__tagline {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.95rem; line-height: 1.55;
  color: var(--color-text-muted, #5a4f56);
  margin: 0 0 1.5rem;
  flex: 1;
}

/* Footer of card */
.pkg-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid rgba(26, 20, 23, 0.06);
}
.pkg-card__price-wrap {
  display: flex; flex-direction: column; gap: 0.2rem;
}
.pkg-card__price {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 1.05rem; font-weight: 600;
  color: var(--color-plum, #2b0f2e);
  font-variant-numeric: tabular-nums;
}
.pkg-card__note {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.8rem; color: var(--color-clay, #c4a582);
}
.pkg-card__arrow {
  font-size: 1.2rem; color: var(--color-charcoal, #1a1417);
  opacity: 0.3; transition: all 300ms ease;
}
.pkg-card:hover .pkg-card__arrow {
  opacity: 1; color: var(--color-clay, #c4a582); transform: translateX(4px);
}

/* ═════════════ BUTTON ═════════════ */
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0.8rem 1.75rem;
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.92rem; font-weight: 600;
  border-radius: 2px; text-decoration: none;
  transition: all 200ms ease; cursor: pointer;
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
    gap: 3rem;
  }
  .hero__media {
    order: -1; /* Image above text on mobile */
  }
  .hero__card {
    aspect-ratio: 16 / 10;
    max-height: 400px;
  }
  .hero__card-overlay {
    padding: 2rem 1.25rem 1.25rem;
  }
}

@media (max-width: 600px) {
  .hero { padding: 2rem 0 1.5rem; }
  .pkg-grid { grid-template-columns: 1fr; }
  .hero__card { aspect-ratio: 4 / 3; }
}

/* ═════════════ REDUCED MOTION ═════════════ */
@media (prefers-reduced-motion: reduce) {
  .hero__card,
  .hero__card img,
  .pkg-card,
  .pkg-card__media img,
  .pkg-card__arrow,
  .btn--dark:hover {
    transition: none;
    transform: none;
  }
  .pkg-card:hover .pkg-card__media img { transform: none; }
}
</style>