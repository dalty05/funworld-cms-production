<!-- Roles.vue -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { http } from "../../api";

const roles = ref<any[]>([]);
const permissions = ref<any[]>([]);
const selected = ref<any | null>(null);

async function load() {
  const [r, p] = await Promise.all([
    http.get("/roles"),
    http.get("/permissions"),
  ]);
  roles.value = r.data.data;
  permissions.value = p.data.data;
}

function selectRole(r: any) { selected.value = { ...r, permission_codes: r.permissions.map((x: any) => x.code) }; }

async function save() {
  if (!selected.value) return;
  await http.patch(`/roles/${selected.value.id}`, {
    name: selected.value.name,
    description: selected.value.description,
    permission_codes: selected.value.permission_codes,
  });
  await load();
}

onMounted(load);
</script>
<template>
  <div>
    <div class="page-head">
      <div>
      <p class="eyebrow">Access</p>
      <h1>Roles</h1>
    </div>
    <RouterLink to="/admin/roles/new" class="btn btn--primary">New role</RouterLink>

    </div>
    <div class="panel">
      <p class="lead">Roles define what users can do in the system. Assign roles to users to grant them access.</p> 
    </div>

    <div class="grid">
      <div class="panel">
        <ul class="roles">
          <li v-for="r in roles" :key="r.id" :class="{ active: selected?.id === r.id }" @click="selectRole(r)">
            <strong>{{ r.name }}</strong>
            <span>{{ r.permissions?.length }} perms</span>
          </li>
        </ul>
      </div>

      <div v-if="selected" class="panel">
        <h3>{{ selected.name }}</h3>
        <label><span>Description</span><input v-model="selected.description" /></label>
        <div class="perms">
          <label v-for="p in permissions" :key="p.id" class="perm">
            <input type="checkbox" :value="p.code" v-model="selected.permission_codes" />
            <span>{{ p.code }}</span>
          </label>
        </div>
        <button class="btn btn--primary" @click="save">Save</button>
      </div>
    </div>
  </div>
</template>
<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: flex-end; }

.page-head { margin-bottom: var(--sp-6); }
.page-head h1 { margin: 0; }
.grid { display: grid; grid-template-columns: 300px 1fr; gap: var(--sp-5); }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
.panel { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-5); align-items: center; }
.roles { list-style: none; padding: 0; margin: 0; }
.roles li { padding: var(--sp-3); border-radius: var(--radius-md); cursor: pointer; display: flex; justify-content: space-between; }
.roles li:hover { background: rgba(201, 164, 92, 0.08); }
.roles li.active { background: rgba(201, 164, 92, 0.14); }
.perms { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--sp-2); max-height: 400px; overflow: auto; margin: var(--sp-4) 0; }
.perm { display: flex; gap: var(--sp-2); align-items: center; font-size: var(--fs-sm); }
.panel input { padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--color-border-soft); width: 100%; }
</style>