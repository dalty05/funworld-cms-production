<script setup lang="ts">
import { reactive, ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { http, listPermissions } from "../../api";

const router = useRouter();
const perms = ref<any[]>([]);
const form = reactive({
  name: "",
  slug: "",
  description: "",
  permission_codes: [] as string[],
});
const saving = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  perms.value = await listPermissions();
});

// Group permissions by category for UI
const byCategory = computed(() => {
  const map: Record<string, any[]> = {};
  for (const p of perms.value) {
    const cat = p.category ?? "other";
    if (!map[cat]) map[cat] = [];
    map[cat].push(p);
  }
  return map;
});

// Auto-slugify the slug from name
function updateSlug() {
  if (form.slug) return;
  form.slug = form.name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80);
}

const canSave = computed(() =>
  form.name.trim().length > 1 &&
  /^[a-z0-9_-]+$/.test(form.slug)
);

async function save() {
  if (!canSave.value || saving.value) return;
  saving.value = true;
  error.value = null;
  try {
    const { data } = await http.post("/roles", {
      name: form.name,
      slug: form.slug,
      description: form.description || null,
      permission_codes: form.permission_codes,
    }, { headers: { "Idempotency-Key": crypto.randomUUID() } });
    router.push("/admin/roles");
  } catch (e: any) {
    error.value = e?.message ?? "Could not create role.";
  } finally { saving.value = false; }
}
</script>

<template>
  <div>
    <div class="page-head">
      <p class="eyebrow">New</p>
      <h1>Create role</h1>
    </div>

    <div class="grid">
      <div class="panel">
        <label class="field">
          <span>Name *</span>
          <input v-model="form.name" @input="updateSlug" placeholder="e.g. Event Coordinator" />
        </label>
        <label class="field">
          <span>Slug *</span>
          <input v-model="form.slug" placeholder="event_coordinator" />
        </label>
        <label class="field">
          <span>Description</span>
          <textarea v-model="form.description" rows="3" />
        </label>
      </div>

      <div class="panel">
        <h3>Permissions</h3>
        <div v-for="(list, cat) in byCategory" :key="cat" class="perm-group">
          <h4>{{ cat }}</h4>
          <label v-for="p in list" :key="p.id" class="check">
            <input type="checkbox" :value="p.code" v-model="form.permission_codes" />
            <span>{{ p.code }}</span>
          </label>
        </div>
      </div>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <div class="actions">
      <button class="btn btn--outline" @click="router.back()">Cancel</button>
      <button class="btn btn--primary" :disabled="!canSave || saving" @click="save">
        {{ saving ? "Creating…" : "Create role" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.page-head { margin-bottom: var(--sp-6); }
.page-head h1 { margin: var(--sp-2) 0; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-5); align-items: start; }
@media (max-width: 1000px) { .grid { grid-template-columns: 1fr; } }
.panel { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-5); }
.panel h3 { font-size: var(--fs-lg); margin: 0 0 var(--sp-4); }
.field { display: grid; gap: var(--sp-2); margin-bottom: var(--sp-4); font-size: var(--fs-sm); color: var(--color-plum); font-weight: 500; }
.field input, .field textarea { padding: 0.6rem 0.9rem; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); background: #fff; font-size: var(--fs-sm); }
.perm-group { margin-bottom: var(--sp-4); }
.perm-group h4 { font-size: var(--fs-xs); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-gold); margin: 0 0 var(--sp-2); }
.check { display: flex; gap: var(--sp-2); align-items: center; font-size: var(--fs-sm); padding: 2px 0; font-weight: normal; }
.actions { display: flex; gap: var(--sp-3); justify-content: flex-end; margin-top: var(--sp-5); }
.err { color: #B91C1C; font-size: var(--fs-sm); }
</style>