<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { http } from "../api";
import WhatsAppButton from "../components/WhatsAppButton.vue";

const route = useRoute();
const pkg = ref<any>(null);
const notFound = ref(false);

onMounted(async () => {
  try {
    const { data } = await http.get(`/packages/${route.params.slug}`);
    pkg.value = data.data;
  } catch { notFound.value = true; }
});
</script>

<template>
  <section v-if="pkg" class="section">
    <div class="container pkg-detail">
      <div>
        <p class="eyebrow">{{ pkg.category?.name ?? "Package" }}</p>
        <h1>{{ pkg.name }}</h1>
        <p v-if="pkg.tagline" class="lead">{{ pkg.tagline }}</p>

        <div v-if="pkg.price_amount" class="price-block">
          <div class="price-block__amount">
            {{ pkg.currency }} {{ pkg.price_amount.toLocaleString() }}
          </div>
          <div v-if="pkg.price_note" class="price-block__note">{{ pkg.price_note }}</div>
        </div>

        <div class="divider-gold" />

        <div class="pkg-body" v-html="pkg.long_description" />

        <div v-if="pkg.what_is_included?.length" class="included-block">
          <h3>What's included</h3>
          <ul>
            <li v-for="(item, i) in pkg.what_is_included" :key="i">{{ item }}</li>
          </ul>
        </div>

        <div v-if="pkg.what_is_not_included?.length" class="not-included-block">
          <h3>Not included</h3>
          <ul>
            <li v-for="(item, i) in pkg.what_is_not_included" :key="i">{{ item }}</li>
          </ul>
        </div>

        <div class="meta-grid">
          <div v-if="pkg.min_guests || pkg.max_guests">
            <strong>Guests</strong>
            <span>{{ pkg.min_guests ?? "—" }}–{{ pkg.max_guests ?? "—" }}</span>
          </div>
          <div v-if="pkg.duration_hours">
            <strong>Duration</strong>
            <span>{{ pkg.duration_hours }} hours</span>
          </div>
          <div v-if="pkg.availability_note">
            <strong>Availability</strong>
            <span>{{ pkg.availability_note }}</span>
          </div>
        </div>

        <div class="pkg-actions">
          <RouterLink
            :to="`/booking/${pkg.slug}`"
            class="btn btn--primary"
          >Book this package</RouterLink>
          <WhatsAppButton
            phone="254742435999"
            :message="`Hello Funworld Events! I'm interested in the ${pkg.name} package.`"
            :ref="`pkg_${pkg.slug}`"
            variant="ghost"
          />
        </div>
      </div>

      <div v-if="pkg.hero_image_url" class="pkg-detail__media glass">
        <img :src="pkg.hero_image_url" :alt="pkg.name" />
      </div>
    </div>
  </section>

  <section v-else-if="notFound" class="section">
    <div class="container">
      <h1>Package not found</h1>
      <RouterLink to="/packages" class="btn btn--outline">Back to packages</RouterLink>
    </div>
  </section>
</template>

<style scoped>
.pkg-detail { display: grid; grid-template-columns: 1.1fr 1fr; gap: var(--sp-7); align-items: start; }
@media (max-width: 900px) { .pkg-detail { grid-template-columns: 1fr; } }
.price-block { margin: var(--sp-5) 0; padding: var(--sp-4) 0; border-top: 2px solid var(--color-gold); border-bottom: 2px solid var(--color-gold); }
.price-block__amount { font-family: var(--font-display); font-size: var(--fs-3xl); color: var(--color-plum); }
.price-block__note { color: var(--color-text-muted); font-size: var(--fs-sm); }
.pkg-body { color: var(--color-text-muted); line-height: var(--lh-normal); margin: var(--sp-5) 0; }
.included-block, .not-included-block { margin: var(--sp-5) 0; }
.included-block h3, .not-included-block h3 { font-size: var(--fs-lg); margin-bottom: var(--sp-3); }
.included-block ul, .not-included-block ul { list-style: none; padding: 0; display: grid; gap: var(--sp-2); }
.included-block li::before { content: "✓"; color: var(--color-sage); font-weight: 700; margin-right: var(--sp-2); }
.not-included-block li::before { content: "—"; color: var(--color-text-muted); margin-right: var(--sp-2); }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: var(--sp-4); margin: var(--sp-6) 0; padding: var(--sp-4) 0; border-top: 1px solid var(--color-border-soft); }
.meta-grid strong { display: block; font-size: var(--fs-xs); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-gold); margin-bottom: 4px; }
.meta-grid span { color: var(--color-plum); }
.pkg-actions { display: flex; gap: var(--sp-3); flex-wrap: wrap; margin-top: var(--sp-5); }
.pkg-detail__media { padding: 0; overflow: hidden; }
.pkg-detail__media img { width: 100%; display: block; }
</style>