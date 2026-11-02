<script setup lang="ts">
import { RouterLink } from "vue-router";

defineProps<{
  title: string;
  description: string;
  image: string;
  slug: string;
  accent?: "gold" | "coral" | "sage";
}>();
</script>

<template>
  <RouterLink :to="`/services/${slug}`" class="service-card">
    <div class="service-card__media">
      <img :src="image" :alt="title" loading="lazy" />
      <div class="service-card__media-overlay" />
    </div>
    <div class="service-card__body">
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <span class="service-card__link">
        Explore
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M13 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
    </div>
  </RouterLink>
</template>

<style scoped>
.service-card {
  display: flex;
  flex-direction: column;
  background: var(--color-ivory);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  transition: transform var(--dur-base) var(--ease-out),
              box-shadow var(--dur-base) var(--ease-out);
}
.service-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-glow);
}
.service-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
}
.service-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--dur-slow) var(--ease-out);
}
.service-card:hover .service-card__media img {
  transform: scale(1.05);
}
.service-card__media-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(43,15,46,0) 0%, rgba(43,15,46,0.18) 100%);
}
.service-card__body {
  padding: var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.service-card__body h3 {
  margin: 0;
  font-size: var(--fs-xl);
}
.service-card__body p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--fs-sm);
  line-height: var(--lh-snug);
}
.service-card__link {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  color: var(--color-gold);
  font-weight: 600;
  font-size: var(--fs-sm);
  margin-top: var(--sp-2);
}
.service-card__link svg { width: 16px; height: 16px; transition: transform var(--dur-fast); }
.service-card:hover .service-card__link svg { transform: translateX(4px); }
</style>