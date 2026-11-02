<!--  app.vue -->

<script setup lang="ts">
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";
import SiteHeader from "./components/SiteHeader.vue";
import SiteFooter from "./components/SiteFooter.vue";
import WhatsAppButton from "./components/WhatsAppButton.vue";


import HireListButton from "./components/HireListButton.vue";
import HireListDrawer from "./components/HireListDrawer.vue";

const route = useRoute();
const isAdmin = computed(() => route.path.startsWith("/admin"));
</script>

<template>
  <template v-if="!isAdmin">
    <SiteHeader />
    <main class="main">
      <RouterView />
    </main>
    <SiteFooter />
    <HireListButton />
    <HireListDrawer />
    <WhatsAppButton
      phone="254785068486"
      message="Hello Funworld Events! I'd like to enquire about your services."
      floating
    />
  </template>
  <template v-else>
    <RouterView />
  </template>
</template>

<style scoped>
.main { padding-top: var(--header-h); min-height: 60vh; }
</style>