<!-- Audit.vue -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { http } from "../../api";
import DataTable from "../../components/admin/DataTable.vue";

const rows = ref<any[]>([]);
const loading = ref(true);
const action = ref("");
const columns = [
  { key: "created_at", label: "When", width: "180px" },
  { key: "action", label: "Action", width: "200px" },
  { key: "entity_type", label: "Entity", width: "120px" },
  { key: "entity_id", label: "ID", width: "260px" },
  { key: "actor_user_id", label: "Actor", width: "260px" },
];
async function load() {
  loading.value = true;
  try {
    const { data } = await http.get("/audit-logs", { params: action.value ? { action: action.value } : {} });
    rows.value = data.data;
  } finally { loading.value = false; }
}
onMounted(load);
</script>
<template>
  <div>
    <div class="page-head">
      <p class="eyebrow">Compliance</p>
      <h1>Audit log</h1>
    </div>
    <div class="filters">
      <input v-model="action" placeholder="Filter by action (e.g. enquiry.qualified)" @input="load" />
    </div>
    <DataTable :columns="columns" :rows="rows" :loading="loading">
      <template #created_at="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
    </DataTable>
  </div>
</template>
<style scoped>
.page-head { margin-bottom: var(--sp-6); }
.page-head h1 { margin: 0; }
.filters { margin-bottom: var(--sp-5); }
.filters input {
  padding: 0.6rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: #fff;
  min-width: 320px;
}
</style>