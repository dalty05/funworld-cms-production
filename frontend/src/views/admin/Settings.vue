<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { http } from "../../api";

const settings = ref<any[]>([]);
const selectedKey = ref<string>("");
const selected = ref<any | null>(null);
const draft = ref("");
const saving = ref(false);
const error = ref<string | null>(null);
const success = ref<string | null>(null);

const categories = [
  { value: "company", label: "Company" },
  { value: "policy", label: "Policies" },
  { value: "quote_terms", label: "Quote defaults" },
  { value: "invoice_terms", label: "Invoice defaults" },
];

const groupedSettings = computed(() => {
  const out: Record<string, any[]> = {};
  for (const s of settings.value) {
    (out[s.category] ||= []).push(s);
  }
  return out;
});

async function load() {
  const { data } = await http.get("/admin/settings");
  settings.value = data.data;
  if (!selectedKey.value && settings.value.length) {
    selectSetting(settings.value[0].key);
  }
}

async function selectSetting(key: string) {
  selectedKey.value = key;
  selected.value = null;
  error.value = null;
  success.value = null;
  const { data } = await http.get(`/admin/settings/${key}`);
  selected.value = data.data;
  draft.value = data.data.value_text ?? "";
}

async function save() {
  if (!selected.value) return;
  saving.value = true;
  error.value = null;
  success.value = null;
  try {
    await http.patch(`/admin/settings/${selected.value.key}`, {
      value_text: draft.value,
    });
    await selectSetting(selected.value.key);
    success.value = "Saved.";
  } catch (e: any) {
    error.value = e?.message ?? "Save failed.";
  } finally {
    saving.value = false;
  }
}

function isDirty() {
  return selected.value && draft.value !== (selected.value.value_text ?? "");
}

onMounted(load);
</script>

<template>
  <div class="settings">
    <div class="page-head">
      <div>
        <p class="eyebrow">Admin</p>
        <h1>Settings</h1>
      </div>
    </div>

    <div class="settings__grid">
      <aside class="settings__nav">
        <div v-for="cat in categories" :key="cat.value">
          <h4>{{ cat.label }}</h4>
          <ul>
            <li
              v-for="s in (groupedSettings[cat.value] ?? [])"
              :key="s.key"
              :class="{ active: s.key === selectedKey }"
              @click="selectSetting(s.key)"
            >
              {{ s.label }}
            </li>
          </ul>
        </div>
      </aside>

      <section v-if="selected" class="settings__editor">
        <div class="editor__head">
          <div>
            <h2>{{ selected.label }}</h2>
            <p class="editor__meta">
              key: <code>{{ selected.key }}</code>
              · v{{ selected.version }}
              · updated {{ new Date(selected.updated_at).toLocaleString() }}
            </p>
            <p v-if="selected.description" class="editor__desc">{{ selected.description }}</p>
          </div>
          <label class="toggle">
            <input type="checkbox" :checked="selected.is_published"
                   @change="http.patch(`/admin/settings/${selected.key}`, { is_published: !selected.is_published }).then(() => load())" />
            <span>Published</span>
          </label>
        </div>

        <textarea
          v-model="draft"
          class="editor__textarea"
          rows="24"
          placeholder="Markdown or plain text."
        />

        <p v-if="selected.category === 'policy'" class="editor__hint">
          Published at <code>/api/v1/settings/policies/{{ selected.key }}</code>
        </p>

        <p v-if="error" class="err">{{ error }}</p>
        <p v-if="success" class="ok">{{ success }}</p>

        <div class="actions">
          <button class="btn btn--outline" :disabled="!isDirty()" @click="draft = selected.value_text ?? ''">
            Reset
          </button>
          <button class="btn btn--primary" :disabled="!isDirty() || saving" @click="save">
            {{ saving ? "Saving…" : "Save" }}
          </button>
        </div>
      </section>

      <p v-else class="empty">Loading…</p>
    </div>
  </div>
</template>

<style scoped>
.page-head { margin-bottom: var(--sp-5); }
.page-head h1 { margin: 0; }
.settings__grid { display: grid; grid-template-columns: 240px 1fr; gap: var(--sp-5); align-items: start; }
@media (max-width: 900px) { .settings__grid { grid-template-columns: 1fr; } }

.settings__nav { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-4); }
.settings__nav h4 { font-size: var(--fs-xs); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-gold); margin: var(--sp-4) 0 var(--sp-2); }
.settings__nav h4:first-child { margin-top: 0; }
.settings__nav ul { list-style: none; padding: 0; margin: 0; }
.settings__nav li { padding: var(--sp-2) var(--sp-3); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--fs-sm); }
.settings__nav li:hover { background: rgba(201, 164, 92, 0.06); }
.settings__nav li.active { background: rgba(201, 164, 92, 0.14); color: var(--color-plum); font-weight: 500; }

.settings__editor { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-5); display: grid; gap: var(--sp-4); }
.editor__head { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--sp-4); flex-wrap: wrap; }
.editor__head h2 { margin: 0 0 var(--sp-1); }
.editor__meta { font-size: var(--fs-xs); color: var(--color-text-muted); margin: 0; }
.editor__desc { font-size: var(--fs-sm); color: var(--color-text-muted); margin: var(--sp-2) 0 0; }
.editor__textarea { width: 100%; padding: var(--sp-3); border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); font-family: "SF Mono", Menlo, monospace; font-size: var(--fs-sm); line-height: 1.5; }
.editor__textarea:focus { outline: none; border-color: var(--color-gold); }
.editor__hint { font-size: var(--fs-xs); color: var(--color-text-muted); margin: 0; }
.toggle { display: flex; gap: var(--sp-2); align-items: center; font-size: var(--fs-sm); }
.actions { display: flex; justify-content: flex-end; gap: var(--sp-2); }
.err { color: #B91C1C; font-size: var(--fs-sm); margin: 0; }
.ok { color: #059669; font-size: var(--fs-sm); margin: 0; }
.empty { padding: var(--sp-6); color: var(--color-text-muted); }
</style>