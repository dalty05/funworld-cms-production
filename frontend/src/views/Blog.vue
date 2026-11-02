<!-- Blog.vue -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { listBlogPosts, type BlogPostSummary } from "../api";

const route = useRoute();
const posts = ref<BlogPostSummary[]>([]);

onMounted(async () => {
  posts.value = await listBlogPosts({ category: route.params.cat as string | undefined });
});
</script>

<template>
  <div class="blog-page">
    <!-- ═══════════════════════════════════════════════════════════
         HERO SECTION
    ═══════════════════════════════════════════════════════════════ -->
    <section class="hero-section">
      <div class="container hero-grid">
        <!-- The white content box on the left -->
        <div class="hero-content">
          <p class="hero-meta">FEBRUARY 1, 2026 &nbsp;·&nbsp; FEATURED &nbsp;·&nbsp; 4 COMMENTS</p>
          <h1 class="hero-title">The joy of Funday: Where community meets celebration</h1>
          <p class="hero-excerpt">
            When the music fades and the last plate is cleared, what remains is the warmth of a community that came together. It's not just about the events we host—it's about the moments we create, the laughter we share, and the memories that linger long after the lights go down. Join us as we dive into the heart of our most vibrant celebrations.
          </p>
        </div>
        <!-- The image on the right (using public folder image) -->
        <div class="hero-image-wrap">
          <img src="/images/funday-hero.jpeg" alt="Community celebration at Funday" class="hero-image" />
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         LATEST STORIES SECTION
    ═══════════════════════════════════════════════════════════════ -->
    <section class="section stories-section">
      <div class="container">
        <header class="section-header">
          <p class="eyebrow">Browse and read the latest stuff</p>
          <h2 class="section-title">Latest Stories</h2>
        </header>

        <div class="stories-grid">
          <RouterLink v-for="p in posts" :key="p.slug" :to="`/blog/${p.slug}`" class="story-card">
            <!-- Media with overlapping image effect -->
            <div class="story-media-wrap">
              <div class="story-media">
                <img v-if="p.featured_image" :src="p.featured_image" :alt="p.title" loading="lazy" />
                <div v-else class="story-media-placeholder"></div>
              </div>
            </div>

            <div class="story-body">
              <h3 class="story-title">{{ p.title }}</h3>
              <p class="story-meta">{{ new Date(p.published_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) }} &nbsp;·&nbsp; {{ p.category || 'LIFESTYLE' }}</p>
              <p class="story-excerpt">{{ p.excerpt }}</p>
              <span class="read-more">READ MORE <span class="arrow">→</span></span>
            </div>
          </RouterLink>
        </div>

        <div class="load-more-wrap">
          <button class="btn btn--pill">More Posts</button>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         SERVICES & PRODUCTS HIGHLIGHT
    ═══════════════════════════════════════════════════════════════ -->
    <section class="section services-section">
      <div class="container">
        <header class="section-header">
          <p class="eyebrow">You have to read this!</p>
          <h2 class="section-title">Our Services & Products</h2>
        </header>

        <div class="services-grid">
          <!-- Service 1 -->
          <div class="service-card">
            <div class="service-content">
              <h3 class="service-title">Event Coordination</h3>
              <p class="service-desc">From intimate gatherings to grand celebrations, our team handles every detail so you can enjoy the moment.</p>
              <a href="/services" class="service-link">Explore Service <span class="arrow">→</span></a>
            </div>
            <div class="service-image">
              <img src="/images/service-event.jpeg" alt="Event Coordination" />
            </div>
          </div>

          <!-- Service 2 -->
          <div class="service-card">
            <div class="service-content">
              <h3 class="service-title">Catering & Menus</h3>
              <p class="service-desc">Curated menus featuring local flavors and seasonal ingredients, tailored to your event's vibe.</p>
              <a href="/services" class="service-link">Explore Service <span class="arrow">→</span></a>
            </div>
            <div class="service-image">
              <img src="/images/service-catering.jpeg" alt="Catering" />
            </div>
          </div>

          <!-- Service 3 -->
          <div class="service-card">
            <div class="service-content">
              <h3 class="service-title">Equipment Hire</h3>
              <p class="service-desc">Premium tents, seating, and audio-visual gear to elevate your community gathering.</p>
              <a href="/services" class="service-link">Explore Service <span class="arrow">→</span></a>
            </div>
            <div class="service-image">
              <img src="/images/service-equipment.jpeg" alt="Equipment Hire" />
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   GLOBAL TYPOGRAPHY & LAYOUT
═══════════════════════════════════════════════════════════════ */
.blog-page {
  background: #fff;
  padding-bottom: var(--sp-8, 3rem);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--sp-4, 1rem);
}

.eyebrow {
  font-size: var(--fs-xs, 0.72rem);
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #4a4a4a;
  margin-bottom: var(--sp-2, 0.5rem);
}

.section-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 var(--sp-6, 2rem);
  line-height: 1.1;
}

.section-header {
  margin-bottom: var(--sp-6, 2rem);
}

/* ═══════════════════════════════════════════════════════════════
   HERO SECTION
═══════════════════════════════════════════════════════════════ */
.hero-section {
  padding: var(--sp-8, 4rem) 0;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.2fr 2fr;
  gap: 0;
  align-items: center;
}

.hero-content {
  background: #fff;
  padding: var(--sp-6, 3rem);
  position: relative;
  z-index: 2;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
  margin-right: -10%;
  max-width: 600px;
}

.hero-meta {
  font-size: var(--fs-xs, 0.7rem);
  font-weight: 600;
  letter-spacing: 0.1em;
  color: #888;
  margin-bottom: var(--sp-3, 1rem);
}

.hero-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(1.8rem, 3vw, 2.4rem);
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 var(--sp-4, 1.5rem);
  color: #111;
}

.hero-excerpt {
  font-size: var(--fs-sm, 0.95rem);
  line-height: 1.6;
  color: #555;
  margin: 0;
}

.hero-image-wrap {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #f0f0f0;
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* ═══════════════════════════════════════════════════════════════
   LATEST STORIES GRID
═══════════════════════════════════════════════════════════════ */
.stories-section {
  padding: var(--sp-8, 4rem) 0;
}

.stories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--sp-6, 2rem) var(--sp-5, 1.5rem);
}

.story-card {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
  group: story;
}

.story-media-wrap {
  position: relative;
  margin-bottom: var(--sp-4, 1.5rem);
}

/* Creates the overlapping grey/white square effect from the screenshot */
.story-media-wrap::before {
  content: "";
  position: absolute;
  bottom: -10px;
  right: -10px;
  width: 50%;
  height: 50%;
  background: #f4f4f4;
  z-index: 0;
}

.story-media {
  position: relative;
  z-index: 1;
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: #eaeaea;
}

.story-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--dur-base, 400ms) ease;
}

.story-card:hover .story-media img {
  transform: scale(1.05);
}

.story-media-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
}

.story-body {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.story-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1.3;
  margin: 0 0 var(--sp-2, 0.5rem);
  color: #111;
}

.story-meta {
  font-size: var(--fs-xs, 0.65rem);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #888;
  margin-bottom: var(--sp-3, 1rem);
}

.story-excerpt {
  font-size: var(--fs-sm, 0.9rem);
  line-height: 1.6;
  color: #555;
  margin: 0 0 var(--sp-4, 1.2rem);
  flex-grow: 1;
}

.read-more {
  font-size: var(--fs-xs, 0.7rem);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #ff4d6d; /* Matches the pink/red accent */
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: gap var(--dur-base, 300ms) ease;
}

.story-card:hover .read-more {
  gap: 0.7rem;
}

.load-more-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--sp-6, 3rem);
}

/* ═══════════════════════════════════════════════════════════════
   SERVICES & PRODUCTS HIGHLIGHT
═══════════════════════════════════════════════════════════════ */
.services-section {
  padding: var(--sp-8, 4rem) 0;
  background: #fafafa;
  border-top: 1px solid #eee;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--sp-5, 2rem);
}

.service-card {
  display: flex;
  background: #fff;
  border: 1px solid #eaeaea;
  border-radius: 0;
  overflow: hidden;
  transition: box-shadow var(--dur-base, 300ms) ease;
}

.service-card:hover {
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
}

.service-content {
  padding: var(--sp-5, 1.5rem);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.service-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 var(--sp-2, 0.5rem);
  color: #111;
}

.service-desc {
  font-size: var(--fs-sm, 0.85rem);
  line-height: 1.5;
  color: #666;
  margin: 0 0 var(--sp-4, 1rem);
  flex-grow: 1;
}

.service-link {
  font-size: var(--fs-xs, 0.7rem);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #111;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.service-link:hover {
  color: #ff4d6d;
}

.service-image {
  width: 120px; /* Narrow strip image on the right */
  flex-shrink: 0;
  background: #eaeaea;
}

.service-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════════ */
.btn--pill {
  background: #ff4d6d;
  color: #fff;
  border: none;
  padding: 0.8rem 2rem;
  border-radius: 999px;
  font-size: var(--fs-sm, 0.85rem);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: background var(--dur-base, 200ms) ease;
}

.btn--pill:hover {
  background: #e03e5c;
}

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════════ */
@media (max-width: 900px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
  
  .hero-content {
    margin-right: 0;
    margin-bottom: -2rem;
    max-width: 100%;
  }
  
  .hero-image-wrap {
    aspect-ratio: 16 / 9;
  }
}

@media (max-width: 640px) {
  .stories-grid {
    grid-template-columns: 1fr;
  }
  
  .service-card {
    flex-direction: column-reverse;
  }
  
  .service-image {
    width: 100%;
    height: 160px;
  }
}
</style>