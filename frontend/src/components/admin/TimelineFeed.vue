<script setup lang="ts">
defineProps<{ events: any[] }>();

function fmt(dt: string) {
  return new Date(dt).toLocaleString();
}
</script>

<template>
  <ol class="timeline">
    <li v-for="e in events" :key="e.id" class="timeline__item">
      <span class="timeline__dot" />
      <div class="timeline__body">
        <div class="timeline__summary">{{ e.summary ?? e.event_type }}</div>
        <div class="timeline__meta">
          <span>{{ fmt(e.created_at) }}</span>
          <span v-if="e.actor_type">• {{ e.actor_type }}</span>
        </div>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.timeline { list-style: none; padding: 0; margin: 0; position: relative; }
.timeline::before {
  content: "";
  position: absolute;
  left: 5px;
  top: 6px;
  bottom: 6px;
  width: 1px;
  background: var(--color-border-soft);
}
.timeline__item {
  position: relative;
  padding-left: var(--sp-6);
  padding-bottom: var(--sp-4);
}
.timeline__item:last-child { padding-bottom: 0; }
.timeline__dot {
  position: absolute;
  left: 0;
  top: 4px;
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--color-gold);
  border: 2px solid var(--color-ivory);
}
.timeline__summary { font-size: var(--fs-sm); color: var(--color-plum); font-weight: 500; }
.timeline__meta { font-size: var(--fs-xs); color: var(--color-text-muted); margin-top: 2px; }
</style>