<!-- /views/admin/UserDetail.vue -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { http, listRoles } from "../../api";
import Modal from "../../components/admin/Modal.vue";

const route = useRoute();
const user = ref<any>(null);
const roles = ref<any[]>([]);
const showAssign = ref(false);
const selectedSlug = ref("");
const error = ref<string | null>(null);

async function load() {
  const [u, r] = await Promise.all([
    http.get(`/users/${route.params.id}`),
    listRoles(),
  ]);
  user.value = u.data.data;
  roles.value = r;
}

onMounted(load);

async function assignRole() {
  if (!selectedSlug.value) return;
  error.value = null;
  try {
    await http.post(
      `/users/${user.value.id}/roles`,
      { role_slug: selectedSlug.value, scope_type: "global" },
      { headers: { "Idempotency-Key": crypto.randomUUID() } }
    );
    showAssign.value = false;
    selectedSlug.value = "";
    await load();
  } catch (e: any) {
    error.value = e?.message ?? "Failed";
  }
}

async function revokeRole(assignmentId: string) {
  await http.delete(`/users/${user.value.id}/roles/${assignmentId}`);
  await load();
}
</script>

<template>
  <div v-if="user">
    <div class="head">
      <div>
        <p class="eyebrow">User</p>
        <h1>{{ user.full_name }}</h1>
        <p class="meta">{{ user.email }} · {{ user.phone ?? "—" }}</p>
      </div>
      <button class="btn btn--primary" @click="showAssign = true">Assign role</button>
    </div>

    <div class="panel">
      <h3>Roles</h3>
      <ul v-if="user.roles?.length" class="roles">
        <li v-for="r in user.roles" :key="r.id">
          <div>
            <strong>{{ r.name }}</strong>
            <span class="scope">{{ r.scope_type }}</span>
          </div>
          <button class="btn btn--outline btn--sm" @click="revokeRole(r.id)">Revoke</button>
        </li>
      </ul>
      <p v-else class="empty">No roles assigned.</p>
    </div>

    <Modal :open="showAssign" title="Assign role" size="sm" @close="showAssign = false">
      <label class="field">
        <span>Role</span>
        <select v-model="selectedSlug">
          <option value="">Select…</option>
          <option v-for="r in roles" :key="r.id" :value="r.slug">{{ r.name }}</option>
        </select>
      </label>
      <p v-if="error" class="err">{{ error }}</p>
      <template #footer>
        <button class="btn btn--outline" @click="showAssign = false">Cancel</button>
        <button class="btn btn--primary" :disabled="!selectedSlug" @click="assignRole">Assign</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--sp-6); }
.head h1 { margin: var(--sp-2) 0; }
.meta { color: var(--color-text-muted); }
.panel { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-5); }
.panel h3 { font-size: var(--fs-lg); margin: 0 0 var(--sp-3); }
.roles { list-style: none; padding: 0; margin: 0; }
.roles li { display: flex; justify-content: space-between; align-items: center; padding: var(--sp-3) 0; border-bottom: 1px solid var(--color-border-soft); }
.roles li:last-child { border-bottom: none; }
.scope { font-size: var(--fs-xs); color: var(--color-text-muted); margin-left: var(--sp-2); }
.empty { color: var(--color-text-muted); font-size: var(--fs-sm); }
.field { display: grid; gap: var(--sp-2); font-size: var(--fs-sm); color: var(--color-plum); font-weight: 500; }
.field select { padding: 0.6rem 0.9rem; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); background: #fff; }
.err { color: #B91C1C; font-size: var(--fs-sm); }
.btn--sm { padding: 0.4rem 0.8rem; font-size: var(--fs-xs); }
</style>