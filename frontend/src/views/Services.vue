
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { http } from "../api";

interface Service {
  name: string;
  slug: string;
  featured_image_url?: string | null;
}

interface ServiceCategory {
  slug: string;
  name: string;
  accent_color?: string | null;
  hero_image_url?: string | null;
  short_description?: string | null;
  service_count?: number;
  services?: Service[];
}

const categories = ref<ServiceCategory[]>([]);
const categoryImages = ref<Record<string, string>>({});
const loading = ref(true);
const error = ref("");

// Category-specific fallback images.
// Make sure these files exist in frontend/public/images/services/
const fallbackImages: Record<string, string> = {
  weddings: "/images/services/weddings.jpg",
  kids: "/images/services/kids.jpg",
  corporate: "/images/services/corporate.jpg",
  fundays: "/images/services/fundays.jpg",
};

function fallbackFor(slug: string): string {
  return fallbackImages[slug] || "/images/services/weddings.jpg";
}

// Resolve the best available image for each category.
function categoryImage(category: ServiceCategory): string {
  return (
    categoryImages.value[category.slug] ||
    category.hero_image_url ||
    fallbackFor(category.slug)
  );
}

// If an image fails to load, use the category fallback.
function handleImageError(
  event: Event,
  category: ServiceCategory
) {
  const img = event.target as HTMLImageElement;
  const fallback = fallbackFor(category.slug);

  if (img.src !== new URL(fallback, window.location.origin).href) {
    img.src = fallback;
  } else {
    img.style.visibility = "hidden";
  }
}

// Hero deck — use the same resolved images as the category cards.
const deckImages = computed(() =>
  categories.value.slice(0, 4).map((category) => ({
    url: categoryImage(category),
    name: category.name,
  }))
);

const fallbackDeck = [
  { url: "/images/services/weddings.jpg", name: "Weddings" },
  { url: "/images/services/corporate.jpg", name: "Corporate" },
  { url: "/images/services/kids.jpg", name: "Kids" },
  { url: "/images/services/fundays.jpg", name: "Fundays" },
];

const displayDeck = computed(() =>
  deckImages.value.length >= 2 ? deckImages.value : fallbackDeck
);

// Palette fallback for cards without accent_color.
const accentPalette = ["#c4a582", "#8a9a7b", "#b8727a", "#7b8b9a"];

function accentFor(category: ServiceCategory, index: number) {
  return category.accent_color || accentPalette[index % accentPalette.length];
}

async function loadCategories() {
  try {
    // First fetch the category list.
    const response = await http.get("/services/categories");

    const payload = response.data;
    const result = Array.isArray(payload) ? payload : payload?.data;

    if (!Array.isArray(result)) {
      throw new Error("Unexpected categories API response format.");
    }

    categories.value = result;

    // Fetch category details to obtain their service images.
    const details = await Promise.allSettled(
      result.map(async (category: ServiceCategory) => {
        const detailResponse = await http.get(
          `/services/categories/${category.slug}`
        );

        const detail = detailResponse.data?.data;

        if (!detail) {
          return {
            slug: category.slug,
            image: category.hero_image_url || null,
          };
        }

        // Category hero image takes priority.
        const image =
          detail.hero_image_url ||
          detail.services?.find(
            (service: Service) => service.featured_image_url
          )?.featured_image_url ||
          null;

        return {
          slug: category.slug,
          image,
        };
      })
    );

    // Save successful image resolutions.
    const resolved: Record<string, string> = {};

    details.forEach((result) => {
      if (result.status === "fulfilled" && result.value.image) {
        resolved[result.value.slug] = result.value.image;
      }
    });

    categoryImages.value = resolved;

  } catch (err: any) {
    console.error("[Services] Failed to load categories:", err);

    error.value =
      err.response?.data?.message ||
      err.message ||
      "Unable to load services. Please try again.";
  } finally {
    loading.value = false;
  }
}

onMounted(loadCategories);
</script>

<template>
  <div class="services-page">
    <!-- ═══════ HERO — COMPACT SPLIT ═══════ -->
    <section class="hero-split">
      <div class="container container--editorial">
        <div class="hero-split__grid">
          <!-- Left: text -->
          <div class="hero-split__copy">
            <p class="eyebrow">Our Services</p>
            <h1 class="hero-title">
              Everything you need,<br />
              <em>under one roof.</em>
            </h1>
            <p class="lead">
              Explore what we do, category by category. Each service is
              tailored to your vision — from intimate gatherings to
              large-scale productions.
            </p>
            <div class="hero-actions">
              <a href="#catalog" class="btn btn--dark">Browse services ↓</a>
            </div>
          </div>

          <!-- Right: enlarged fan-out deck -->
          <div class="hero-split__visual" aria-hidden="true">
            <div class="deck" :style="{ '--total': displayDeck.length }">
              <div
                v-for="(item, i) in displayDeck"
                :key="i"
                class="deck__card"
                :style="{ '--i': i }"
              >
                <img :src="item.url" :alt="item.name" loading="lazy" />
                <span class="deck__label">{{ item.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════ CATALOG ═══════ -->
    <section id="catalog" class="section-catalog">
      <div class="container container--editorial">
        <header class="section-head">
          <p class="eyebrow">The Catalogue</p>
          <h2 class="section-title">Pick a category to start.</h2>
        </header>

        <p v-if="loading" class="status-msg">Loading services…</p>
        <p v-else-if="error" class="status-msg status-msg--error">{{ error }}</p>
        <p v-else-if="categories.length === 0" class="status-msg">
          No service categories are available yet.
        </p>

        <div v-else class="cat-grid">
          <RouterLink
            v-for="(c, i) in categories"
            :key="c.slug"
            :to="`/services/${c.slug}`"
            class="cat-card"
            :style="{ '--accent': accentFor(c, i) }"
          >
            
          <div class="cat-card__media">
            <img
              :src="categoryImage(c)"
              :alt="c.name"
              loading="lazy"
              @error="handleImageError($event, c)"
            />

            <span class="cat-card__num">
              {{ String(i + 1).padStart(2, "0") }}
            </span>
          </div>


            <div class="cat-card__body">
              <h3 class="cat-card__title">{{ c.name }}</h3>
              <p class="cat-card__desc">{{ c.short_description }}</p>
              <div class="cat-card__foot">
                <span class="cat-card__count">
                  {{ c.service_count ?? 0 }}
                  {{ (c.service_count ?? 0) === 1 ? "service" : "services" }}
                </span>
                <span class="cat-card__arrow">→</span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ═════════════ PAGE SHELL — no fixed backgrounds ═════════════ */
.services-page {
  background: #fbfaf7; /* warm off-white, gentler than pure white */
  position: relative;
  /* No overflow:hidden — footer must remain visible */
}

.container--editorial {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 clamp(1rem, 4vw, 4rem);
}

/* ═════════════ HERO — COMPACT ═════════════ */
.hero-split {
  /* Tight vertical rhythm — no dead space */
  padding: clamp(3rem, 6vw, 5rem) 0 clamp(2rem, 4vw, 3rem);
  position: relative;
  overflow: hidden;
}
/* Soft pastel wash behind the whole hero for vibrancy */
.hero-split::before {
  content: "";
  position: absolute;
  top: -20%;
  right: -10%;
  width: 60vw;
  height: 60vw;
  max-width: 800px;
  max-height: 800px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 40% 40%, rgba(196, 165, 130, 0.18), transparent 70%),
    radial-gradient(circle at 70% 60%, rgba(138, 154, 123, 0.14), transparent 70%);
  pointer-events: none;
  z-index: 0;
}
.hero-split .container {
  position: relative;
  z-index: 1;
}

.hero-split__grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: clamp(2rem, 5vw, 5rem);
  align-items: center;
}

.eyebrow {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-clay, #c4a582);
  margin: 0 0 0.75rem;
}
.hero-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(2.4rem, 4.8vw, 4rem);
  font-weight: 300;
  line-height: 1.04;
  letter-spacing: -0.025em;
  color: var(--color-charcoal, #1a1417);
  margin: 0 0 1.1rem;
}
.hero-title em {
  font-style: italic;
  color: var(--color-plum, #2b0f2e);
}
.lead {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: clamp(1rem, 1.1vw, 1.1rem);
  line-height: 1.65;
  color: var(--color-text-muted, #5a4f56);
  max-width: 48ch;
  margin: 0;
}
.hero-actions {
  margin-top: 1.75rem;
}

/* ═════════════ THE DECK — BIGGER, MORE PRESENT ═════════════ */
.hero-split__visual {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 420px;
  position: relative;
}
.deck {
  position: relative;
  width: clamp(280px, 30vw, 360px);
  height: clamp(360px, 38vw, 460px);
  perspective: 1200px;
}
.deck__card {
  position: absolute;
  inset: 0;
  background: #ffffff;
  padding: 12px 12px 44px;
  border-radius: 6px;
  box-shadow:
    0 30px 60px rgba(26, 20, 23, 0.18),
    0 8px 20px rgba(26, 20, 23, 0.08);
  border: 1px solid rgba(26, 20, 23, 0.05);
  transition: transform 500ms cubic-bezier(0.2, 0.8, 0.2, 1);
  cursor: pointer;
  transform-origin: center center;

  /* The pile math: centered spread */
  transform:
    rotate(calc((var(--i) - (var(--total) - 1) / 2) * 7deg))
    translateY(calc(var(--i) * 8px))
    translateX(calc((var(--i) - (var(--total) - 1) / 2) * 6px));

  z-index: calc(var(--total) - var(--i));
}
.deck__card img {
  width: 100%;
  height: calc(100% - 32px);
  object-fit: cover;
  border-radius: 3px;
  display: block;
}
.deck__label {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 0.9rem;
  font-style: italic;
  color: var(--color-charcoal, #1a1417);
  text-align: center;
}
/* Hover: dramatic fan-out */
.deck:hover .deck__card {
  transform:
    rotate(calc((var(--i) - (var(--total) - 1) / 2) * 14deg))
    translateY(calc(var(--i) * 12px - 20px))
    translateX(calc((var(--i) - (var(--total) - 1) / 2) * 90px));
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

.status-msg {
  font-family: var(--font-body);
  font-size: 1rem;
  color: var(--color-text-muted, #5a4f56);
  padding: 3rem;
  text-align: center;
}
.status-msg--error {
  color: #c0392b;
}

/* ═════════════ CARDS ═════════════ */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: clamp(1.25rem, 2.5vw, 2rem);
}

.cat-card {
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
  position: relative;
}
.cat-card:hover {
  transform: translateY(-6px);
  box-shadow:
    0 6px 12px rgba(26, 20, 23, 0.06),
    0 20px 40px rgba(26, 20, 23, 0.1);
  border-color: var(--accent);
}

/* Image area — with the accent ribbon bar on top */
.cat-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: #f4f1ec;
}
.cat-card__media::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 5px;
  background: var(--accent);
  z-index: 2;
  transition: height 300ms ease;
}
.cat-card:hover .cat-card__media::before {
  height: 7px;
}
.cat-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 700ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.cat-card:hover .cat-card__media img {
  transform: scale(1.06);
}
.cat-card__placeholder {
  width: 100%;
  height: 100%;
  background:
    repeating-linear-gradient(
      45deg,
      rgba(26, 20, 23, 0.03),
      rgba(26, 20, 23, 0.03) 10px,
      rgba(26, 20, 23, 0.06) 10px,
      rgba(26, 20, 23, 0.06) 20px
    );
}

/* Big number badge — top-right */
.cat-card__num {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: var(--accent);
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 0.35rem 0.65rem;
  border-radius: 4px;
  z-index: 2;
}

.cat-card__body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}
.cat-card__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.2rem, 1.6vw, 1.45rem);
  font-weight: 500;
  line-height: 1.2;
  margin: 0;
  color: var(--color-charcoal, #1a1417);
}
.cat-card__desc {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.92rem;
  line-height: 1.55;
  color: var(--color-text-muted, #5a4f56);
  margin: 0;
  flex: 1;
}
.cat-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(26, 20, 23, 0.06);
}
.cat-card__count {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--accent);
}
.cat-card__arrow {
  font-size: 1.1rem;
  color: var(--color-charcoal, #1a1417);
  opacity: 0.3;
  transition: all 300ms ease;
}
.cat-card:hover .cat-card__arrow {
  opacity: 1;
  color: var(--accent);
  transform: translateX(4px);
}

/* ═════════════ BUTTON ═════════════ */
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
  .hero-split__grid {
    grid-template-columns: 1fr;
    gap: 2.5rem;
  }
  .hero-split__visual {
    min-height: 380px;
    order: -1; /* deck appears above text on mobile */
  }
  .cat-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}
@media (max-width: 600px) {
  .hero-split {
    padding: 2rem 0 1.5rem;
  }
  .hero-split__visual {
    min-height: 320px;
  }
  .deck {
    width: 260px;
    height: 340px;
  }
  .cat-grid {
    grid-template-columns: 1fr;
  }
  .cat-card__body {
    padding: 1.25rem;
  }
}

/* ═════════════ REDUCED MOTION ═════════════ */
@media (prefers-reduced-motion: reduce) {
  .deck__card,
  .deck:hover .deck__card,
  .cat-card,
  .cat-card__media img,
  .cat-card__arrow,
  .btn--dark:hover {
    transition: none;
    transform: none;
  }
  .cat-card:hover .cat-card__media::before {
    height: 5px;
  }
}
</style>