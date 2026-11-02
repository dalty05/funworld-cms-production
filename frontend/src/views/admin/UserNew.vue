<script setup lang="ts">
import { reactive, ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { http, listRoles } from "../../api";

const router = useRouter();
const roles = ref<any[]>([]);
const form = reactive({
  full_name: "",
  email: "",
  phone: "",
  password: "",
  is_active: true,
  role_slugs: [] as string[],
});
const saving = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  roles.value = await listRoles();
});

const passwordIsStrong = computed(() =>
  form.password.length >= 10 &&
  new TextEncoder().encode(form.password).length <= 72 &&
  /[A-Z]/.test(form.password) &&
  /[a-z]/.test(form.password) &&
  /\d/.test(form.password) &&
  /[^A-Za-z0-9]/.test(form.password) &&
  !["password", "password123", "password1", "12345678", "123456789", "qwerty123", "admin123", "letmein", "welcome1", "funworld123"].includes(form.password.toLowerCase())
);

const canSave = computed(() =>
  form.full_name.trim().length > 1 &&
  form.email.trim().length > 3 &&
  passwordIsStrong.value
);

async function save() {
  if (!canSave.value || saving.value) return;
  saving.value = true;
  error.value = null;
  try {
    const { data } = await http.post("/users", {
      full_name: form.full_name,
      email: form.email,
      phone: form.phone || undefined,
      password: form.password,
      is_active: form.is_active,
      role_slugs: form.role_slugs,
    }, { headers: { "Idempotency-Key": crypto.randomUUID() } });
    router.push(`/admin/users/${data.data.id}`);
  } catch (e: any) {
    error.value = e?.message ?? "Could not create user.";
  } finally { saving.value = false; }
}
</script>

<template>
  <div>
    <div class="page-head">
      <p class="eyebrow">New</p>
      <h1>Create user</h1>
    </div>

    <div class="panel">
      <label class="field">
        <span>Full name *</span>
        <input v-model="form.full_name" />
      </label>

      <div class="grid-2">
        <label class="field">
          <span>Email *</span>
          <input v-model="form.email" type="email" />
        </label>
        <label class="field">
          <span>Phone</span>
          <input v-model="form.phone" />
        </label>
      </div>

      <label class="field">
        <span>Password *</span>
        <input v-model="form.password" type="password" />
        <small class="policy">At least 10 characters, uppercase, lowercase, number and symbol; max 72 UTF-8 bytes.</small>
      </label>

      <label class="field">
        <span>Roles</span>
        <div class="check-grid">
          <label v-for="r in roles" :key="r.id" class="check">
            <input type="checkbox" :value="r.slug" v-model="form.role_slugs" />
            <span>{{ r.name }}</span>
          </label>
        </div>
      </label>

      <label class="field check">
        <input type="checkbox" v-model="form.is_active" />
        <span>Active</span>
      </label>

      <p v-if="error" class="err">{{ error }}</p>

      <div class="actions">
        <button class="btn btn--outline" @click="router.back()">Cancel</button>
        <button class="btn btn--primary" :disabled="!canSave || saving" @click="save">
          {{ saving ? "Creating…" : "Create user" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head { margin-bottom: var(--sp-6); }
.page-head h1 { margin: var(--sp-2) 0; }
.panel { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-6); max-width: 720px; }
.field { display: grid; gap: var(--sp-2); margin-bottom: var(--sp-4); font-size: var(--fs-sm); color: var(--color-plum); font-weight: 500; }
.field input { padding: 0.6rem 0.9rem; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); background: #fff; font-size: var(--fs-sm); }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-4); }
.check-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); }
.check { display: flex; gap: var(--sp-2); align-items: center; font-weight: normal; }
.actions { display: flex; gap: var(--sp-3); justify-content: flex-end; }
.err { color: #B91C1C; font-size: var(--fs-sm); }
.policy { color: var(--color-text-muted); font-size: var(--fs-xs); font-weight: 400; }
</style>