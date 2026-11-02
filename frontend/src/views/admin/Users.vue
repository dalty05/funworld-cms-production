<!-- Users.vue -->

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { http } from "../../api";
import DataTable from "../../components/admin/DataTable.vue";

const router = useRouter();
const rows = ref<any[]>([]);
const loading = ref(true);

const columns = [
  { key: "full_name", label: "Name" },
  { key: "email", label: "Email" },
  { key: "roles", label: "Roles" },
  { key: "is_active", label: "Active", width: "80px" },
];

async function load() {
  loading.value = true;
  try {
    const { data } = await http.get("/users");
    rows.value = data.data;
  } finally {
    loading.value = false;
  }
}

function openUser(row: any) {
  if (!row?.id) return;
  router.push(`/admin/users/${row.id}`);
}

onMounted(load);
</script>





<template>
  <div>
    <div class="page-head">
      <div>
      <p class="eyebrow">Access</p>
      <h1>Users</h1>
      </div>
            <RouterLink to="/admin/users/new" class="btn btn--primary">New user</RouterLink>  
    </div>

    <div class="filters">

    </div>
    <!-- <DataTable :columns="columns" :rows="rows" :loading="loading">
      <template #roles="{ row }">{{ (row.roles ?? []).join(", ") }}</template>
      <template #is_active="{ row }">{{ row.is_active ? "Yes" : "No" }}</template>
    </DataTable> -->


    <DataTable
  :columns="columns"
  :rows="rows"
  :loading="loading"
  :row-link="(row) => `/admin/users/${row.id}`"
>
  <template #roles="{ row }">
    {{ (row.roles ?? []).join(", ") }}
  </template>

  <template #is_active="{ row }">
    {{ row.is_active ? "Yes" : "No" }}
  </template>
</DataTable>
    


  </div>
</template>
<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: flex-end; }

.page-head { margin-bottom: var(--sp-6); }
.page-head h1 { margin: 0; }
</style>