<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import WhatsAppButton from "../components/WhatsAppButton.vue";
import {
  listPackages,
  listServiceCategories,
  listFeaturedGallery,
  listRentals,
  type PackageSummary,
  type ServiceCategorySummary,
  type GalleryImage,
  type RentalItem,
} from "../api";

// ─── Types ──────────────────────────────────────────────────────
type HeroSlide = {
  id: string;
  imageUrl: string;
  eyebrow: string;
  title: string;
  description: string;
  ctaText: string;
  ctaLink?: string;
};

type BrowseCard = {
  label: string;
  description: string;
  to: string;
  image?: string;
  meta?: string;
};

type EventType = { label: string; slug: string };

// ─── Router ─────────────────────────────────────────────────────
const router = useRouter();

// ─── State ──────────────────────────────────────────────────────
const packages = ref<PackageSummary[]>([]);
const services = ref<ServiceCategorySummary[]>([]);
const gallery = ref<GalleryImage[]>([]);
const rentalItems = ref<RentalItem[]>([]);

const loading = ref({ hero: true, belowFold: true });
const activeSlide = ref(0);
const reduceMotion = ref(false);
let heroTimer: ReturnType<typeof setInterval> | null = null;

const heroWrapperRef = ref<HTMLElement | null>(null);
const scrollProgress = ref(0);
let ticking = false;

// Search / discovery
const searchQuery = ref("");
const selectedEventType = ref("");

// ─── Fallbacks ──────────────────────────────────────────────────
const fallbackServices: ServiceCategorySummary[] = [
  { slug: "weddings", name: "Weddings & Receptions", short_description: "Full-service planning, décor, coordination, and vendor management.", hero_image_url: "/images/services/weddings.jpg", accent_color: null, service_count: 0 },
  { slug: "birthdays", name: "Birthdays", short_description: "Themed celebrations with décor, entertainment, and everything planned.", hero_image_url: "/images/services/birthdays.jpg", accent_color: null, service_count: 0 },
  { slug: "corporate", name: "Corporate Events", short_description: "Conferences, launches, team retreats, and end-of-year parties.", hero_image_url: "/images/services/corporate.jpg", accent_color: null, service_count: 0 },
  { slug: "school-fundays", name: "School Fun Days", short_description: "Sports days, family fun days, and school carnivals.", hero_image_url: "/images/services/fundays.jpg", accent_color: null, service_count: 0 },
  { slug: "graduations", name: "Graduations", short_description: "Milestone celebrations with photo-ready styling.", hero_image_url: "/images/services/graduations.jpg", accent_color: null, service_count: 0 },
  { slug: "family-events", name: "Family Events", short_description: "Reunions, baby showers, and intimate gatherings.", hero_image_url: "/images/services/family.jpg", accent_color: null, service_count: 0 },
];
const fallbackHeroImage = "/images/hero-home.jpeg";
const fallbackTile = "/images/hero-home.jpeg";

const displayServices = computed(() =>
  services.value.length ? services.value : fallbackServices
);

// Event types for search dropdown
const eventTypes = computed<EventType[]>(() =>
  displayServices.value.slice(0, 8).map((s) => ({ label: s.name, slug: s.slug }))
);

// ─── Hero slides ────────────────────────────────────────────────
const heroSlides = computed<HeroSlide[]>(() => {
  const slides: HeroSlide[] = [];
  const brandImage = gallery.value[0]?.url || fallbackHeroImage;

  slides.push({
    id: "brand",
    imageUrl: brandImage,
    eyebrow: "Kenya's Premium Event Partner",
    title: "Every occasion deserves something extraordinary.",
    description: "From intimate weddings to corporate showcases and school fundays — one team, one standard, every time.",
    ctaText: "Get a free quote",
    ctaLink: "/get-a-quote",
  });

  const featuredPkg =
  packages.value.find((p) => p.hero_image_url) || packages.value[0];

if (featuredPkg?.hero_image_url) {
    slides.push({
      id: `pkg-${featuredPkg.id}`,
      imageUrl: featuredPkg.hero_image_url,
      eyebrow: "Featured Package",
      title: featuredPkg.name,
      description: featuredPkg.tagline || "A complete event, tailored to your guests and your budget.",
      ctaText: "View package",
      ctaLink: `/packages/${featuredPkg.slug}`,
    });
  }
  return slides;
});

// ─── Discovery / search ─────────────────────────────────────────
function onSearch() {
  const q = searchQuery.value.trim();
  const type = selectedEventType.value;

  if (type) {
    router.push(`/services/${type}`);
    return;
  }
  if (q) {
    router.push({ path: "/services", query: { q } });
    return;
  }
  router.push("/services");
}

// ─── Below-fold rails ───────────────────────────────────────────
const occasionRail = computed<BrowseCard[]>(() => {
  const src = displayServices.value.slice(0, 6);
  return src.map((s) => ({
    label: s.name,
    description: s.short_description || "Discover our services for this occasion.",
    to: `/services/${s.slug}`,
    image: s.hero_image_url || undefined,
    meta: s.service_count ? `${s.service_count} services` : undefined,
  }));
});

const packageRail = computed<BrowseCard[]>(() =>
  packages.value.slice(0, 4).map((p) => ({
    label: p.name,
    description: p.tagline || "A complete event, tailored to you.",
    to: `/packages/${p.slug}`,
    image: p.hero_image_url || undefined,
    meta: p.price_amount != null
      ? `${p.price_note ? `${p.price_note} ` : "From "}${p.currency} ${p.price_amount.toLocaleString()}`
      : undefined,
  }))
);

// Rental categories derived from rentals
const rentalCategories = computed<BrowseCard[]>(() => {
  const map = new Map<string, { name: string; slug: string; img?: string; count: number }>();
  for (const r of rentalItems.value) {
    const slug = r.category?.slug ?? "general";
    const name = r.category?.name ?? "General Hire";
    const entry = map.get(slug) ?? { name, slug, img: undefined, count: 0 };
    entry.count += 1;
    if (!entry.img && r.featured_image_url) entry.img = r.featured_image_url;
    map.set(slug, entry);
  }
  return Array.from(map.values())
    .slice(0, 8)
    .map((c) => ({
      label: c.name,
      description: `${c.count} item${c.count === 1 ? "" : "s"} available`,
      to: `/rentals/${c.slug}`,
      image: c.img,
    }));
});

const hireItemsRail = computed<BrowseCard[]>(() =>
  rentalItems.value
    .filter((r) => r.featured_image_url)
    .slice(0, 8)
    .map((r) => ({
      label: r.name,
      description: r.category?.name ?? "Hire item",
      to: r.category?.slug
        ? `/rentals/${r.category.slug}`
        : "/rentals",
      image: r.featured_image_url || undefined,
      meta: r.from_price != null
        ? `${r.currency} ${r.from_price.toLocaleString()}${r.unit ? ` ${r.unit}` : ""}`
        : undefined,
    }))
);

const galleryRail = computed<BrowseCard[]>(() =>
  gallery.value.slice(0, 7).map((g) => ({
    label: g.caption || "From our portfolio",
    // description: g.category || "Gallery",
    description: "From our portfolio",
    to: "/gallery",
    image: g.url,
  }))
);

// ─── Hero image mounting / timer ────────────────────────────────
const shouldMountImage = (index: number) => {
  const total = heroSlides.value.length;
  if (total <= 1) return true;
  const next = (activeSlide.value + 1) % total;
  return index === activeSlide.value || index === next;
};

function startTimer() {
  stopTimer();
  if (reduceMotion.value || heroSlides.value.length < 2) return;
  heroTimer = setInterval(() => {
    activeSlide.value = (activeSlide.value + 1) % heroSlides.value.length;
  }, 6500);
}
function stopTimer() {
  if (heroTimer) clearInterval(heroTimer);
  heroTimer = null;
}
function goToSlide(i: number) {
  activeSlide.value = i;
  startTimer();
}

// ─── Scroll progress ────────────────────────────────────────────
function updateScrollProgress() {
  if (!heroWrapperRef.value) return;
  const rect = heroWrapperRef.value.getBoundingClientRect();
  const scrollRange = rect.height - window.innerHeight;
  if (scrollRange <= 0) {
    scrollProgress.value = 0;
    return;
  }
  const progress = Math.max(0, Math.min(1, -rect.top / scrollRange));
  scrollProgress.value = progress;
  ticking = false;
}
function onScroll() {
  if (!ticking) {
    window.requestAnimationFrame(updateScrollProgress);
    ticking = true;
  }
}

// ─── Lifecycle ──────────────────────────────────────────────────
onMounted(async () => {
  if (typeof window !== "undefined") {
    reduceMotion.value = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.addEventListener("scroll", onScroll, { passive: true });
    setTimeout(updateScrollProgress, 100);
  }

  const [galRes, pkgRes] = await Promise.allSettled([
    listFeaturedGallery(8),
    listPackages(),
  ]);

  if (galRes.status === "fulfilled") gallery.value = galRes.value;
  if (pkgRes.status === "fulfilled") packages.value = pkgRes.value;

  loading.value.hero = false;
  startTimer();








  
  setTimeout(async () => {
    const [svcRes, rentRes] = await Promise.allSettled([
      listServiceCategories(),
      listRentals ? listRentals() : Promise.resolve([]),
    ]);
    if (svcRes.status === "fulfilled") services.value = svcRes.value;
    if (rentRes.status === "fulfilled") rentalItems.value = rentRes.value;
    loading.value.belowFold = false;
  }, 500);

  console.log("First package API object:", packages.value[0]);
console.log(
  "Package API keys:",
  Object.keys(packages.value[0] ?? {})
);
});

onBeforeUnmount(() => {
  stopTimer();
  if (typeof window !== "undefined") {
    window.removeEventListener("scroll", onScroll);
  }
});
</script>

<template>
  <!-- ═══════════════════════════════════════════════════════════
       01 · CINEMATIC HERO — Discover Funworld
  ═══════════════════════════════════════════════════════════════ -->
  <div
    class="hero-wrapper"
    ref="heroWrapperRef"
    :style="{ '--scroll-progress': scrollProgress }"
  >
    <section class="hero-sticky">
      <div class="hero__media">
        <template v-for="(slide, i) in heroSlides" :key="slide.id">
          <img
            v-if="shouldMountImage(i)"
            :src="slide.imageUrl"
            :alt="slide.title"
            class="hero__img"
            :class="{ 'hero__img--active': i === activeSlide }"
            :loading="i === 0 ? 'eager' : 'lazy'"
            :fetchpriority="i === 0 ? 'high' : 'auto'"
          />
        </template>
        <div class="hero__overlay" />
      </div>

      <div class="container hero__content">
        <Transition name="slide-fade" mode="out-in">
          <div :key="heroSlides[activeSlide]?.id ?? 'empty'" class="hero__panel">
            <p class="eyebrow eyebrow--gold">{{ heroSlides[activeSlide]?.eyebrow }}</p>
            <h1 class="hero__title">{{ heroSlides[activeSlide]?.title }}</h1>
            <p class="hero__lead">{{ heroSlides[activeSlide]?.description }}</p>
          </div>
        </Transition>

        <!-- Search / discovery bar -->
        <form class="hero-search" @submit.prevent="onSearch">
          <div class="hero-search__field hero-search__field--grow">
            <label class="hero-search__label" for="hero-q">What are you planning?</label>
            <input
              id="hero-q"
              v-model="searchQuery"
              type="text"
              class="hero-search__input"
              placeholder="e.g. outdoor wedding, kids birthday…"
            />
          </div>
          <div class="hero-search__field">
            <label class="hero-search__label" for="hero-type">Select event type</label>
            <select id="hero-type" v-model="selectedEventType" class="hero-search__input">
              <option value="">All types</option>
              <option v-for="t in eventTypes" :key="t.slug" :value="t.slug">{{ t.label }}</option>
            </select>
          </div>
          <button type="submit" class="hero-search__submit">
            Search
          </button>
        </form>

        <div class="hero__actions">
          <RouterLink :to="heroSlides[activeSlide]?.ctaLink || '/get-a-quote'" class="btn btn--gold">
            {{ heroSlides[activeSlide]?.ctaText || 'Get a free quote' }}
          </RouterLink>
          <RouterLink to="/rentals" class="btn btn--ghost-light">
            Build a hire list
          </RouterLink>
        </div>

        <div v-if="heroSlides.length > 1" class="hero__dots" role="tablist">
          <button
            v-for="(s, i) in heroSlides"
            :key="s.id"
            class="hero__dot"
            :class="{ 'hero__dot--active': i === activeSlide }"
            :aria-label="`Show slide ${i + 1}: ${s.title}`"
            :aria-selected="i === activeSlide"
            role="tab"
            @click="goToSlide(i)"
          />
        </div>
      </div>
    </section>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       PAGE BODY
  ═══════════════════════════════════════════════════════════════ -->
  <div class="page-body-wrapper">
    <main class="page-body">
      <div class="scroll-progress" aria-hidden="true">
        <span class="scroll-progress__fill" :style="{ transform: `scaleY(${scrollProgress})` }" />
      </div>

      <!-- ═══════ 02 · EXPLORE BY OCCASION ═══════ -->
      <section class="section section--rail">
        <div class="container container--editorial">
          <header class="rail-head">
            <div>
              <p class="eyebrow">Explore by occasion</p>
              <h2 class="section-title">What are you <em>planning?</em></h2>
            </div>
            <RouterLink to="/services" class="rail-more">View all services →</RouterLink>
          </header>

          <div class="rail">
            <RouterLink
              v-for="card in occasionRail"
              :key="card.to"
              :to="card.to"
              class="rail-card rail-card--tall"
            >
              <div class="rail-card__media">
                <img v-if="card.image" :src="card.image" :alt="card.label" loading="lazy" />
                <div v-else class="rail-card__placeholder" />
              </div>
              <div class="rail-card__body">
                <h3 class="rail-card__title">{{ card.label }}</h3>
                <p class="rail-card__desc">{{ card.description }}</p>
                <span v-if="card.meta" class="rail-card__meta">{{ card.meta }}</span>
              </div>
            </RouterLink>
          </div>
        </div>
      </section>

      <!-- ═══════ 03 · BROWSE OUR RENTALS ═══════ -->
      <section class="section section--rail section--dark">
        <div class="container container--editorial">
          <header class="rail-head">
            <div>
              <p class="eyebrow eyebrow--gold">Browse our rentals</p>
              <h2 class="section-title">Everything for the <em>day.</em></h2>
            </div>
            <RouterLink to="/rentals" class="rail-more rail-more--onDark">View all rentals →</RouterLink>
          </header>

          <div class="rail">
            <template v-if="rentalCategories.length">
              <RouterLink
                v-for="card in rentalCategories"
                :key="card.to"
                :to="card.to"
                class="rail-card rail-card--compact"
              >
                <div class="rail-card__media">
                  <img v-if="card.image" :src="card.image" :alt="card.label" loading="lazy" />
                  <div v-else class="rail-card__placeholder" />
                </div>
                <div class="rail-card__body">
                  <h3 class="rail-card__title">{{ card.label }}</h3>
                  <p class="rail-card__desc">{{ card.description }}</p>
                </div>
              </RouterLink>
            </template>
            <template v-else>
              <div v-for="i in 4" :key="`rs-${i}`" class="rail-card rail-card--compact rail-card--skeleton" />
            </template>
          </div>
        </div>
      </section>

      <!-- ═══════ 04 · POPULAR PACKAGES ═══════ -->
      <section class="section section--rail">
        <div class="container container--editorial">
          <header class="rail-head">
            <div>
              <p class="eyebrow">Popular packages</p>
              <h2 class="section-title">Start from a package,<br /><em>tailor to you.</em></h2>
            </div>
            <RouterLink to="/packages" class="rail-more">View all packages →</RouterLink>
          </header>

          <div v-if="loading.hero" class="rail">
            <div v-for="i in 4" :key="i" class="rail-card rail-card--tall rail-card--skeleton" />
          </div>
          <div v-else-if="packageRail.length" class="rail">
            <RouterLink
              v-for="card in packageRail"
              :key="card.to"
              :to="card.to"
              class="rail-card rail-card--tall"
            >
              <div class="rail-card__media">
                <img v-if="card.image" :src="card.image" :alt="card.label" loading="lazy" />
                <div v-else class="rail-card__placeholder" />
              </div>
              <div class="rail-card__body">
                <h3 class="rail-card__title">{{ card.label }}</h3>
                <p class="rail-card__desc">{{ card.description }}</p>
                <span v-if="card.meta" class="rail-card__meta">{{ card.meta }}</span>
              </div>
            </RouterLink>
          </div>
          <p v-else class="pkg-empty">
            New packages are being prepared.
            <RouterLink to="/get-a-quote">Ask us for a bespoke quote →</RouterLink>
          </p>
        </div>
      </section>

      <!-- ═══════ 05 · POPULAR HIRE ITEMS ═══════ -->
      <section v-if="hireItemsRail.length" class="section section--rail">
        <div class="container container--editorial">
          <header class="rail-head">
            <div>
              <p class="eyebrow">Popular hire items</p>
              <h2 class="section-title">Add to your <em>hire list.</em></h2>
            </div>
            <RouterLink to="/rentals" class="rail-more">See full inventory →</RouterLink>
          </header>

          <div class="rail">
            <RouterLink
              v-for="card in hireItemsRail"
              :key="card.to"
              :to="card.to"
              class="rail-card rail-card--compact"
            >
              <div class="rail-card__media">
                <img :src="card.image!" :alt="card.label" loading="lazy" />
              </div>
              <div class="rail-card__body">
                <h3 class="rail-card__title">{{ card.label }}</h3>
                <p class="rail-card__desc">{{ card.description }}</p>
                <span v-if="card.meta" class="rail-card__meta">{{ card.meta }}</span>
              </div>
            </RouterLink>
          </div>
        </div>
      </section>

      <!-- ═══════ 06 · A LITTLE INSPIRATION ═══════ -->
      <section v-if="galleryRail.length" class="section section--rail">
        <div class="container container--editorial">
          <header class="rail-head">
            <div>
              <p class="eyebrow">A little inspiration</p>
              <h2 class="section-title">Real events, <em>recently.</em></h2>
            </div>
            <RouterLink to="/gallery" class="rail-more">View full gallery →</RouterLink>
          </header>

          <div class="rail">
            <RouterLink
              v-for="(card, i) in galleryRail"
              :key="`${card.to}-${i}`"
              :to="card.to"
              class="rail-card rail-card--frame"
            >
              <div class="rail-card__media rail-card__media--square">
                <img :src="card.image!" :alt="card.label" loading="lazy" />
              </div>
              <span class="rail-card__caption">{{ card.label }}</span>
            </RouterLink>
          </div>
        </div>
      </section>

      <!-- ═══════ 07 · THE FUNWORLD EXPERIENCE ═══════ -->
      <section class="section section--dark">
        <div class="container container--editorial">
          <header class="section-head">
            <p class="eyebrow eyebrow--gold">The Funworld experience</p>
            <h2 class="section-title">One team. <em>Every detail.</em></h2>
          </header>
          <div class="process-grid">
            <div class="process-step">
              <span class="process-step__num">01</span>
              <h3>Tell us the vision</h3>
              <p>A short call or WhatsApp — dates, guest count, the mood you want to create.</p>
            </div>
            <div class="process-step">
              <span class="process-step__num">02</span>
              <h3>Get a tailored plan</h3>
              <p>A fixed quote, a run-of-show, and a clear inventory of what we'll bring.</p>
            </div>
            <div class="process-step">
              <span class="process-step__num">03</span>
              <h3>We deliver</h3>
              <p>Our own crew and equipment arrive on time, set the scene, and stay through breakdown.</p>
            </div>
            <div class="process-step">
              <span class="process-step__num">04</span>
              <h3>You enjoy</h3>
              <p>You stay a guest at your own event. We handle the rest.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════ 08 · FINAL CTA ═══════ -->
      <section class="section">
        <div class="container container--editorial">
          <div class="cta">
            <div class="cta__copy">
              <p class="eyebrow">Ready when you are</p>
              <h2 class="section-title">Let's plan something<br /><em>unforgettable.</em></h2>
              <p class="lead">Send us a few details and we'll come back with a tailored quote within a few hours.</p>
            </div>
            <div class="cta__actions">
              <RouterLink to="/get-a-quote" class="btn btn--gold">Get a quote</RouterLink>
              <WhatsAppButton message="Hello Funworld Events! I'd like to plan an event." source-ref="home_cta" variant="ghost" />
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   BASE
═══════════════════════════════════════════════════════════════ */
.container--editorial { max-width: var(--container-editorial, 1200px); margin: 0 auto; padding: 0 5vw; }
.section { padding: clamp(4rem, 8vw, 6.5rem) 0; }
.section--dark { background: var(--color-plum, #2b0f2e); color: var(--color-ivory, #fcf9f4); }
.section-head { max-width: 720px; margin-bottom: 3rem; }
.section-title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(2rem, 4vw, 3.2rem);
  font-weight: 300; line-height: 1.05; letter-spacing: -0.02em;
  margin: 0; color: var(--color-charcoal, #1a1417);
}
.section--dark .section-title { color: var(--color-ivory, #fcf9f4); }
.section-title em { font-style: italic; color: var(--color-plum, #2b0f2e); }
.section--dark .section-title em { color: var(--color-gold, #d4af6a); }
.lead { font-family: var(--font-body, "Manrope", sans-serif); font-size: clamp(1.05rem, 1.2vw, 1.2rem); line-height: 1.6; color: var(--color-text-muted, #5a4f56); max-width: 55ch; }
.section--dark .lead { color: rgba(252, 249, 244, 0.75); }
.eyebrow { font-family: var(--font-body, "Manrope", sans-serif); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: var(--color-clay, #c4a582); margin: 0 0 1rem; }
.eyebrow--gold { color: var(--color-gold, #d4af6a); }

/* ═══════════════════════════════════════════════════════════════
   CINEMATIC HERO
═══════════════════════════════════════════════════════════════ */
.hero-wrapper { position: relative; height: 200vh; background: var(--color-plum, #2b0f2e); }
.hero-sticky {
  position: sticky; top: 0; height: 100vh;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
  transform: scale(calc(1.02 - (var(--scroll-progress) * 0.02)));
}
.hero__media { position: absolute; inset: 0; z-index: 0; }
.hero__img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 1400ms ease-in-out; }
.hero__img--active { opacity: 1; }
.hero__overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(26, 20, 23, 0.5) 0%, rgba(43, 15, 46, calc(0.6 + (var(--scroll-progress) * 0.35))) 100%),
              radial-gradient(ellipse at center, transparent 0%, rgba(26, 20, 23, 0.45) 100%);
  z-index: 1;
}
.hero__content {
  position: relative;
  z-index: 4;
  width: 100%;
  max-width: var(--container-editorial, 1200px);
  margin: 0 auto;
  padding: 0 5vw;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100%;
}
.hero__panel {
  max-width: 680px;
  padding: 2rem 0 1.5rem;
}
.hero__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  font-weight: 300;
  line-height: 1.02;
  letter-spacing: -0.025em;
  color: var(--color-ivory, #fcf9f4);
  margin: 0 0 1.25rem;
  text-wrap: balance;
}
.hero__lead {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: clamp(1rem, 1.4vw, 1.2rem);
  line-height: 1.65;
  color: rgba(252, 249, 244, 0.82);
  max-width: 52ch;
  margin: 0;
}
.hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.85rem;
  margin-top: 1.5rem;
}

/* ─── Search bar ─── */
.hero-search {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
  padding: 1rem;
  margin-top: 1.5rem;
  background: rgba(252, 249, 244, 0.94);
  border: 1px solid rgba(196, 165, 130, 0.4);
  border-radius: 14px;
  backdrop-filter: blur(8px);
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.25);
  max-width: 720px;
}
.hero-search__field { display: flex; flex-direction: column; gap: 0.3rem; min-width: 150px; }
.hero-search__field--grow { flex: 1 1 240px; }
.hero-search__label {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-clay, #c4a582);
}
.hero-search__input {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.9rem;
  color: var(--color-charcoal, #1a1417);
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(26, 20, 23, 0.2);
  padding: 0.35rem 0;
  outline: none;
  transition: border-color 200ms ease;
}
.hero-search__input:focus { border-bottom-color: var(--color-gold, #d4af6a); }
.hero-search__submit {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--color-ivory, #fcf9f4);
  background: var(--color-plum, #2b0f2e);
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1.4rem;
  cursor: pointer;
  transition: background 200ms ease, transform 200ms ease;
  white-space: nowrap;
}
.hero-search__submit:hover { background: var(--color-charcoal, #1a1417); transform: translateY(-1px); }

/* ─── Hero dots ─── */
.hero__dots { display: flex; gap: 0.5rem; margin-top: 2rem; padding-bottom: 1rem; }
.hero__dot {
  width: 28px; height: 3px; border-radius: 2px; border: none;
  background: rgba(252, 249, 244, 0.35); cursor: pointer; padding: 0;
  transition: background 250ms ease, width 250ms ease;
}
.hero__dot--active { background: var(--color-gold, #d4af6a); width: 42px; }
.hero__dot:hover { background: rgba(252, 249, 244, 0.6); }
.hero__dot--active:hover { background: var(--color-gold, #d4af6a); }

/* ─── Slide transition ─── */
.slide-fade-enter-active,
.slide-fade-leave-active { transition: opacity 500ms ease, transform 500ms ease; }
.slide-fade-enter-from { opacity: 0; transform: translateY(16px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-16px); }

/* ═══════════════════════════════════════════════════════════════
   PAGE BODY
═══════════════════════════════════════════════════════════════ */
.page-body-wrapper { position: relative; background: var(--color-ivory, #fcf9f4); }
.page-body { position: relative; z-index: 1; }
.scroll-progress {
  position: fixed; top: 0; left: 0; width: 3px; height: 100vh;
  z-index: 50; pointer-events: none; opacity: 0.6;
}
.scroll-progress__fill {
  display: block; width: 100%; height: 100%;
  background: var(--color-gold, #d4af6a);
  transform-origin: top;
  transition: transform 100ms linear;
}

/* ═══════════════════════════════════════════════════════════════
   RAIL SECTIONS
═══════════════════════════════════════════════════════════════ */
.section--rail { padding: clamp(3.5rem, 7vw, 5.5rem) 0; }
.rail-head {
  display: flex; flex-wrap: wrap; align-items: flex-end;
  justify-content: space-between; gap: 1rem; margin-bottom: 2rem;
}
.rail-more {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.85rem; font-weight: 600;
  color: var(--color-plum, #2b0f2e); text-decoration: none; white-space: nowrap;
  border-bottom: 1px solid transparent;
  transition: border-color 200ms ease;
}
.rail-more:hover { border-bottom-color: var(--color-plum, #2b0f2e); }
.rail-more--onDark { color: var(--color-gold, #d4af6a); }
.rail-more--onDark:hover { border-bottom-color: var(--color-gold, #d4af6a); }

/* ─── Horizontal rail ─── */
.rail {
  display: flex;
  gap: 1.25rem;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  padding-bottom: 1.5rem;
  margin: 0 -5vw;
  padding-left: 5vw;
  padding-right: 5vw;
  scrollbar-width: thin;
  scrollbar-color: rgba(43, 15, 46, 0.2) transparent;
}
.rail::-webkit-scrollbar { height: 6px; }
.rail::-webkit-scrollbar-track { background: transparent; }
.rail::-webkit-scrollbar-thumb { background: rgba(43, 15, 46, 0.2); border-radius: 3px; }
.section--dark .rail::-webkit-scrollbar-thumb { background: rgba(252, 249, 244, 0.2); }

/* ─── Rail card ─── */
.rail-card {
  flex: 0 0 auto;
  scroll-snap-align: start;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 2px 12px rgba(26, 20, 23, 0.06);
  transition: transform 300ms ease, box-shadow 300ms ease;
}
.rail-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(26, 20, 23, 0.12); }

.rail-card--tall { width: 300px; }
.rail-card--compact { width: 240px; }
.rail-card--frame {
  width: 200px;
  background: transparent;
  box-shadow: none;
  overflow: visible;
}
.rail-card--frame:hover { transform: translateY(-3px); box-shadow: none; }

/* ─── Card media ─── */
.rail-card__media {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--color-ivory, #fcf9f4);
}
.rail-card--tall .rail-card__media { aspect-ratio: 3 / 4; }
.rail-card--compact .rail-card__media { aspect-ratio: 1 / 1; }
.rail-card__media--square { aspect-ratio: 1 / 1; border-radius: 10px; }

.rail-card__media img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 600ms ease;
}
.rail-card:hover .rail-card__media img { transform: scale(1.05); }

.rail-card__placeholder {
  width: 100%; height: 100%;
  background: linear-gradient(135deg, var(--color-ivory, #fcf9f4) 0%, rgba(196, 165, 130, 0.15) 100%);
}

/* ─── Card body ─── */
.rail-card__body { padding: 1rem 1.1rem 1.25rem; display: flex; flex-direction: column; gap: 0.35rem; }
.rail-card--frame .rail-card__body { padding: 0.6rem 0 0; }

.rail-card__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.05rem;
  font-weight: 400;
  line-height: 1.25;
  margin: 0;
  color: var(--color-charcoal, #1a1417);
}
.rail-card__desc {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.82rem;
  line-height: 1.45;
  color: var(--color-text-muted, #5a4f56);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.rail-card__meta {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-clay, #c4a582);
  margin-top: 0.35rem;
}
.rail-card__caption {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.78rem;
  color: var(--color-text-muted, #5a4f56);
  display: block;
  line-height: 1.3;
}

/* ─── Skeleton ─── */
.rail-card--skeleton {
  pointer-events: none;
  background: rgba(43, 15, 46, 0.04);
  min-height: 320px;
  animation: skeleton-pulse 1.6s ease-in-out infinite;
}
.section--dark .rail-card--skeleton { background: rgba(252, 249, 244, 0.06); }
@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}

/* ═══════════════════════════════════════════════════════════════
   PROCESS GRID
═══════════════════════════════════════════════════════════════ */
.process-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 2rem;
  margin-top: 1rem;
}
.process-step {
  padding: 1.5rem 0;
  border-top: 1px solid rgba(252, 249, 244, 0.15);
}
.process-step__num {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 0.85rem;
  font-weight: 400;
  letter-spacing: 0.1em;
  color: var(--color-gold, #d4af6a);
  display: block;
  margin-bottom: 0.75rem;
}
.process-step h3 {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.35rem;
  font-weight: 300;
  line-height: 1.2;
  margin: 0 0 0.6rem;
  color: var(--color-ivory, #fcf9f4);
}
.process-step p {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.9rem;
  line-height: 1.6;
  color: rgba(252, 249, 244, 0.65);
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════════
   FINAL CTA
═══════════════════════════════════════════════════════════════ */
.cta {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 2.5rem;
  padding: clamp(2.5rem, 5vw, 4rem) 0;
  border-top: 1px solid rgba(43, 15, 46, 0.12);
}
.cta__copy .lead { margin-top: 1rem; }
.cta__actions { display: flex; flex-wrap: wrap; gap: 0.85rem; align-items: center; }

/* ═══════════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════════ */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 0.85rem 1.9rem;
  border-radius: 6px;
  text-decoration: none;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 220ms ease, color 220ms ease, border-color 220ms ease, transform 220ms ease;
}
.btn:hover { transform: translateY(-1px); }
.btn--gold { background: var(--color-gold, #d4af6a); color: var(--color-charcoal, #1a1417); }
.btn--gold:hover { background: #e0bc78; }
.btn--ghost-light { background: transparent; color: var(--color-ivory, #fcf9f4); border-color: rgba(252, 249, 244, 0.4); }
.btn--ghost-light:hover { background: rgba(252, 249, 244, 0.1); border-color: rgba(252, 249, 244, 0.7); }
.btn--ghost { background: transparent; color: var(--color-plum, #2b0f2e); border-color: rgba(43, 15, 46, 0.3); }
.btn--ghost:hover { background: rgba(43, 15, 46, 0.05); border-color: var(--color-plum, #2b0f2e); }

/* ═══════════════════════════════════════════════════════════════
   MISC
═══════════════════════════════════════════════════════════════ */
.pkg-empty {
  font-family: var(--font-body, "Manrope", sans-serif);
  font-size: 0.95rem;
  color: var(--color-text-muted, #5a4f56);
  padding: 2rem 0;
}
.pkg-empty a { color: var(--color-plum, #2b0f2e); font-weight: 600; text-decoration: underline; }

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════════ */
@media (max-width: 900px) {
  .hero-wrapper { height: 180vh; }
  .hero__panel { padding: 1rem 0; }
  .cta { grid-template-columns: 1fr; gap: 1.5rem; }
  .rail-card--tall { width: 260px; }
  .rail-card--compact { width: 210px; }
}

@media (max-width: 640px) {
  .hero-wrapper { height: 160vh; }
  .hero__content { padding: 0 6vw; }
  .hero-search {
    flex-direction: column;
    align-items: stretch;
    gap: 0.9rem;
    padding: 1.1rem;
  }
  .hero-search__field { min-width: 0; }
  .hero-search__submit { width: 100%; padding: 0.75rem; }
  .hero__actions { gap: 0.65rem; }
  .btn { padding: 0.75rem 1.5rem; font-size: 0.84rem; }
  .rail { gap: 1rem; margin: 0 -6vw; padding-left: 6vw; padding-right: 6vw; }
  .rail-card--tall { width: 240px; }
  .rail-card--compact { width: 180px; }
  .rail-card--frame { width: 160px; }
  .process-grid { gap: 1.25rem; }
  .process-step { padding: 1.1rem 0; }
  .scroll-progress { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .hero-sticky { transform: none; }
  .hero__img { transition: none; }
  .rail-card { transition: none; }
  .rail-card:hover { transform: none; }
  .rail-card:hover .rail-card__media img { transform: none; }
  .slide-fade-enter-active,
  .slide-fade-leave-active { transition: none; }
  .rail-card--skeleton { animation: none; }
  .scroll-progress__fill { transition: none; }
}
</style>



$neon = "postgresql://funworld_cms_db_user:zsePCrFCRsCHOlxZaMsG2BcLnTbUuLQr@dpg-dbk3uv6c6qcc73dff1e0-a.frankfurt-postgres.render.com/funworld_cms_db?sslmode=require&channel_binding=require"

& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" `
  --dbname="$neon" `
  --data-only `
  --no-owner `
  --no-acl `
  --verbose `
  .\funworld_data.dump


$neon = "postgresql://funworld_cms_db_user:zsePCrFCRsCHOlxZaMsG2BcLnTbUuLQr@dpg-dbk3uv6c6qcc73dff1e0-a.frankfurt-postgres.render.com/funworld_cms_db?sslmode=require&channel_binding=require"

& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" `
  --dbname="$neon" `
  --format=custom `
  --no-owner `
  --no-acl `
  --file=".\neon_before_restore.dump"







postgresql://funworld_cms_db_user:zsePCrFCRsCHOlxZaMsG2BcLnTbUuLQr@dpg-dbk3uv6c6qcc73dff1e0-a.frankfurt-postgres.render.com/funworld_cms_db


$env:RENDER_DATABASE_URL = Read-Host "postgresql://funworld_cms_db_user:zsePCrFCRsCHOlxZaMsG2BcLnTbUuLQr@dpg-dbk3uv6c6qcc73dff1e0-a.frankfurt-postgres.render.com/funworld_cms_db"
$env:RENDER_DATABASE_URL = Read-Host "Paste updated Render External Database URL"
PGPASSWORD=zsePCrFCRsCHOlxZaMsG2BcLnTbUuLQr psql -h dpg-dbk3uv6c6qcc73dff1e0

  postgresql://funworld_cms_db_user:zsePCrFCRsCHOlxZaMsG2BcLnTbUuLQr@dpg-dbk3uv6c6qcc73dff1e0-a.frankfurt-postgres.render.com/funworld_cms_db