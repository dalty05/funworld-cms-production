<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { http } from "../api";

const props = defineProps<{ kind: "privacy" | "terms" }>();
const key = computed(() => props.kind === "privacy" ? "privacy_policy" : "terms_of_service");
const policy = ref<any>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    const { data } = await http.get(`/settings/policies/${key.value}`);
    policy.value = data.data;
  } catch {
    policy.value = null;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <section class="section">
    <div class="container container--narrow">
      <p class="eyebrow">Legal</p>
      <h1>{{ policy?.label ?? (props.kind === "privacy" ? "Privacy Policy" : "Terms of Service") }}</h1>
      <div class="divider-gold" />
      <div v-if="loading" class="loading">Loading…</div>
      <div v-else-if="policy" class="legal-body" v-html="policy.value_text" />
      <p v-else class="empty">This document hasn't been published yet.</p>
    </div>
  </section>
</template>