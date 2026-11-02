<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<template>
  <section class="section nf">
    <div class="container nf-inner">
      <p class="eyebrow">404</p>
      <h1>That page doesn't exist.</h1>
      <p class="lead">But the event does.</p>
      <RouterLink to="/" class="btn btn--primary">Back to home</RouterLink>
    </div>
  </section>
</template>

<style scoped>
.nf { min-height: 60vh; display: flex; align-items: center; }
.nf-inner { text-align: center; }
.nf h1 { margin-bottom: var(--sp-4); }
</style>