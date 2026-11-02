<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { http } from "../../api.ts";
import StatusPill from "../../components/admin/StatusPill.vue";

const queues = ref<any>({ unassigned: [], due_followups: [], stale: [] });
const loading = ref(true);

async function load() {
  try {
    const { data } = await http.get("/enquiries/queue");
    queues.value = data.data;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>

<template>
  <div class="dash">
    <div class="dash__head">
      <div>
        <p class="eyebrow">Today</p>
        <h1>Dashboard</h1>
      </div>
      <RouterLink to="/admin/enquiries" class="btn btn--primary">All enquiries</RouterLink>
    </div>

    <div class="kpi-grid">
      <RouterLink to="/admin/enquiries" class="kpi">
        <p class="kpi__label">Unassigned</p>
        <p class="kpi__value">{{ queues.unassigned.length }}</p>
      </RouterLink>
      <RouterLink to="/admin/enquiries" class="kpi">
        <p class="kpi__label">Due follow-ups</p>
        <p class="kpi__value">{{ queues.due_followups.length }}</p>
      </RouterLink>
      <RouterLink to="/admin/enquiries" class="kpi">
        <p class="kpi__label">Stale enquiries</p>
        <p class="kpi__value">{{ queues.stale.length }}</p>
      </RouterLink>
    </div>

    <div class="panel">
      <h2>Unassigned</h2>
      <div v-if="!queues.unassigned.length" class="empty">Nothing waiting.</div>
      <ul v-else class="queue">
        <li v-for="e in queues.unassigned" :key="e.id">
          <RouterLink :to="`/admin/enquiries/${e.id}`" class="queue__item">
            <div>
              <div class="queue__name">{{ e.customer?.full_name ?? "—" }}</div>
              <div class="queue__ref">{{ e.reference }}</div>
            </div>
            <StatusPill :status="e.status" kind="enquiry" />
          </RouterLink>
        </li>
      </ul>
    </div>

    <div class="panel">
      <h2>Due follow-ups</h2>
      <div v-if="!queues.due_followups.length" class="empty">Nothing due.</div>
      <ul v-else class="queue">
        <li v-for="e in queues.due_followups" :key="e.id">
          <RouterLink :to="`/admin/enquiries/${e.id}`" class="queue__item">
            <div>
              <div class="queue__name">{{ e.customer?.full_name ?? "—" }}</div>
              <div class="queue__ref">{{ e.reference }} • {{ new Date(e.next_follow_up_at).toLocaleDateString() }}</div>
            </div>
            <StatusPill :status="e.status" kind="enquiry" />
          </RouterLink>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.dash__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-6); }
.dash__head h1 { margin: 0; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sp-4);
  margin-bottom: var(--sp-6);
}
.kpi {
  display: block;
  background: #fff;
  border-radius: var(--radius-md);
  padding: var(--sp-5);
  border: 1px solid var(--color-border-soft);
  transition: transform var(--dur-fast);
}
.kpi:hover { transform: translateY(-2px); }
.kpi__label { font-size: var(--fs-xs); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-gold); margin: 0 0 var(--sp-2); }
.kpi__value { font-family: var(--font-display); font-size: var(--fs-3xl); color: var(--color-plum); margin: 0; }

.panel {
  background: #fff;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  padding: var(--sp-5);
  margin-bottom: var(--sp-5);
}
.panel h2 { font-size: var(--fs-lg); margin: 0 0 var(--sp-4); }

.empty { color: var(--color-text-muted); font-size: var(--fs-sm); }
.queue { list-style: none; padding: 0; margin: 0; }
.queue__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-3) 0;
  border-bottom: 1px solid var(--color-border-soft);
}
.queue li:last-child .queue__item { border-bottom: none; }
.queue__name { font-weight: 500; color: var(--color-plum); }
.queue__ref { font-size: var(--fs-xs); color: var(--color-text-muted); }
</style>