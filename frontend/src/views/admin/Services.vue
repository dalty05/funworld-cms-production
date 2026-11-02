<!-- /admin/services.vue -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { http } from "../../api";
import Modal from "../../components/admin/Modal.vue";

// ─── Types ──────────────────────────────────────────────────────
type ServiceCategory = {
  id: string;
  name: string;
  service_count: number;
  published_count: number;
};

type Service = {
  id: string;
  category_id: string;
  name: string;
  short_description?: string | null;
  long_description?: string | null;
  featured_image_url?: string | null;
  price_note?: string | null;
  sort_order?: number;
  is_published: boolean;
};

// ─── State ──────────────────────────────────────────────────────
const categories = ref<ServiceCategory[]>([]);
const services = ref<Service[]>([]);
const activeCategory = ref<string>("");
const error = ref<string | null>(null);

// Edit / create modal
const showServiceModal = ref(false);
const editing = ref<Service | null>(null);
const saving = ref(false);

// Action modal (for selected card)
const showActionModal = ref(false);
const selectedService = ref<Service | null>(null);
const actionBusy = ref(false);

// Image upload
const selectedImage = ref<File | null>(null);
const imagePreview = ref<string | null>(null);

const form = ref({
  category_id: "",
  name: "",
  short_description: "",
  long_description: "",
  featured_image_url: "",
  price_note: "",
  sort_order: 0,
});

// ─── Load ───────────────────────────────────────────────────────
async function load() {
  error.value = null;

  try {
    const [c, s] = await Promise.all([
      http.get("/admin/services/categories"),
      http.get("/admin/services"),
    ]);

    const categoryData = c.data?.data;
    const serviceData = s.data?.data;

    if (!Array.isArray(categoryData)) {
      throw new Error(
        "The categories API did not return an array in data.data."
      );
    }
    if (!Array.isArray(serviceData)) {
      throw new Error(
        "The services API did not return an array in data.data."
      );
    }

    categories.value = categoryData;
    services.value = serviceData;

    if (
      !categories.value.some(
        (category) => category.id === activeCategory.value
      )
    ) {
      activeCategory.value = categories.value[0]?.id ?? "";
    }

    console.log("[Admin Services] Categories:", categories.value);
    console.log("[Admin Services] Services:", services.value);
  } catch (e: unknown) {
    console.error("[Admin Services] Failed to load:", e);
    error.value =
      e instanceof Error
        ? e.message
        : "Failed to load services and categories.";
  }
}

onMounted(load);

// ─── Derived ────────────────────────────────────────────────────
const activeCategoryName = computed(
  () =>
    categories.value.find((c) => c.id === activeCategory.value)?.name ?? ""
);

const servicesByCategory = (catId: string) =>
  services.value.filter((s) => s.category_id === catId);

const visibleServices = computed(() =>
  servicesByCategory(activeCategory.value)
);

// ─── Image handling ─────────────────────────────────────────────
function clearImageSelection() {
  if (imagePreview.value?.startsWith("blob:")) {
    URL.revokeObjectURL(imagePreview.value);
  }
  selectedImage.value = null;
  imagePreview.value = null;
}

function onServiceImageChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  if (
    !["image/jpeg", "image/png", "image/webp", "image/gif"].includes(file.type)
  ) {
    error.value = "Please select a JPG, PNG, WEBP or GIF image.";
    input.value = "";
    return;
  }

  error.value = null;
  clearImageSelection();
  selectedImage.value = file;
  imagePreview.value = URL.createObjectURL(file);
}

// ─── Create / edit modal ────────────────────────────────────────
function openCreate(categoryId: string) {
  clearImageSelection();
  editing.value = null;
  form.value = {
    category_id: categoryId,
    name: "",
    short_description: "",
    long_description: "",
    featured_image_url: "",
    price_note: "",
    sort_order: 0,
  };
  error.value = null;
  showServiceModal.value = true;
}

function openEdit(s: Service) {
  clearImageSelection();
  editing.value = s;
  form.value = {
    category_id: s.category_id,
    name: s.name,
    short_description: s.short_description ?? "",
    long_description: s.long_description ?? "",
    featured_image_url: s.featured_image_url ?? "",
    price_note: s.price_note ?? "",
    sort_order: s.sort_order ?? 0,
  };
  imagePreview.value = s.featured_image_url || null;
  error.value = null;
  showActionModal.value = false;
  showServiceModal.value = true;
}

async function save() {
  error.value = null;

  if (!form.value.name.trim()) {
    error.value = "Service name is required.";
    return;
  }

  saving.value = true;

  try {
    // Step 1: Upload image if a new one was selected.
    let imageUrl = form.value.featured_image_url;

    if (selectedImage.value) {
      const fd = new FormData();
      fd.append("file", selectedImage.value, selectedImage.value.name);

      console.log("[Service Upload] FormData entries:");
      for (const [key, value] of fd.entries()) {
        console.log(
          key,
          value instanceof File
            ? { name: value.name, type: value.type, size: value.size }
            : value
        );
      }

      const uploadResponse = await http.post(
        "/admin/services/upload-image",
        fd,
        { headers: { "Content-Type": undefined } }
      );

      imageUrl = uploadResponse.data?.data?.url;
      if (!imageUrl) throw new Error("No image URL returned.");

      form.value.featured_image_url = imageUrl;
      clearImageSelection();
      imagePreview.value = imageUrl;
    }

    // Step 2: Save service details with the returned image URL.
    const payload = {
      ...form.value,
      name: form.value.name.trim(),
      featured_image_url: imageUrl || null,
    };

    if (editing.value) {
      await http.patch(`/admin/services/${editing.value.id}`, payload);
    } else {
      await http.post("/admin/services", payload, {
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
    }

    showServiceModal.value = false;
    clearImageSelection();
    await load();
  } catch (e: any) {
    console.error("[Admin Services] Save failed:", e);
    error.value =
      e?.response?.data?.message ??
      e?.message ??
      "Failed to save service.";
  } finally {
    saving.value = false;
  }
}

// ─── Card selection / action modal ──────────────────────────────
function selectService(s: Service) {
  selectedService.value = s;
  showActionModal.value = true;
}

function closeActionModal() {
  if (actionBusy.value) return;
  showActionModal.value = false;
  selectedService.value = null;
}

async function togglePublish(s: Service) {
  actionBusy.value = true;
  try {
    const url = s.is_published
      ? `/admin/services/${s.id}/unpublish`
      : `/admin/services/${s.id}/publish`;
    await http.post(url);
    await load();

    // Refresh selected service reference from new list
    const refreshed = services.value.find((x) => x.id === s.id);
    if (refreshed) selectedService.value = refreshed;
  } catch (e: any) {
    error.value =
      e?.response?.data?.message ?? e?.message ?? "Failed to update status.";
  } finally {
    actionBusy.value = false;
  }
}

async function remove(s: Service) {
  if (!confirm(`Delete "${s.name}"?`)) return;
  actionBusy.value = true;
  try {
    await http.delete(`/admin/services/${s.id}`);
    showActionModal.value = false;
    selectedService.value = null;
    await load();
  } catch (e: any) {
    error.value =
      e?.response?.data?.message ?? e?.message ?? "Failed to delete service.";
  } finally {
    actionBusy.value = false;
  }
}
</script>

<template>
  <div class="svc-admin">
    <!-- ─── Page head ─── -->
    <header class="page-head">
      <div>
        <p class="eyebrow">Content</p>
        <h1>Services</h1>
        <p class="subhead">
          Organise your offerings by category. Tap any card to reveal actions.
        </p>
      </div>
      <div class="page-head__actions">
        <button class="btn btn--outline" @click="load">Refresh</button>
        <button
          class="btn btn--primary"
          :disabled="!activeCategory"
          @click="openCreate(activeCategory)"
        >
          + Add service
        </button>
      </div>
    </header>

    <p v-if="error && !showServiceModal" class="err">{{ error }}</p>

    <!-- ─── Category tabs ─── -->
    <nav v-if="categories.length" class="tabs" role="tablist">
      <button
        v-for="c in categories"
        :key="c.id"
        :class="{ active: activeCategory === c.id }"
        role="tab"
        :aria-selected="activeCategory === c.id"
        @click="activeCategory = c.id"
      >
        {{ c.name }}
        <span class="count">{{ c.published_count }}/{{ c.service_count }}</span>
      </button>
    </nav>

    <!-- ─── Empty categories state ─── -->
    <div v-if="!categories.length && !error" class="empty-panel">
      <h3>No service categories configured</h3>
      <p>Create or seed service categories before adding services.</p>
      <button class="btn btn--outline" @click="load">Retry loading</button>
    </div>

    <!-- ─── Services grid ─── -->
    <section v-else-if="activeCategory" class="category-section">
      <div class="category-head">
        <h2>
          {{ activeCategoryName }}
          <span class="category-head__count">
            {{ visibleServices.length }}
            {{ visibleServices.length === 1 ? "service" : "services" }}
          </span>
        </h2>
      </div>

      <p v-if="!visibleServices.length" class="empty">
        No services yet in this category. Add your first service above.
      </p>

      <div v-else class="svc-grid">
        <article
          v-for="s in visibleServices"
          :key="s.id"
          class="svc-card"
          :class="{ 'svc-card--draft': !s.is_published }"
          tabindex="0"
          role="button"
          :aria-label="`Open actions for ${s.name}`"
          @click="selectService(s)"
          @keydown.enter.prevent="selectService(s)"
          @keydown.space.prevent="selectService(s)"
        >
          <div class="svc-card__media">
            <img
              v-if="s.featured_image_url"
              :src="s.featured_image_url"
              :alt="s.name"
              loading="lazy"
            />
            <div v-else class="svc-card__placeholder">
              <span>{{ s.name.charAt(0).toUpperCase() }}</span>
            </div>
            <span
              class="badge"
              :class="s.is_published ? 'badge--pub' : 'badge--draft'"
            >
              {{ s.is_published ? "Published" : "Draft" }}
            </span>
          </div>

          <div class="svc-card__body">
            <h3 class="svc-card__title">{{ s.name }}</h3>
            <p v-if="s.short_description" class="svc-card__desc">
              {{ s.short_description }}
            </p>
            <p v-else class="svc-card__desc svc-card__desc--muted">
              No short description
            </p>
            <p v-if="s.price_note" class="svc-card__price">
              {{ s.price_note }}
            </p>
          </div>
        </article>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         ACTION MODAL — appears when a card is selected
    ═══════════════════════════════════════════════════════════════ -->
    <Modal
      :open="showActionModal && !!selectedService"
      :title="selectedService?.name ?? 'Service actions'"
      size="sm"
      @close="closeActionModal"
    >
      <div v-if="selectedService" class="action-modal">
        <div v-if="selectedService.featured_image_url" class="action-modal__image">
          <img
            :src="selectedService.featured_image_url"
            :alt="selectedService.name"
          />
        </div>

        <p v-if="selectedService.short_description" class="action-modal__desc">
          {{ selectedService.short_description }}
        </p>

        <div class="action-modal__meta">
          <span
            class="badge"
            :class="
              selectedService.is_published ? 'badge--pub' : 'badge--draft'
            "
          >
            {{ selectedService.is_published ? "Published" : "Draft" }}
          </span>
          <span v-if="selectedService.price_note" class="action-modal__price">
            {{ selectedService.price_note }}
          </span>
        </div>
      </div>

      <template #footer>
        <div class="action-footer">
          <button
            class="btn btn--outline btn--sm danger"
            :disabled="actionBusy"
            @click="selectedService && remove(selectedService)"
          >
            Delete
          </button>

          <div class="action-footer__right">
            <button
              class="btn btn--outline btn--sm"
              :disabled="actionBusy"
              @click="closeActionModal"
            >
              Cancel
            </button>
            <button
              class="btn btn--outline btn--sm"
              :disabled="actionBusy || !selectedService"
              @click="selectedService && togglePublish(selectedService)"
            >
              {{
                selectedService?.is_published ? "Unpublish" : "Publish"
              }}
            </button>
            <button
              class="btn btn--primary btn--sm"
              :disabled="actionBusy || !selectedService"
              @click="selectedService && openEdit(selectedService)"
            >
              Edit
            </button>
          </div>
        </div>
      </template>
    </Modal>

    <!-- ═══════════════════════════════════════════════════════════
         CREATE / EDIT MODAL
    ═══════════════════════════════════════════════════════════════ -->
    <Modal
      :open="showServiceModal"
      :title="editing ? 'Edit service' : 'New service'"
      size="md"
      @close="showServiceModal = false"
    >
      <label class="field">
        <span>Name *</span>
        <input v-model="form.name" />
      </label>

      <label class="field">
        <span>Short description</span>
        <input v-model="form.short_description" />
      </label>

      <label class="field">
        <span>Long description</span>
        <textarea v-model="form.long_description" rows="4"></textarea>
      </label>

      <div class="field">
        <span>Featured image</span>

        <div v-if="imagePreview" class="service-image-preview">
          <img :src="imagePreview" alt="Service image preview" />
          <button
            type="button"
            class="btn btn--outline btn--sm"
            @click="clearImageSelection(); form.featured_image_url = ''"
          >
            Remove image
          </button>
        </div>

        <label class="service-image-upload">
          <strong>
            {{ selectedImage ? selectedImage.name : "Choose an image" }}
          </strong>
          <small>JPG, PNG, WEBP or GIF</small>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            @change="onServiceImageChange"
          />
        </label>
      </div>

      <label class="field">
        <span>Price note (optional)</span>
        <input v-model="form.price_note" placeholder="From KES 5,000/day" />
      </label>

      <label class="field">
        <span>Sort order</span>
        <input v-model.number="form.sort_order" type="number" />
      </label>

      <p v-if="error" class="err">{{ error }}</p>

      <template #footer>
        <button
          class="btn btn--outline"
          :disabled="saving"
          @click="showServiceModal = false; clearImageSelection()"
        >
          Cancel
        </button>
        <button
          class="btn btn--primary"
          :disabled="saving || !form.name.trim()"
          @click="save"
        >
          {{
            saving
              ? "Uploading & saving…"
              : editing
                ? "Save changes"
                : "Create service"
          }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   PAGE
═══════════════════════════════════════════════════════════════ */
.svc-admin { display: flex; flex-direction: column; gap: var(--sp-4, 1rem); }

.page-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--sp-4, 1rem);
  margin-bottom: var(--sp-3, 0.75rem);
}
.page-head h1 { margin: 0; }
.eyebrow {
  font-size: var(--fs-xs, 0.72rem);
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  margin: 0 0 0.35rem;
}
.subhead {
  font-size: var(--fs-sm, 0.85rem);
  color: var(--color-text-muted);
  margin: 0.4rem 0 0;
}
.page-head__actions { display: flex; gap: var(--sp-2, 0.5rem); flex-wrap: wrap; }

/* ═══════════════════════════════════════════════════════════════
   TABS
═══════════════════════════════════════════════════════════════ */
.tabs {
  display: flex;
  gap: var(--sp-2, 0.5rem);
  border-bottom: 1px solid var(--color-border-soft);
  margin-bottom: var(--sp-3, 0.75rem);
  flex-wrap: wrap;
}
.tabs button {
  padding: var(--sp-3, 0.75rem) var(--sp-4, 1rem);
  font-size: var(--fs-sm, 0.85rem);
  color: var(--color-text-muted);
  border-bottom: 2px solid transparent;
  background: none;
  cursor: pointer;
  transition: color 180ms ease, border-color 180ms ease;
}
.tabs button:hover { color: var(--color-plum); }
.tabs button.active {
  color: var(--color-plum);
  border-bottom-color: var(--color-gold);
  font-weight: 600;
}
.count {
  font-size: var(--fs-xs, 0.72rem);
  color: var(--color-gold);
  margin-left: 4px;
}

/* ═══════════════════════════════════════════════════════════════
   CATEGORY HEAD
═══════════════════════════════════════════════════════════════ */
.category-section { display: flex; flex-direction: column; gap: var(--sp-3, 0.75rem); }
.category-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--sp-3, 0.75rem);
}
.category-head h2 {
  font-size: var(--fs-lg, 1.1rem);
  margin: 0;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}
.category-head__count {
  font-size: var(--fs-xs, 0.72rem);
  font-weight: 500;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ═══════════════════════════════════════════════════════════════
   CARD GRID
═══════════════════════════════════════════════════════════════ */
.svc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--sp-4, 1rem);
}

.svc-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  text-align: left;
  padding: 0;
  transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
  outline: none;
}
.svc-card:hover,
.svc-card:focus-visible {
  transform: translateY(-3px);
  box-shadow: 0 10px 26px rgba(26, 20, 23, 0.1);
  border-color: var(--color-gold);
}
.svc-card--draft { opacity: 0.85; }

.svc-card__media {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: var(--color-ivory, #fcf9f4);
}
.svc-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 500ms ease;
}
.svc-card:hover .svc-card__media img { transform: scale(1.05); }

.svc-card__placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-ivory, #fcf9f4) 0%, rgba(196, 165, 130, 0.18) 100%);
}
.svc-card__placeholder span {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 2.5rem;
  font-weight: 300;
  color: var(--color-gold, #d4af6a);
}

.svc-card .badge {
  position: absolute;
  top: 0.65rem;
  left: 0.65rem;
}

.svc-card__body {
  padding: var(--sp-3, 0.75rem) var(--sp-4, 1rem) var(--sp-4, 1rem);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.svc-card__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.05rem;
  font-weight: 500;
  margin: 0;
  color: var(--color-plum, #2b0f2e);
  line-height: 1.25;
}
.svc-card__desc {
  font-size: var(--fs-xs, 0.75rem);
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.svc-card__desc--muted { font-style: italic; opacity: 0.7; }
.svc-card__price {
  font-size: var(--fs-xs, 0.72rem);
  color: var(--color-gold);
  font-weight: 600;
  margin: 0.25rem 0 0;
}

/* ═══════════════════════════════════════════════════════════════
   BADGES
═══════════════════════════════════════════════════════════════ */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-xs, 0.68rem);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  backdrop-filter: blur(4px);
}
.badge--pub { background: #d1fae5; color: #065f46; }
.badge--draft { background: #e5e7eb; color: #4b5563; }

/* ═══════════════════════════════════════════════════════════════
   ACTION MODAL
═══════════════════════════════════════════════════════════════ */
.action-modal { display: flex; flex-direction: column; gap: var(--sp-3, 0.75rem); }
.action-modal__image {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-ivory);
}
.action-modal__image img { width: 100%; height: 100%; object-fit: cover; }
.action-modal__desc {
  font-size: var(--fs-sm, 0.85rem);
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.5;
}
.action-modal__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-2, 0.5rem);
}
.action-modal__price {
  font-size: var(--fs-sm, 0.85rem);
  font-weight: 600;
  color: var(--color-gold);
}

.action-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-3, 0.75rem);
  flex-wrap: wrap;
}
.action-footer__right { display: flex; gap: var(--sp-2, 0.5rem); flex-wrap: wrap; }

/* ═══════════════════════════════════════════════════════════════
   FORM FIELDS
═══════════════════════════════════════════════════════════════ */
.field {
  display: grid;
  gap: var(--sp-2, 0.5rem);
  margin-bottom: var(--sp-3, 0.75rem);
  font-size: var(--fs-sm, 0.85rem);
  color: var(--color-plum);
  font-weight: 500;
}
.field input,
.field textarea {
  padding: 0.55rem 0.85rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: #fff;
  font-size: var(--fs-sm, 0.85rem);
  font-family: inherit;
  transition: border-color 160ms ease;
}
.field input:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--color-gold);
}

.err {
  color: #b91c1c;
  font-size: var(--fs-sm, 0.85rem);
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════════
   IMAGE UPLOAD
═══════════════════════════════════════════════════════════════ */
.service-image-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2, 0.5rem);
  padding: var(--sp-5, 1.25rem);
  border: 1px dashed var(--color-gold);
  border-radius: var(--radius-md);
  background: var(--color-ivory);
  cursor: pointer;
  text-align: center;
  transition: background 160ms ease;
}
.service-image-upload:hover { background: rgba(212, 175, 106, 0.06); }
.service-image-upload small {
  color: var(--color-text-muted);
  font-size: var(--fs-xs, 0.72rem);
}
.service-image-upload input { display: none; }

.service-image-preview {
  display: grid;
  gap: var(--sp-2, 0.5rem);
  margin-bottom: var(--sp-3, 0.75rem);
}
.service-image-preview img {
  width: 100%;
  max-height: 240px;
  object-fit: cover;
  border-radius: var(--radius-md);
}

/* ═══════════════════════════════════════════════════════════════
   EMPTY STATES
═══════════════════════════════════════════════════════════════ */
.empty-panel {
  background: #fff;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  padding: var(--sp-5, 1.25rem);
  text-align: center;
}
.empty-panel h3 { margin: 0 0 var(--sp-2, 0.5rem); }
.empty-panel p {
  color: var(--color-text-muted);
  font-size: var(--fs-sm, 0.85rem);
  margin: 0 0 var(--sp-4, 1rem);
}
.empty {
  color: var(--color-text-muted);
  font-size: var(--fs-sm, 0.85rem);
  padding: var(--sp-5, 1.25rem) 0;
  text-align: center;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════════ */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.55rem 1rem;
  font-size: var(--fs-sm, 0.85rem);
  font-weight: 600;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 160ms ease, color 160ms ease, border-color 160ms ease;
  font-family: inherit;
}
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn--sm { padding: 0.35rem 0.75rem; font-size: var(--fs-xs, 0.72rem); }
.btn--primary {
  background: var(--color-plum);
  color: #fff;
  border-color: var(--color-plum);
}
.btn--primary:hover:not(:disabled) { background: var(--color-charcoal, #1a1417); }
.btn--outline {
  background: transparent;
  color: var(--color-plum);
  border-color: var(--color-border-soft);
}
.btn--outline:hover:not(:disabled) { border-color: var(--color-plum); }
.danger {
  color: #b91c1c;
  border-color: #b91c1c;
}
.danger:hover:not(:disabled) {
  background: #b91c1c;
  color: #fff;
}

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════════ */
@media (max-width: 640px) {
  .page-head { align-items: flex-start; }
  .page-head__actions { width: 100%; }
  .page-head__actions .btn { flex: 1; }
  .svc-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.75rem; }
  .svc-card__title { font-size: 0.95rem; }
  .action-footer { flex-direction: column-reverse; align-items: stretch; }
  .action-footer__right { justify-content: flex-end; }
}

@media (prefers-reduced-motion: reduce) {
  .svc-card,
  .svc-card__media img,
  .tabs button,
  .btn { transition: none; }
  .svc-card:hover,
  .svc-card:focus-visible { transform: none; }
  .svc-card:hover .svc-card__media img { transform: none; }
}
</style>