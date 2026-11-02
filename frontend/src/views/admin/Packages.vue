<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { http } from "../../api";
import StatusPill from "../../components/admin/StatusPill.vue";
import DataTable, { type DataTableColumn } from "../../components/admin/DataTable.vue";

const rows = ref<any[]>([]);
const loading = ref(true);
const status = ref("");

const columns: DataTableColumn[] = [
  { key: "name", label: "Package" },
  { key: "price_amount", label: "Price", align: "right", width: "140px" },
  { key: "status", label: "Status", width: "140px" },
  { key: "submitted_at", label: "Submitted", width: "120px" },
  { key: "updated_at", label: "Updated", width: "140px" },
];

async function load() {
  loading.value = true;
  try {
    const { data } = await http.get("/admin/packages", {
      params: status.value ? { status: status.value } : {},
    });
    rows.value = Array.isArray(data?.data) ? data.data : [];
  } catch (e) {
    console.error("Failed to load packages:", e);
    rows.value = [];
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
        <p class="eyebrow">Content</p>
        <h1>Packages</h1>
      </div>
      <RouterLink to="/admin/packages/new" class="btn btn--primary">New package</RouterLink>
    </div>

    <div class="filters">
      <select v-model="status" @change="load">
        <option value="">All statuses</option>
        <option value="draft">Draft</option>
        <option value="pending_review">Pending review</option>
        <option value="published">Published</option>
        <option value="rejected">Rejected</option>
        <option value="archived">Archived</option>
      </select>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading">
      <template #name="{ row }">
        <RouterLink :to="`/admin/packages/${row.id}`" class="link">{{ row.name }}</RouterLink>
      </template>
      <template #price_amount="{ row }">
        {{ row.price_amount ? `${row.currency ?? "KES"} ${Number(row.price_amount).toLocaleString()}` : "—" }}
      </template>
      <template #status="{ row }"><StatusPill :status="row.status" /></template>
      <template #submitted_at="{ row }">
        {{ row.submitted_at ? new Date(row.submitted_at).toLocaleDateString() : "—" }}
      </template>
      <template #updated_at="{ row }">
        {{ new Date(row.updated_at).toLocaleDateString() }}
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-6); }
.page-head h1 { margin: 0; }
.filters { margin-bottom: var(--sp-5); }
.filters select {
  padding: 0.6rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: #fff;
  font-size: var(--fs-sm);
}
.link { color: var(--color-gold); font-weight: 600; }
</style>