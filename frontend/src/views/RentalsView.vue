<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import WhatsAppButton from "../components/WhatsAppButton.vue";
import {
  listRentalCategories,
  listRentalItems,
  type RentalCategory,
} from "../api";

const categories = ref<RentalCategory[]>([]);
const categoryImages = ref<Record<string, string>>({});
const loading = ref(true);

onMounted(async () => {
  try {
    categories.value = await listRentalCategories();

    // Fetch items for each category and use the first available image.
    await Promise.all(
      categories.value.map(async (category) => {
        try {
          const { items } = await listRentalItems(category.slug);

          const image = items.find(
            (item) => item.featured_image_url
          )?.featured_image_url;

          if (image) {
            categoryImages.value[category.slug] = image;
          }
        } catch (error) {
          console.warn(
            `Could not load rental items for ${category.name}:`,
            error
          );
        }
      })
    );
  } catch (error) {
    console.error("Could not load rental categories:", error);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="rentals-page">
    <!-- ═══════════ HERO SECTION (BACKGROUND IMAGE) ═══════════ -->
    <section class="rentals-hero">
      <div class="rentals-hero__bg">
        <!-- You can replace this with a high-quality image of your inventory -->
        <img src="/images/inventory-hero.jpg" alt="Funworld Events inventory" />
        <div class="rentals-hero__overlay" />
      </div>

      <div class="container container--editorial rentals-hero__content">
        <div class="rentals-hero__copy">
          <p class="eyebrow eyebrow--gold">The Hire Collection</p>
          <h1 class="rentals-hero__title">
            Everything you need<br />
            for your <em>event.</em>
          </h1>
          <p class="lead rentals-hero__lead">
            Tents, seating, sound, lighting and décor — available for events
            across Kenya. Browse our collection, then message us on WhatsApp 
            to confirm availability for your date.
          </p>
          <div class="rentals-hero__cta">
            <a href="#collections" class="btn btn--gold">Shop the collection ↓</a>
            <WhatsAppButton
              message="Hello Funworld Events! I'd like to hire items for my event. Could you share your current availability and pricing?"
              source-ref="rentals_landing_hero"
              label="Enquire on WhatsApp"
              variant="ghost"
            />
          </div>
        </div>

        <!-- Floating "proof" image to anchor the hero -->
        <div class="rentals-hero__media" aria-hidden="true">
           <!-- Use a curated image of items here -->
          <img src="/images/rentals-featured.jpg" alt="Featured event items" loading="eager" />
        </div>
      </div>
    </section>

    <!-- ═══════════ STOREFRONT GRID ═══════════ -->
    <section id="collections" class="section section--catalog">
      <div class="container container--editorial">
        <header class="section-head">
          <p class="eyebrow">Browse the Collection</p>
          <h2 class="section-title">Pick a category to start.</h2>
        </header>

        <div v-if="loading" class="cat-grid">
          <div v-for="i in 4" :key="i" class="cat-card cat-card--skeleton" />
        </div>

        <div v-else-if="categories.length" class="cat-grid">
          <RouterLink
            v-for="c in categories"
            :key="c.slug"
            :to="`/rentals/${c.slug}`"
            class="cat-card"
          >
            <div class="cat-card__media">
              <img
                v-if="categoryImages[c.slug]"
                :src="categoryImages[c.slug]"
                :alt="c.name"
                loading="lazy"
              />

              <div v-else class="cat-card__pattern" />

              <span class="cat-card__count">
                {{ c.published_item_count }} Items
              </span>
            </div>
            <div class="cat-card__body">
              <h3 class="cat-card__title">{{ c.name }}</h3>
              <p v-if="c.short_description" class="cat-card__desc">
                {{ c.short_description }}
              </p>
              <div class="cat-card__action">
                <span>View items</span>
                <span class="cat-card__arrow">→</span>
              </div>
            </div>
          </RouterLink>
        </div>

        <div v-else class="empty-state">
          <p>Our hire catalogue is being updated.</p>
          <WhatsAppButton
            message="Hello Funworld Events! Could you send me your current items available for hire?"
            source-ref="rentals_empty"
            label="Ask us what's available"
            variant="solid"
          />
        </div>
      </div>
    </section>

    <!-- ═══════════ HOW IT WORKS ═══════════ -->
    <section class="section section--dark section--how-it-works">
      <div class="container container--editorial">
        <header class="section-head">
          <p class="eyebrow eyebrow--gold">How hiring works</p>
          <h2 class="section-title">Three steps, no surprises.</h2>
        </header>
        <div class="steps-grid">
          <div class="step">
            <span class="step-num">01</span>
            <h3>Browse</h3>
            <p>Pick what you need from the collection. Prices shown are indicative — final quote depends on quantity, dates and delivery.</p>
          </div>
          <div class="step">
            <span class="step-num">02</span>
            <h3>Message us</h3>
            <p>Tap "Hire" on any item or the WhatsApp button. Tell us your date, venue and quantity — we'll confirm availability within a few hours.</p>
          </div>
          <div class="step">
            <span class="step-num">03</span>
            <h3>We deliver</h3>
            <p>We handle transport, setup and collection. Fixed quote, no hidden line items.</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ═════════════ PAGE SHELL ═════════════ */
.rentals-page {
  background: #fbfaf7;
  position: relative;
}
.container--editorial {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 clamp(1rem, 4vw, 4rem);
}

/* ═════════════ HERO (BACKGROUND IMAGE) ═════════════ */
.rentals-hero {
  position: relative;
  min-height: 80vh;
  display: flex;
  align-items: center;
  padding: clamp(4rem, 10vw, 8rem) 0;
  overflow: hidden;
  background: var(--color-plum, #2b0f2e); /* Fallback */
}
.rentals-hero__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}
.rentals-hero__bg img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.rentals-hero__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(26, 20, 23, 0.85) 0%,
    rgba(26, 20, 23, 0.6) 50%,
    rgba(26, 20, 23, 0.3) 100%
  );
}
.rentals-hero__content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 4rem;
  align-items: center;
  width: 100%;
}

.rentals-hero__copy {
  max-width: 600px;
  color: var(--color-ivory, #fcf9f4);
}
.eyebrow {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--color-clay, #c4a582);
  margin: 0 0 1rem;
}
.eyebrow--gold { color: var(--color-gold, #d4af6a); }
.rentals-hero__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(2.8rem, 5vw, 4.5rem);
  font-weight: 300; line-height: 1.05; letter-spacing: -0.03em;
  margin: 0 0 1.5rem;
}
.rentals-hero__title em {
  font-style: italic; color: var(--color-gold, #d4af6a);
}
.rentals-hero__lead {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: clamp(1.05rem, 1.2vw, 1.25rem);
  line-height: 1.6; color: rgba(252, 249, 244, 0.85);
  max-width: 50ch; margin: 0 0 2.5rem;
}
.rentals-hero__cta {
  display: flex; gap: 1rem; flex-wrap: wrap;
}

/* Floating media to the right */
.rentals-hero__media {
  display: flex;
  justify-content: flex-end;
}
.rentals-hero__media img {
  width: 100%;
  max-width: 400px;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
  border: 4px solid rgba(255, 255, 255, 0.1);
  transform: rotate(3deg);
  transition: transform 0.4s ease;
}
.rentals-hero__media img:hover {
  transform: rotate(0deg) scale(1.02);
}

/* ═════════════ STOREFRONT GRID ═════════════ */
.section {
  padding: clamp(4rem, 8vw, 6rem) 0;
}
.section--catalog {
  background: #ffffff;
}
.section-head {
  max-width: 640px; margin-bottom: 3rem;
}
.section-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(2rem, 3.6vw, 3rem);
  font-weight: 300; line-height: 1.05; letter-spacing: -0.02em;
  margin: 0; color: var(--color-charcoal, #1a1417);
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: clamp(1.5rem, 3vw, 2.5rem);
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
  box-shadow: 0 2px 6px rgba(26, 20, 23, 0.04), 0 10px 24px rgba(26, 20, 23, 0.04);
  transition: transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 400ms ease;
}
.cat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 6px 12px rgba(26, 20, 23, 0.06), 0 20px 40px rgba(26, 20, 23, 0.1);
}
.cat-card--skeleton {
  height: 340px;
  background: #f4f1ec;
  border: none;
  box-shadow: none;
}

.cat-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  background: #f4f1ec;
  overflow: hidden;
}
/* We use a subtle pattern to stand in for category images */
.cat-card__pattern {
  width: 100%; height: 100%;
  background:
    repeating-linear-gradient(
      45deg,
      rgba(196, 165, 130, 0.05),
      rgba(196, 165, 130, 0.05) 10px,
      rgba(196, 165, 130, 0.1) 10px,
      rgba(196, 165, 130, 0.1) 20px
    );
  transition: transform 700ms ease;
}
.cat-card:hover .cat-card__pattern {
  transform: scale(1.05);
}
.cat-card__count {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: #ffffff;
  color: var(--color-plum, #2b0f2e);
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.cat-card__body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.cat-card__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.4rem;
  font-weight: 500;
  margin: 0 0 0.5rem;
  color: var(--color-charcoal, #1a1417);
}
.cat-card__desc {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.95rem;
  line-height: 1.55;
  color: var(--color-text-muted, #5a4f56);
  margin: 0 0 1.5rem;
  flex: 1;
}
.cat-card__action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid rgba(26, 20, 23, 0.06);
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-plum, #2b0f2e);
}
.cat-card__arrow {
  transition: transform 300ms ease;
}
.cat-card:hover .cat-card__arrow {
  transform: translateX(4px);
}

/* ═════════════ HOW IT WORKS ═════════════ */
.section--dark {
  background: var(--color-plum, #2b0f2e);
  color: var(--color-ivory, #fcf9f4);
  border-top: 1px solid rgba(252, 249, 244, 0.1);
}
.section--dark .section-title { color: var(--color-ivory, #fcf9f4); }
.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3rem;
}
.step {
  border-top: 1px solid rgba(212, 175, 106, 0.3);
  padding-top: 1.5rem;
}
.step-num {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.75rem; font-weight: 600;
  letter-spacing: 0.15em;
  color: var(--color-gold, #d4af6a);
  display: block; margin-bottom: 1rem;
}
.step h3 {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.4rem; font-weight: 500;
  margin: 0 0 0.75rem;
  color: var(--color-ivory, #fcf9f4);
}
.step p {
  color: rgba(252, 249, 244, 0.75);
  line-height: 1.6; font-size: 0.95rem;
  margin: 0;
}

/* ═════════════ EMPTY STATE ═════════════ */
.empty-state {
  text-align: center;
  padding: 4rem 1.5rem;
  border: 1px dashed var(--color-clay, #c4a582);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

/* ═════════════ BUTTONS ═════════════ */
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0.85rem 2rem;
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.95rem; font-weight: 600;
  border-radius: 2px; text-decoration: none;
  transition: all 200ms ease; cursor: pointer;
  border: 1px solid transparent;
}
.btn--gold { background: var(--color-gold, #d4af6a); color: var(--color-charcoal, #1a1417); }
.btn--gold:hover { background: #e6c385; transform: translateY(-2px); }

/* ═════════════ RESPONSIVE ═════════════ */
@media (max-width: 900px) {
  .rentals-hero__content {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
  .rentals-hero__media {
    justify-content: flex-start;
    order: -1; /* Image above text on mobile */
  }
  .rentals-hero__media img {
    max-width: 100%;
    aspect-ratio: 16 / 9;
    transform: rotate(0);
  }
  .steps-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}
@media (max-width: 600px) {
  .rentals-hero { min-height: auto; }
  .rentals-hero__title { font-size: clamp(2.2rem, 8vw, 3rem); }
  .cat-grid { grid-template-columns: 1fr; }
}

/* ═════════════ REDUCED MOTION ═════════════ */
@media (prefers-reduced-motion: reduce) {
  .rentals-hero__media img,
  .cat-card,
  .cat-card__pattern,
  .cat-card__arrow,
  .btn--gold:hover {
    transition: none;
    transform: none;
  }
  .cat-card:hover .cat-card__pattern { transform: none; }
}

@media (prefers-reduced-motion: reduce) {
  .rentals-hero__media img,
  .cat-card,
  .cat-card__pattern,
  .cat-card__media img,
  .cat-card__arrow,
  .btn--gold:hover {
    transition: none;
    transform: none;
  }
}
</style>