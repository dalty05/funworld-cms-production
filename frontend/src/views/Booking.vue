<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import LeadForm from "../components/LeadForm.vue";
import { http } from "../api";

const route = useRoute();
const pkg = ref<any>(null);
const notFound = ref(false);

onMounted(async () => {
  try {
    const { data } = await http.get(`/packages/${route.params.packageSlug}`);
    pkg.value = data.data;
  } catch { notFound.value = true; }
});
</script>

<template>
  <section v-if="pkg" class="section">
    <div class="container booking-grid">
      <div>
        <p class="eyebrow">Booking request</p>
        <h1>{{ pkg.name }}</h1>
        <p v-if="pkg.tagline" class="lead">{{ pkg.tagline }}</p>

        <div v-if="pkg.hero_image_url" class="booking-media glass">
          <img :src="pkg.hero_image_url" :alt="pkg.name" />
        </div>

        <div class="summary">
          <p><strong>Price:</strong> {{ pkg.currency }} {{ pkg.price_amount?.toLocaleString() ?? "on request" }}</p>
          <p v-if="pkg.availability_note"><strong>Availability:</strong> {{ pkg.availability_note }}</p>
        </div>
      </div>

      <LeadForm
        channel="website_booking"
        :event-type="pkg.category?.slug ?? 'other'"
        :source-ref="`booking_${pkg.slug}`"
        :package-id="pkg.id"
      />
    </div>
  </section>

  <section v-else-if="notFound" class="section">
    <div class="container"><h1>Package not found</h1></div>
  </section>
</template>

<style scoped>
.booking-grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: var(--sp-7); align-items: start; }
@media (max-width: 900px) { .booking-grid { grid-template-columns: 1fr; } }
.booking-media { padding: 0; overflow: hidden; margin-top: var(--sp-5); }
.booking-media img { width: 100%; display: block; }
.summary { margin-top: var(--sp-5); font-size: var(--fs-sm); color: var(--color-text-muted); }
.summary strong { color: var(--color-plum); }
</style>