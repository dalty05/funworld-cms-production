<!-- BlogPost.vue -->
<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { useRoute } from "vue-router";
import { getBlogPost } from "../api";

const route = useRoute();
const post = ref<any>(null);
const loading = ref(true);
const loadError = ref<string | null>(null);

onMounted(async () => {
  try {
    post.value = await getBlogPost(route.params.slug as string);
  } catch (error) {
    console.error("Failed to load blog post:", error);
    loadError.value = "Unable to load this article.";
  } finally {
    loading.value = false;
  }
});

const formattedDate = computed(() =>
  post.value?.published_at
    ? new Date(post.value.published_at).toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : ""
);

// Author name intentionally not displayed per layout spec, but kept for logic.
const authorName = computed(() => {
  const author = post.value?.author;
  if (typeof author === "string") return author;
  if (author && typeof author === "object") {
    return author.name || author.full_name || "Funworld Events";
  }
  return "Funworld Events";
});

// About the site (static content for the sidebar)
const siteAbout = {
  title: "About Funworld Events",
  description:
    "We craft unforgettable celebrations across Kenya — from intimate gatherings to grand galas. Our journal shares planning tips, venue insights, and inspiration for your next event.",
  image: "/images/about-funworld.jpg", 
};
</script>

<template>
  <div class="post-shell">
    <!-- Loading / error -->
    <p v-if="loading" class="state-msg">Loading article...</p>
    <p v-else-if="loadError" class="state-msg state-msg--err">
      {{ loadError }}
    </p>

    <article v-if="post" class="post-layout">
      <!-- ═══════════════════════════════════════════════════════
           LEFT: MAIN COLUMN
      ═══════════════════════════════════════════════════════════ -->
      <main class="post-main">
        <!-- Hero / Title block -->
        <header class="post-header">
          <p v-if="post.category" class="post-header__tag">
            {{ post.category }}
          </p>
          <h1 class="post-header__title">{{ post.title }}</h1>
          <div class="post-header__meta">
            <time :datetime="post.published_at">{{ formattedDate }}</time>
            <template v-if="post.reading_minutes">
              <span class="dot" aria-hidden="true">·</span>
              <span>{{ post.reading_minutes }} min read</span>
            </template>
          </div>
        </header>

        <!-- Featured image -->
        <figure v-if="post.featured_image" class="post-hero-img">
          <img :src="post.featured_image" :alt="post.title" />
        </figure>

        <!-- Lead -->
        <p v-if="post.excerpt" class="post-lead">{{ post.excerpt }}</p>

        <!-- Rich body -->
        <div class="post-body" v-html="post.body_html" />

        <!-- ─── Share strip ─── -->
        <footer class="post-footer">
          <div class="post-footer__share">
            <span class="post-footer__label">Share</span>
            <button class="icon-btn" aria-label="Share on X">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 4l16 16M20 4L4 20" />
              </svg>
            </button>
            <button class="icon-btn" aria-label="Share on Facebook">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M15 3h-2a4 4 0 0 0-4 4v3H6v4h3v7h4v-7h3l1-4h-4V7a1 1 0 0 1 1-1h3z"
                />
              </svg>
            </button>
            <button class="icon-btn" aria-label="Copy link">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
                <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
              </svg>
            </button>
          </div>
          <div v-if="post.tags?.length" class="post-footer__tags">
            <span
              v-for="tag in post.tags"
              :key="tag.slug"
              class="post-tag"
            >
              {{ tag.name }}
            </span>
          </div>
        </footer>
      </main>

      <!-- ═══════════════════════════════════════════════════════
           RIGHT: SIDEBAR
      ═══════════════════════════════════════════════════════════ -->
      <aside class="post-sidebar">
        <!-- About the site -->
        <section class="sidebar-card">
          <h2 class="sidebar-card__title">About</h2>
          <div class="about-block">
            <div class="about-block__media">
              <img
                :src="siteAbout.image"
                :alt="siteAbout.title"
                loading="lazy"
              />
            </div>
            <p class="about-block__name">{{ siteAbout.title }}</p>
            <p class="about-block__desc">{{ siteAbout.description }}</p>
          </div>
        </section>

        <!-- Related posts -->
        <section v-if="post.related?.length" class="sidebar-card">
          <h2 class="sidebar-card__title">Related Posts</h2>
          <ul class="related-list">
            <li
              v-for="rel in post.related"
              :key="rel.slug"
              class="related-item"
            >
              <a :href="`/blog/${rel.slug}`" class="related-item__link">
                <div class="related-item__thumb">
                  <img
                    v-if="rel.featured_image"
                    :src="rel.featured_image"
                    :alt="rel.title"
                    loading="lazy"
                  />
                </div>
                <div class="related-item__body">
                  <h3 class="related-item__title">{{ rel.title }}</h3>
                  <p v-if="rel.excerpt" class="related-item__excerpt">
                    {{ rel.excerpt }}
                  </p>
                </div>
              </a>
            </li>
          </ul>
        </section>
      </aside>
    </article>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   SHELL — soft patterned background like reference
═══════════════════════════════════════════════════════════════ */
.post-shell {
  background-color: #f5f2ed;
  background-image:
    radial-gradient(circle at 1px 1px, rgba(180, 165, 140, 0.18) 1px, transparent 0);
  background-size: 14px 14px;
  color: var(--color-text, #2b0f2e);
  padding-block: var(--sp-6, 2rem) var(--sp-8, 3rem);
  min-height: 100vh;
}

.state-msg {
  max-width: 760px;
  margin: 4rem auto;
  text-align: center;
  font-size: var(--fs-sm, 0.9rem);
  color: var(--color-text-muted);
}
.state-msg--err { color: #a12828; }

/* ═══════════════════════════════════════════════════════════════
   LAYOUT — main + sidebar
═══════════════════════════════════════════════════════════════ */
.post-layout {
  max-width: 1080px;
  margin-inline: auto;
  padding-inline: var(--sp-4, 1rem);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: var(--sp-6, 2rem);
  align-items: start;
}

/* ═══════════════════════════════════════════════════════════════
   MAIN COLUMN — white paper card
═══════════════════════════════════════════════════════════════ */
.post-main {
  background: #fff;
  padding: var(--sp-6, 2rem) var(--sp-6, 2.25rem);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 1px 3px rgba(26, 20, 23, 0.06);
}

/* Header */
.post-header {
  text-align: center;
  padding-bottom: var(--sp-4, 1rem);
  border-bottom: 1px solid var(--color-border-soft, #e8e0d5);
  margin-bottom: var(--sp-5, 1.5rem);
}
.post-header__tag {
  display: inline-block;
  font-size: var(--fs-xs, 0.7rem);
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-text-muted, #8a7a80);
  background: #f4efe7;
  padding: 0.25rem 0.7rem;
  border-radius: 2px;
  margin: 0 0 1rem;
}
.post-header__title {
  font-family: var(--font-display, "Fraunces", Georgia, serif);
  font-weight: 400;
  font-size: clamp(1.6rem, 3.6vw, 2.4rem);
  line-height: 1.2;
  margin: 0 0 0.75rem;
  color: var(--color-plum, #1a1214);
}
.post-header__meta {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 0.4rem;
  font-size: var(--fs-xs, 0.75rem);
  color: var(--color-text-muted, #8a7a80);
  letter-spacing: 0.03em;
}
.post-header__meta .dot { opacity: 0.5; }

/* Hero image */
.post-hero-img {
  margin: 0 0 var(--sp-5, 1.5rem);
  border-radius: 4px;
  overflow: hidden;
}
.post-hero-img img {
  width: 100%;
  display: block;
  object-fit: cover;
  max-height: 420px;
}

/* Lead */
.post-lead {
  font-size: var(--fs-lg, 1.05rem);
  line-height: 1.7;
  color: var(--color-plum, #1a1214);
  margin: 0 0 var(--sp-5, 1.5rem);
  padding-left: var(--sp-3, 0.85rem);
  border-left: 3px solid var(--color-gold, #d4af6a);
}

/* Body */
.post-body {
  color: var(--color-text, #2b0f2e);
  font-size: var(--fs-md, 0.95rem);
  line-height: 1.85;
  max-width: 68ch;
}
.post-body :deep(h2),
.post-body :deep(h3) {
  font-family: var(--font-display, "Fraunces", Georgia, serif);
  color: var(--color-plum, #1a1214);
  font-weight: 500;
  line-height: 1.3;
  margin: 2rem 0 0.75rem;
}
.post-body :deep(h2) { font-size: 1.35rem; }
.post-body :deep(h3) { font-size: 1.15rem; }

.post-body :deep(p) {
  margin: 0 0 1.1rem;
  color: var(--color-text-muted, #4a3b4e);
}

.post-body :deep(a) {
  color: var(--color-plum, #2b0f2e);
  text-decoration: underline;
  text-decoration-color: var(--color-gold, #d4af6a);
  text-underline-offset: 3px;
  transition: color 160ms ease;
}
.post-body :deep(a:hover) { color: var(--color-gold, #d4af6a); }

.post-body :deep(ul),
.post-body :deep(ol) {
  padding-left: 1.25rem;
  margin: 0 0 1.1rem;
  color: var(--color-text-muted, #4a3b4e);
}
.post-body :deep(li) { margin-bottom: 0.45rem; }

.post-body :deep(blockquote) {
  margin: 1.75rem 0;
  padding: 1rem 1.25rem;
  border-left: 3px solid var(--color-gold, #d4af6a);
  background: #fcf9f4;
  border-radius: 0 4px 4px 0;
  font-style: italic;
  color: var(--color-plum, #1a1214);
}

.post-body :deep(img) {
  width: 100%;
  border-radius: 4px;
  margin: 1.5rem 0;
  display: block;
}

.post-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border-soft, #e8e0d5);
  margin: 2rem 0;
}

/* Footer */
.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-3, 0.75rem);
  margin-top: var(--sp-6, 2rem);
  padding-top: var(--sp-4, 1rem);
  border-top: 1px solid var(--color-border-soft, #e8e0d5);
}
.post-footer__share {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.post-footer__label {
  font-size: var(--fs-xs, 0.7rem);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-text-muted, #8a7a80);
  margin-right: 0.25rem;
}
.icon-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1px solid var(--color-border-soft, #e8e0d5);
  background: #fff;
  color: var(--color-plum, #2b0f2e);
  cursor: pointer;
  transition: border-color 160ms ease, background 160ms ease;
}
.icon-btn:hover {
  border-color: var(--color-gold, #d4af6a);
  background: #fcf9f4;
}
.icon-btn svg {
  width: 15px;
  height: 15px;
  stroke: currentColor;
  stroke-width: 1.8;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.post-footer__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.post-tag {
  font-size: var(--fs-xs, 0.7rem);
  padding: 0.22rem 0.65rem;
  border-radius: 999px;
  background: rgba(43, 15, 46, 0.05);
  color: var(--color-plum, #2b0f2e);
  font-weight: 500;
}

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════════════════════ */
.post-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--sp-5, 1.5rem);
  position: sticky;
  top: var(--sp-5, 1.5rem);
}

.sidebar-card {
  background: #fff;
  border-radius: var(--radius-md, 8px);
  padding: var(--sp-4, 1rem);
  box-shadow: 0 1px 3px rgba(26, 20, 23, 0.06);
}
.sidebar-card__title {
  font-family: var(--font-display, "Fraunces", Georgia, serif);
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--color-plum, #1a1214);
  text-align: center;
  margin: 0 0 var(--sp-4, 1rem);
  padding-bottom: var(--sp-3, 0.75rem);
  border-bottom: 1px solid var(--color-border-soft, #e8e0d5);
}

/* About block */
.about-block__media {
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border-radius: 4px;
  background: #f4efe7;
  margin-bottom: var(--sp-3, 0.75rem);
}
.about-block__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.about-block__name {
  font-family: var(--font-display, "Fraunces", Georgia, serif);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-plum, #1a1214);
  margin: 0 0 0.4rem;
}
.about-block__desc {
  font-size: var(--fs-xs, 0.78rem);
  line-height: 1.6;
  color: var(--color-text-muted, #6a5b60);
  margin: 0;
}

/* Related list */
.related-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3, 0.75rem);
}
.related-item__link {
  display: flex;
  gap: var(--sp-3, 0.75rem);
  text-decoration: none;
  color: inherit;
  align-items: flex-start;
  transition: opacity 160ms ease;
}
.related-item__link:hover { opacity: 0.82; }
.related-item__thumb {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: 3px;
  overflow: hidden;
  background: #f4efe7;
}
.related-item__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.related-item__body {
  flex: 1;
  min-width: 0;
}
.related-item__title {
  font-family: var(--font-display, "Fraunces", Georgia, serif);
  font-size: 0.85rem;
  font-weight: 500;
  line-height: 1.35;
  margin: 0 0 0.25rem;
  color: var(--color-plum, #1a1214);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.related-item__excerpt {
  font-size: var(--fs-xs, 0.72rem);
  line-height: 1.5;
  color: var(--color-text-muted, #8a7a80);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════════ */
@media (max-width: 900px) {
  .post-layout {
    grid-template-columns: 1fr;
    gap: var(--sp-5, 1.5rem);
  }
  .post-sidebar {
    position: static;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--sp-4, 1rem);
  }
}
@media (max-width: 640px) {
  .post-shell { padding-block: 0 var(--sp-6, 2rem); }
  .post-main {
    padding: var(--sp-4, 1.25rem) var(--sp-4, 1.25rem);
    border-radius: 0;
  }
  .post-header {
    text-align: left;
  }
  .post-header__meta { justify-content: flex-start; }
  .post-footer {
    flex-direction: column;
    align-items: flex-start;
  }
  .post-sidebar {
    grid-template-columns: 1fr;
    padding-inline: var(--sp-4, 1rem);
  }
}

@media (prefers-reduced-motion: reduce) {
  .icon-btn,
  .related-item__link,
  .post-body :deep(a) {
    transition: none !important;
  }
}
</style>