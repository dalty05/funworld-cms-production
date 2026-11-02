<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted  } from "vue";
import { http } from "../api";

interface GalleryImage {
  id: string;
  url: string;
  thumb_url: string;
  alt_text: string;
  caption: string | null;
  is_featured: boolean;
  album: { slug: string; name: string } | null;
}

interface AlbumGroup {
  slug: string;
  name: string;
  images: GalleryImage[];
}

const images = ref<GalleryImage[]>([]);
const albums = ref<any[]>([]);
const loading = ref(true);
const filter = ref<string | null>(null);

// ── Lightbox State ─────────────────────────────────────────────
const activeImage = ref<GalleryImage | null>(null);
const activeAlbumImages = ref<GalleryImage[]>([]);
const activeImageIndex = ref<number>(0);

async function load() {
  loading.value = true;
  try {
    const params: any = {};
    if (filter.value) params.category = filter.value;
    
    const [imgRes, albRes] = await Promise.all([
      http.get("/gallery", { params }),
      http.get("/gallery/albums"),
    ]);
    
    images.value = imgRes.data.data ?? [];
    albums.value = albRes.data.data ?? [];
  } catch (err) {
    console.error("Failed to load gallery", err);
  } finally {
    loading.value = false;
  }
}

onMounted(load);

function setFilter(cat: string | null) {
  filter.value = cat;
  load();
}

// ── Grouping Logic ─────────────────────────────────────────────
// Groups images into their respective albums. 
// Images without an album are grouped under "General".
const groupedCollections = computed<AlbumGroup[]>(() => {
  const groups: Record<string, AlbumGroup> = {};
  const generalGroup: AlbumGroup = { slug: "general", name: "General", images: [] };

  // Initialize groups from albums API to ensure empty albums show up (optional)
  albums.value.forEach((alb: any) => {
    groups[alb.slug] = { slug: alb.slug, name: alb.name, images: [] };
  });

  images.value.forEach((img) => {
    if (img.album && img.album.slug) {
      if (!groups[img.album.slug]) {
        groups[img.album.slug] = { slug: img.album.slug, name: img.album.name, images: [] };
      }
      groups[img.album.slug].images.push(img);
    } else {
      generalGroup.images.push(img);
    }
  });

  // Filter out empty albums, or add general if it has images
  const result = Object.values(groups).filter((g) => g.images.length > 0);
  if (generalGroup.images.length > 0) {
    result.push(generalGroup);
  }

  // Sort each group so featured images are first
  result.forEach((group) => {
    group.images.sort((a, b) => (b.is_featured ? 1 : 0) - (a.is_featured ? 1 : 0));
  });

  return result;
});

// ── Lightbox Logic ─────────────────────────────────────────────
function openLightbox(img: GalleryImage, albumImages: GalleryImage[]) {
  activeImage.value = img;
  activeAlbumImages.value = albumImages;
  activeImageIndex.value = albumImages.findIndex((i) => i.id === img.id);
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  activeImage.value = null;
  activeAlbumImages.value = [];
  document.body.style.overflow = "";
}

function nextImage() {
  if (activeImageIndex.value < activeAlbumImages.value.length - 1) {
    activeImageIndex.value++;
    activeImage.value = activeAlbumImages.value[activeImageIndex.value];
  }
}

function prevImage() {
  if (activeImageIndex.value > 0) {
    activeImageIndex.value--;
    activeImage.value = activeAlbumImages.value[activeImageIndex.value];
  }
}

function jumpToImage(img: GalleryImage) {
  activeImage.value = img;
  activeImageIndex.value = activeAlbumImages.value.findIndex((i) => i.id === img.id);
}

function onKey(e: KeyboardEvent) {
  if (!activeImage.value) return;
  if (e.key === "Escape") closeLightbox();
  if (e.key === "ArrowRight") nextImage();
  if (e.key === "ArrowLeft") prevImage();
}

onMounted(() => window.addEventListener("keydown", onKey));
onUnmounted(() => window.removeEventListener("keydown", onKey));
</script>

<template>
  <section class="gallery-page">
    <div class="container container--editorial">
      <header class="gallery-header">
        <p class="eyebrow">Gallery</p>
        <h1 class="gallery-header__title">Popular Collections</h1>
        
        <!-- Filter Pills -->
        <div class="filters">
          <button :class="{ active: filter === null }" @click="setFilter(null)">All</button>
          <button
            v-for="cat in ['weddings', 'kids', 'corporate', 'fundays']"
            :key="cat"
            :class="{ active: filter === cat }"
            @click="setFilter(cat)"
          >
            {{ cat.charAt(0).toUpperCase() + cat.slice(1) }}
          </button>
        </div>
      </header>

      <!-- Loading Skeletons -->
      <div v-if="loading" class="collections-grid">
        <div v-for="i in 3" :key="i" class="collection-card skeleton" />
      </div>

      <!-- Empty State -->
      <div v-else-if="!groupedCollections.length" class="empty-state">
        <p>No photos yet. Check back soon.</p>
      </div>

      <!-- Collections Grid -->
      <div v-else class="collections-grid">
        <article
          v-for="group in groupedCollections"
          :key="group.slug"
          class="collection-card"
        >
          <!-- Main Image -->
          <button
            class="collection-card__main"
            @click="openLightbox(group.images[0], group.images)"
          >
            <img
              :src="group.images[0].thumb_url"
              :alt="group.images[0].alt_text"
              loading="lazy"
            />
          </button>

          <!-- Thumbnails (Up to 3) -->
          <div class="collection-card__thumbs" v-if="group.images.length > 1">
            <button
              v-for="img in group.images.slice(1, 4)"
              :key="img.id"
              class="thumb-btn"
              @click="openLightbox(img, group.images)"
            >
              <img
                :src="img.thumb_url"
                :alt="img.alt_text"
                loading="lazy"
              />
            </button>
          </div>

          <!-- Card Footer -->
          <div class="collection-card__footer">
            <h3 class="collection-card__title">{{ group.name }}</h3>
            <span class="collection-card__count">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              {{ group.images.length }}
            </span>
          </div>
        </article>
      </div>
    </div>

    <!-- ═══════════ LIGHTBOX ═══════════ -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="activeImage"
          class="lightbox"
          @click.self="closeLightbox"
        >
          <button class="lightbox__close" @click="closeLightbox" aria-label="Close">✕</button>
          
          <!-- Navigation Arrows -->
          <button 
            v-if="activeImageIndex > 0" 
            class="lightbox__nav lightbox__nav--prev" 
            @click.stop="prevImage"
            aria-label="Previous image"
          >
            ‹
          </button>
          
          <button 
            v-if="activeImageIndex < activeAlbumImages.length - 1" 
            class="lightbox__nav lightbox__nav--next" 
            @click.stop="nextImage"
            aria-label="Next image"
          >
            ›
          </button>

          <!-- Main Lightbox Content -->
          <div class="lightbox__content">
            <img
              :src="activeImage.url"
              :alt="activeImage.alt_text"
              class="lightbox__img"
            />
            <p v-if="activeImage.caption" class="lightbox__caption">
              {{ activeImage.caption }}
            </p>
          </div>

          <!-- Album Filmstrip (Bottom) -->
          <div class="lightbox__filmstrip" v-if="activeAlbumImages.length > 1">
            <button
              v-for="img in activeAlbumImages"
              :key="img.id"
              class="filmstrip__thumb"
              :class="{ active: img.id === activeImage.id }"
              @click.stop="jumpToImage(img)"
            >
              <img :src="img.thumb_url" :alt="img.alt_text" />
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </section>
</template>

<style scoped>
/* ── Page Layout ──────────────────────────────────────────── */
.gallery-page {
  padding: 4rem 0 6rem;
  background: var(--color-ivory);
  min-height: 100vh;
}

.container--editorial {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 1.25rem;
}

/* ── Header & Filters ─────────────────────────────────────── */
.gallery-header {
  margin-bottom: 3rem;
}

.eyebrow {
  font-family: var(--font-body);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-clay);
  margin: 0 0 0.5rem;
}

.gallery-header__title {
  font-family: var(--font-display);
  font-size: clamp(2rem, 3vw, 2.8rem);
  font-weight: 400;
  color: var(--color-charcoal);
  margin: 0 0 1.5rem;
}

.filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filters button {
  padding: 0.4rem 1rem;
  border-radius: 50px;
  border: 1px solid var(--color-clay);
  background: transparent;
  color: var(--color-charcoal);
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 180ms ease;
}

.filters button:hover {
  border-color: var(--color-plum);
}

.filters button.active {
  background: var(--color-charcoal);
  color: var(--color-ivory);
  border-color: var(--color-charcoal);
}

/* ── Collections Grid ─────────────────────────────────────── */
.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2rem;
}

.collection-card {
  display: flex;
  flex-direction: column;
  background: #ffffff; /* White cards like the reference */
  border-radius: 16px;
  padding: 0.75rem;
  box-shadow: 0 4px 20px rgba(26, 20, 23, 0.04);
  transition: transform 240ms ease, box-shadow 240ms ease;
}

.collection-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(26, 20, 23, 0.08);
}

.collection-card__main {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 12px;
  overflow: hidden;
  padding: 0;
  border: none;
  cursor: zoom-in;
  background: rgba(26, 20, 23, 0.04);
}

.collection-card__main img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 400ms ease;
}

.collection-card__main:hover img {
  transform: scale(1.03);
}

.collection-card__thumbs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.thumb-btn {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  padding: 0;
  border: none;
  cursor: zoom-in;
  background: rgba(26, 20, 23, 0.04);
}

.thumb-btn img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 200ms ease;
}

.thumb-btn:hover img {
  opacity: 0.85;
}

.collection-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0.5rem 0.5rem;
}

.collection-card__title {
  font-family: var(--font-body);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin: 0;
}

.collection-card__count {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* ── Skeleton ─────────────────────────────────────────────── */
.skeleton {
  background: linear-gradient(90deg, rgba(26, 20, 23, 0.03), rgba(26, 20, 23, 0.06), rgba(26, 20, 23, 0.03));
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  aspect-ratio: 4 / 5;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Empty State ──────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 6rem 1rem;
  color: var(--color-text-muted);
  font-family: var(--font-body);
}

/* ── Lightbox Modal ───────────────────────────────────────── */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(26, 20, 23, 0.95);
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(6px);
}

.lightbox__close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 10;
  color: var(--color-ivory);
  background: rgba(255, 255, 255, 0.1);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 200ms ease;
}

.lightbox__close:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Navigation Arrows */
.lightbox__nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-ivory);
  border: none;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  font-size: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 200ms ease;
}

.lightbox__nav:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lightbox__nav--prev {
  left: 1.5rem;
  padding-right: 4px; /* visual centering for the ‹ */
}

.lightbox__nav--next {
  right: 1.5rem;
  padding-left: 4px; /* visual centering for the › */
}

/* Main Content Area */
.lightbox__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 4rem;
  min-height: 0; /* allows flex child to shrink */
}

.lightbox__img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.4);
}

.lightbox__caption {
  margin-top: 1rem;
  color: rgba(252, 249, 244, 0.8);
  font-family: var(--font-body);
  font-size: 0.9rem;
  text-align: center;
}

/* Filmstrip (Bottom) */
.lightbox__filmstrip {
  height: 100px;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 1.5rem;
  overflow-x: auto;
  scrollbar-width: thin;
}

.lightbox__filmstrip::-webkit-scrollbar {
  height: 6px;
}
.lightbox__filmstrip::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.filmstrip__thumb {
  flex: 0 0 auto;
  width: 72px;
  height: 72px;
  border-radius: 6px;
  overflow: hidden;
  padding: 0;
  border: 2px solid transparent;
  cursor: pointer;
  opacity: 0.5;
  transition: all 200ms ease;
  background: rgba(255, 255, 255, 0.05);
}

.filmstrip__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.filmstrip__thumb:hover {
  opacity: 0.8;
}

.filmstrip__thumb.active {
  opacity: 1;
  border-color: var(--color-gold);
}

/* ── Transitions ──────────────────────────────────────────── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 300ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 900px) {
  .collections-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 600px) {
  .collections-grid {
    grid-template-columns: 1fr;
  }
  
  .lightbox__content {
    padding: 4rem 1rem 1rem;
  }
  
  .lightbox__nav {
    display: none; /* Hide arrows on mobile, rely on filmstrip/swipe */
  }
  
  .lightbox__filmstrip {
    height: 80px;
    padding: 0 1rem;
  }
  
  .filmstrip__thumb {
    width: 56px;
    height: 56px;
  }
}
</style>