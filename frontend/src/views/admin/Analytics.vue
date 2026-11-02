<script setup lang="ts">
import { onMounted, ref } from "vue";
import { http } from "../../api";

const overview = ref<any>(null);
const sessions = ref<any[]>([]);
const days = ref(30);
const loading = ref(true);

async function load() {
  loading.value = true;
  try {
    const [o, s] = await Promise.all([
      http.get("/admin/analytics/overview", { params: { days: days.value } }),
      http.get("/admin/analytics/sessions", { params: { limit: 50 } }),
    ]);
    overview.value = o.data.data;
    sessions.value = s.data.data;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">Insights</p>
        <h1>Analytics</h1>
      </div>
      <select v-model.number="days" @change="load" class="range-select">
        <option :value="7">Last 7 days</option>
        <option :value="30">Last 30 days</option>
        <option :value="90">Last 90 days</option>
      </select>
    </div>

    <div v-if="overview" class="kpi-grid">
      <div class="kpi">
        <p class="kpi__label">Page views</p>
        <p class="kpi__value">{{ overview.total_views.toLocaleString() }}</p>
      </div>
      <div class="kpi">
        <p class="kpi__label">Sessions</p>
        <p class="kpi__value">{{ overview.total_sessions.toLocaleString() }}</p>
      </div>
      <div class="kpi">
        <p class="kpi__label">Converted</p>
        <p class="kpi__value">{{ overview.converted_sessions.toLocaleString() }}</p>
      </div>
      <div class="kpi">
        <p class="kpi__label">Conversion rate</p>
        <p class="kpi__value">{{ (overview.conversion_rate * 100).toFixed(1) }}%</p>
      </div>
    </div>

    <div v-if="overview" class="grid-2">
      <div class="panel">
        <h3>Top pages</h3>
        <table class="mini-table">
          <tr v-for="p in overview.top_pages" :key="p.path">
            <td class="mono">{{ p.path }}</td>
            <td class="right">{{ p.views }}</td>
          </tr>
        </table>
      </div>

      <div class="panel">
        <h3>Top countries</h3>
        <table class="mini-table">
          <tr v-for="c in overview.top_countries" :key="c.country">
            <td>{{ c.country }}</td>
            <td class="right">{{ c.views }}</td>
          </tr>
        </table>
      </div>

      <div class="panel">
        <h3>Top cities</h3>
        <table class="mini-table">
          <tr v-for="c in overview.top_cities" :key="c.city">
            <td>{{ c.city }}</td>
            <td class="right">{{ c.views }}</td>
          </tr>
        </table>
      </div>

      <div class="panel">
        <h3>Recent sessions</h3>
        <table class="mini-table">
          <tr v-for="s in sessions" :key="s.session_id">
            <td>{{ s.city ?? "—" }}, {{ s.country ?? "—" }}</td>
            <td class="right">{{ s.page_count }} views</td>
            <td class="right">{{ s.converted ? "✓" : "" }}</td>
          </tr>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-5); }
.page-head h1 { margin: 0; }
.range-select { padding: 0.5rem 0.9rem; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); background: #fff; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--sp-4); margin-bottom: var(--sp-5); }
.kpi { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-5); }
.kpi__label { font-size: var(--fs-xs); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-gold); margin: 0 0 var(--sp-2); }
.kpi__value { font-family: var(--font-display); font-size: var(--fs-2xl); color: var(--color-plum); margin: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-4); }
@media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }
.panel { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-5); }
.panel h3 { font-size: var(--fs-lg); margin: 0 0 var(--sp-3); }
.mini-table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); }
.mini-table td { padding: var(--sp-2) var(--sp-1); border-bottom: 1px solid var(--color-border-soft); }
.mini-table td.right { text-align: right; }
.mono { font-family: monospace; font-size: var(--fs-xs); }
</style>