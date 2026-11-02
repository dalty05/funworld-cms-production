<!-- /admin/inventory.vue -->
<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { http } from "../../api";
import Modal from "../../components/admin/Modal.vue";

// ─── Types ──────────────────────────────────────────────────────────
type Category = {
  id: string;
  slug: string;
  name: string;
  short_description?: string | null;
  icon?: string | null;
  sort_order?: number;
};

type InventoryItem = {
  id: string;
  category_id: string;
  name: string;
  short_description?: string | null;
  long_description?: string | null;
  quantity_owned?: number;
  quantity_available_note?: string | null;
  unit_price_hint?: number;
  unit?: string;
  currency?: string;
  featured_image_url?: string | null;
  sort_order?: number;
  is_published: boolean;
};

// ─── State ──────────────────────────────────────────────────────────
const categories = ref<Category[]>([]);
const items = ref<InventoryItem[]>([]);
const activeCategory = ref<string>("");
const search = ref("");

// Item modal
const showItemModal = ref(false);
const editingItem = ref<InventoryItem | null>(null);
const savingItem = ref(false);
const itemError = ref<string | null>(null);

// Category modal
const showCategoryModal = ref(false);
const editingCategory = ref<Category | null>(null);
const savingCategory = ref(false);
const categoryError = ref<string | null>(null);

// Delete confirm
const showDeleteCategory = ref(false);
const deletingCategory = ref<Category | null>(null);
const deleteError = ref<string | null>(null);
const deletingCategoryBusy = ref(false);

// Action modal (selected item)
const showActionModal = ref(false);
const selectedItem = ref<InventoryItem | null>(null);
const actionBusy = ref(false);

const itemForm = ref({
  category_id: "",
  name: "",
  short_description: "",
  long_description: "",
  quantity_owned: 0,
  quantity_available_note: "",
  unit_price_hint: 0,
  unit: "per piece",
  currency: "KES",
  featured_image_url: "",
  sort_order: 0,
});

const categoryForm = ref({
  slug: "",
  name: "",
  short_description: "",
  icon: "",
  sort_order: 0,
});

const selectedImage = ref<File | null>(null);
const imagePreview = ref<string | null>(null);

const displayedImage = computed(
  () => imagePreview.value || itemForm.value.featured_image_url
);

// ─── Image handling ─────────────────────────────────────────────────
function onImageChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    itemError.value = "Please select a valid image.";
    input.value = "";
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    itemError.value = "Image must be smaller than 5 MB.";
    input.value = "";
    return;
  }

  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value);
  selectedImage.value = file;
  imagePreview.value = URL.createObjectURL(file);
  itemError.value = null;
}

async function uploadInventoryImage(): Promise<void> {
  if (!selectedImage.value) return;

  const fd = new FormData();
  fd.append("file", selectedImage.value, selectedImage.value.name);

  const endpoint = editingItem.value
    ? "/admin/inventory/upload-image/edit"
    : "/admin/inventory/upload-image";

  const { data } = await http.post(endpoint, fd);

  const uploadedUrl = data?.data?.url;
  if (!uploadedUrl) {
    throw new Error("Image uploaded but no image URL was returned.");
  }

  itemForm.value.featured_image_url = uploadedUrl;
  selectedImage.value = null;

  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
    imagePreview.value = null;
  }
}

// ─── Load ───────────────────────────────────────────────────────────
async function load() {
  const [c, i] = await Promise.all([
    http.get("/admin/inventory/categories"),
    http.get("/admin/inventory"),
  ]);

  categories.value = c.data.data ?? [];
  items.value = i.data.data ?? [];

  const stillValid = categories.value.some((c) => c.id === activeCategory.value);
  if (!stillValid) activeCategory.value = categories.value[0]?.id ?? "";
}

onMounted(load);

// ─── Category CRUD ──────────────────────────────────────────────────
function openCreateCategory() {
  editingCategory.value = null;
  categoryError.value = null;
  categoryForm.value = {
    slug: "",
    name: "",
    short_description: "",
    icon: "",
    sort_order: 0,
  };
  showCategoryModal.value = true;
}

function openEditCategory(cat: Category) {
  editingCategory.value = cat;
  categoryError.value = null;
  categoryForm.value = {
    slug: cat.slug,
    name: cat.name,
    short_description: cat.short_description ?? "",
    icon: cat.icon ?? "",
    sort_order: cat.sort_order ?? 0,
  };
  showCategoryModal.value = true;
}

function autoSlugCategory() {
  if (categoryForm.value.slug) return;
  categoryForm.value.slug = categoryForm.value.name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
}

async function saveCategory() {
  categoryError.value = null;
  if (!categoryForm.value.name.trim()) {
    categoryError.value = "Name is required.";
    return;
  }
  if (!categoryForm.value.slug.trim()) {
    categoryError.value = "Slug is required.";
    return;
  }

  savingCategory.value = true;
  try {
    const payload = {
      ...categoryForm.value,
      short_description: categoryForm.value.short_description || null,
      icon: categoryForm.value.icon || null,
    };
    if (editingCategory.value) {
      await http.patch(
        `/admin/inventory/categories/${editingCategory.value.id}`,
        payload
      );
    } else {
      await http.post("/admin/inventory/categories", payload, {
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
    }
    showCategoryModal.value = false;
    await load();
  } catch (e: any) {
    const d = e?.details ?? e?.response?.data?.details;
    categoryError.value = d
      ? Object.entries(d)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
          .join(" · ")
      : e?.message ?? "Save failed.";
  } finally {
    savingCategory.value = false;
  }
}

function confirmDeleteCategory(cat: Category) {
  deletingCategory.value = cat;
  deleteError.value = null;
  showDeleteCategory.value = true;
}

async function doDeleteCategory() {
  if (!deletingCategory.value) return;
  deleteError.value = null;
  deletingCategoryBusy.value = true;

  const itemCount = items.value.filter(
    (i) => i.category_id === deletingCategory.value!.id
  ).length;

  if (itemCount > 0) {
    deleteError.value =
      `This category contains ${itemCount} item${itemCount === 1 ? "" : "s"}. ` +
      `Move or delete them first.`;
    deletingCategoryBusy.value = false;
    return;
  }

  try {
    await http.delete(
      `/admin/inventory/categories/${deletingCategory.value.id}`
    );
    showDeleteCategory.value = false;
    deletingCategory.value = null;
    await load();
  } catch (e: any) {
    const d = e?.details ?? e?.response?.data?.details;
    deleteError.value = d?.item_count
      ? `Cannot delete — ${d.item_count} item${d.item_count === 1 ? "" : "s"} still reference this category.`
      : e?.message ?? "Delete failed.";
  } finally {
    deletingCategoryBusy.value = false;
  }
}

// ─── Item CRUD ──────────────────────────────────────────────────────
function openCreateItem(categoryId?: string) {
  const selected =
    categoryId || activeCategory.value || categories.value[0]?.id || "";
  if (!selected) {
    itemError.value =
      "Please create an inventory category before adding an item.";
    return;
  }

  editingItem.value = null;
  itemError.value = null;
  selectedImage.value = null;
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
    imagePreview.value = null;
  }
  itemForm.value = {
    category_id: selected,
    name: "",
    short_description: "",
    long_description: "",
    quantity_owned: 0,
    quantity_available_note: "",
    unit_price_hint: 0,
    unit: "per piece",
    currency: "KES",
    featured_image_url: "",
    sort_order: 0,
  };
  showItemModal.value = true;
}

function openEditItem(item: InventoryItem) {
  editingItem.value = item;
  itemError.value = null;
  selectedImage.value = null;
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
    imagePreview.value = null;
  }
  itemForm.value = {
    category_id: item.category_id,
    name: item.name,
    short_description: item.short_description ?? "",
    long_description: item.long_description ?? "",
    quantity_owned: item.quantity_owned ?? 0,
    quantity_available_note: item.quantity_available_note ?? "",
    unit_price_hint: item.unit_price_hint ?? 0,
    unit: item.unit ?? "per piece",
    currency: item.currency ?? "KES",
    featured_image_url: item.featured_image_url ?? "",
    sort_order: item.sort_order ?? 0,
  };
  showActionModal.value = false;
  showItemModal.value = true;
}

async function saveItem() {
  savingItem.value = true;
  itemError.value = null;

  try {
    await uploadInventoryImage();

    const payload = { ...itemForm.value };

    if (editingItem.value) {
      await http.patch(`/admin/inventory/${editingItem.value.id}`, payload);
    } else {
      await http.post("/admin/inventory", payload, {
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
    }

    showItemModal.value = false;
    await load();
  } catch (err: any) {
    itemError.value =
      err.response?.data?.message ||
      err.message ||
      "Failed to save inventory item.";
  } finally {
    savingItem.value = false;
  }
}

// ─── Item selection / action modal ──────────────────────────────────
function selectItem(item: InventoryItem) {
  selectedItem.value = item;
  showActionModal.value = true;
}

function closeActionModal() {
  if (actionBusy.value) return;
  showActionModal.value = false;
  selectedItem.value = null;
}

async function togglePublish(item: InventoryItem) {
  actionBusy.value = true;
  try {
    const action = item.is_published ? "unpublish" : "publish";
    await http.post(`/admin/inventory/${item.id}/${action}`);
    await load();
    const refreshed = items.value.find((x) => x.id === item.id);
    if (refreshed) selectedItem.value = refreshed;
  } catch (e: any) {
    itemError.value =
      e?.response?.data?.message ?? e?.message ?? "Status update failed.";
  } finally {
    actionBusy.value = false;
  }
}

async function removeItem(item: InventoryItem) {
  if (!confirm(`Delete "${item.name}"?`)) return;
  actionBusy.value = true;
  try {
    await http.delete(`/admin/inventory/${item.id}`);
    showActionModal.value = false;
    selectedItem.value = null;
    await load();
  } finally {
    actionBusy.value = false;
  }
}

// ─── Derived ────────────────────────────────────────────────────────
function itemsFor(catId: string) {
  const q = search.value.toLowerCase().trim();
  return items.value
    .filter((i) => i.category_id === catId)
    .filter((i) => !q || i.name.toLowerCase().includes(q));
}

const activeCategoryName = computed(
  () => categories.value.find((c) => c.id === activeCategory.value)?.name ?? ""
);

const activeCategoryItemCount = computed(
  () => itemsFor(activeCategory.value).length
);

const activeCategoryObj = computed(
  () => categories.value.find((c) => c.id === activeCategory.value) ?? null
);

// Category-level header for selected categories (used in header)
const visibleItems = computed(() => itemsFor(activeCategory.value));
</script>

<template>
  <div class="inv-admin">
    <!-- ─── Page head ─── -->
    <header class="page-head">
      <div>
        <p class="eyebrow">Operations</p>
        <h1>Inventory</h1>
        <p class="subhead">
          Browse by category. Tap any item card to reveal its actions.
        </p>
      </div>
      <div class="head-actions">
        <button class="btn btn--outline" @click="openCreateCategory">
          Manage categories
        </button>
        <button class="btn btn--primary" @click="openCreateItem()">
          + New item
        </button>
      </div>
    </header>

    <!-- ─── Search ─── -->
    <div class="toolbar">
      <div class="search-wrap">
        <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.3-4.3" />
        </svg>
        <input
          v-model="search"
          type="search"
          class="search"
          placeholder="Search items across this category…"
        />
      </div>
    </div>

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
        <span class="count">{{ itemsFor(c.id).length }}</span>
      </button>
    </nav>

    <!-- ─── Empty categories ─── -->
    <div v-if="!categories.length" class="empty-state">
      <h3>No inventory categories yet</h3>
      <p>Categories organise your hire items. Create your first one to begin.</p>
      <button class="btn btn--primary" @click="openCreateCategory">
        Create your first category
      </button>
    </div>

    <!-- ─── Items section ─── -->
    <section v-else class="category-section">
      <header class="category-head">
        <div>
          <h2>
            {{ activeCategoryName }}
            <span class="category-head__count">
              {{ activeCategoryItemCount }}
              {{ activeCategoryItemCount === 1 ? "item" : "items" }}
            </span>
          </h2>
          <p v-if="activeCategoryObj?.short_description" class="category-head__desc">
            {{ activeCategoryObj.short_description }}
          </p>
        </div>
        <div class="category-head__actions">
          <button
            class="btn btn--outline btn--sm"
            @click="openEditCategory(activeCategoryObj!)"
          >
            Edit category
          </button>
          <button
            class="btn btn--outline btn--sm danger"
            @click="confirmDeleteCategory(activeCategoryObj!)"
          >
            Delete category
          </button>
          <button
            class="btn btn--primary btn--sm"
            @click="openCreateItem(activeCategory)"
          >
            + Add item
          </button>
        </div>
      </header>

      <p v-if="!visibleItems.length" class="empty">
        <template v-if="search.trim()">
          No items match "{{ search }}".
        </template>
        <template v-else>
          No items yet in this category. Add your first item above.
        </template>
      </p>

      <div v-else class="item-grid">
        <article
          v-for="item in visibleItems"
          :key="item.id"
          class="item-card"
          :class="{ 'item-card--draft': !item.is_published }"
          tabindex="0"
          role="button"
          :aria-label="`Open actions for ${item.name}`"
          @click="selectItem(item)"
          @keydown.enter.prevent="selectItem(item)"
          @keydown.space.prevent="selectItem(item)"
        >
          <div class="item-card__media">
            <img
              v-if="item.featured_image_url"
              :src="item.featured_image_url"
              :alt="item.name"
              loading="lazy"
            />
            <div v-else class="item-card__placeholder">
              <span>{{ item.name.charAt(0).toUpperCase() }}</span>
            </div>
            <span
              class="badge"
              :class="item.is_published ? 'badge--pub' : 'badge--draft'"
            >
              {{ item.is_published ? "Published" : "Draft" }}
            </span>
          </div>

          <div class="item-card__body">
            <h3 class="item-card__title">{{ item.name }}</h3>
            <p v-if="item.short_description" class="item-card__desc">
              {{ item.short_description }}
            </p>
            <p v-else class="item-card__desc item-card__desc--muted">
              No description
            </p>

            <div class="item-card__meta">
              <span class="pill pill--qty">
                Qty {{ item.quantity_owned ?? 0 }}
              </span>
              <span
                v-if="item.unit_price_hint"
                class="pill pill--price"
              >
                {{ item.currency || "KES" }}
                {{ item.unit_price_hint.toLocaleString() }}
                <template v-if="item.unit"> · {{ item.unit }}</template>
              </span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         ITEM ACTION MODAL
    ═══════════════════════════════════════════════════════════════ -->
    <Modal
      :open="showActionModal && !!selectedItem"
      :title="selectedItem?.name ?? 'Item actions'"
      size="sm"
      @close="closeActionModal"
    >
      <div v-if="selectedItem" class="action-modal">
        <div v-if="selectedItem.featured_image_url" class="action-modal__image">
          <img
            :src="selectedItem.featured_image_url"
            :alt="selectedItem.name"
          />
        </div>

        <p v-if="selectedItem.short_description" class="action-modal__desc">
          {{ selectedItem.short_description }}
        </p>

        <div class="action-modal__meta">
          <span
            class="badge"
            :class="
              selectedItem.is_published ? 'badge--pub' : 'badge--draft'
            "
          >
            {{ selectedItem.is_published ? "Published" : "Draft" }}
          </span>
          <span class="pill pill--qty">
            Qty {{ selectedItem.quantity_owned ?? 0 }}
          </span>
          <span v-if="selectedItem.unit_price_hint" class="pill pill--price">
            {{ selectedItem.currency || "KES" }}
            {{ selectedItem.unit_price_hint.toLocaleString() }}
            <template v-if="selectedItem.unit"> · {{ selectedItem.unit }}</template>
          </span>
        </div>

        <p v-if="selectedItem.quantity_available_note" class="action-modal__note">
          {{ selectedItem.quantity_available_note }}
        </p>
      </div>

      <template #footer>
        <div class="action-footer">
          <button
            class="btn btn--outline btn--sm danger"
            :disabled="actionBusy"
            @click="selectedItem && removeItem(selectedItem)"
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
              :disabled="actionBusy || !selectedItem"
              @click="selectedItem && togglePublish(selectedItem)"
            >
              {{ selectedItem?.is_published ? "Unpublish" : "Publish" }}
            </button>
            <button
              class="btn btn--primary btn--sm"
              :disabled="actionBusy || !selectedItem"
              @click="selectedItem && openEditItem(selectedItem)"
            >
              Edit
            </button>
          </div>
        </div>
      </template>
    </Modal>

    <!-- ═══════════════════════════════════════════════════════════
         ITEM CREATE / EDIT MODAL
    ═══════════════════════════════════════════════════════════════ -->
    <Modal
      :open="showItemModal"
      :title="editingItem ? 'Edit item' : 'New inventory item'"
      size="md"
      @close="showItemModal = false"
    >
      <label class="field">
        <span>Category *</span>
        <select v-model="itemForm.category_id" required>
          <option value="" disabled>Select a category</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </select>
      </label>

      <label class="field"><span>Name *</span><input v-model="itemForm.name" /></label>
      <label class="field">
        <span>Short description</span>
        <input v-model="itemForm.short_description" />
      </label>
      <label class="field">
        <span>Long description</span>
        <textarea v-model="itemForm.long_description" rows="3" />
      </label>

      <div class="grid-2">
        <label class="field">
          <span>Quantity owned</span>
          <input v-model.number="itemForm.quantity_owned" type="number" min="0" />
        </label>
        <label class="field">
          <span>Unit</span>
          <input v-model="itemForm.unit" placeholder="per piece, per day" />
        </label>
      </div>

      <div class="grid-2">
        <label class="field">
          <span>Unit price hint</span>
          <input v-model.number="itemForm.unit_price_hint" type="number" min="0" />
        </label>
        <label class="field">
          <span>Currency</span>
          <input v-model="itemForm.currency" />
        </label>
      </div>

      <label class="field">
        <span>Quantity note</span>
        <input
          v-model="itemForm.quantity_available_note"
          placeholder="Some units under maintenance"
        />
      </label>

      <div class="field">
        <span>Featured image</span>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          @change="onImageChange"
        />
        <div v-if="displayedImage" class="image-preview">
          <img :src="displayedImage" alt="Inventory item preview" />
        </div>
      </div>

      <label class="field">
        <span>Sort order</span>
        <input v-model.number="itemForm.sort_order" type="number" />
      </label>

      <p v-if="itemError" class="err">{{ itemError }}</p>

      <template #footer>
        <button class="btn btn--outline" @click="showItemModal = false">
          Cancel
        </button>
        <button
          class="btn btn--primary"
          :disabled="savingItem || !itemForm.name.trim()"
          @click="saveItem"
        >
          {{ savingItem ? "Saving…" : editingItem ? "Save" : "Create" }}
        </button>
      </template>
    </Modal>

    <!-- ═══════════════════════════════════════════════════════════
         CATEGORY MODAL
    ═══════════════════════════════════════════════════════════════ -->
    <Modal
      :open="showCategoryModal"
      :title="editingCategory ? 'Edit category' : 'New category'"
      size="sm"
      @close="showCategoryModal = false"
    >
      <label class="field">
        <span>Name *</span>
        <input
          v-model="categoryForm.name"
          @blur="autoSlugCategory"
          placeholder="Tents & Seating"
        />
      </label>
      <label class="field">
        <span>Slug *</span>
        <input v-model="categoryForm.slug" placeholder="tents-seating" />
      </label>
      <label class="field">
        <span>Short description</span>
        <input
          v-model="categoryForm.short_description"
          placeholder="Marquees, tables, chairs"
        />
      </label>

      <div class="grid-2">
        <label class="field">
          <span>Icon</span>
          <input v-model="categoryForm.icon" placeholder="tent" />
        </label>
        <label class="field">
          <span>Sort order</span>
          <input v-model.number="categoryForm.sort_order" type="number" />
        </label>
      </div>

      <p v-if="categoryError" class="err">{{ categoryError }}</p>

      <template #footer>
        <button class="btn btn--outline" @click="showCategoryModal = false">
          Cancel
        </button>
        <button
          class="btn btn--primary"
          :disabled="
            savingCategory ||
            !categoryForm.name.trim() ||
            !categoryForm.slug.trim()
          "
          @click="saveCategory"
        >
          {{ savingCategory ? "Saving…" : editingCategory ? "Save" : "Create" }}
        </button>
      </template>
    </Modal>

    <!-- ═══════════════════════════════════════════════════════════
         DELETE CATEGORY CONFIRM MODAL
    ═══════════════════════════════════════════════════════════════ -->
    <Modal
      :open="showDeleteCategory"
      title="Delete category"
      size="sm"
      @close="showDeleteCategory = false"
    >
      <p class="delete-warning">
        You are about to delete
        <strong>{{ deletingCategory?.name }}</strong>.
      </p>
      <p class="delete-note">
        A category can only be deleted if it contains no items. If you've just
        moved the items, refresh first.
      </p>
      <p v-if="deleteError" class="err">{{ deleteError }}</p>

      <template #footer>
        <button class="btn btn--outline" @click="showDeleteCategory = false">
          Keep category
        </button>
        <button
          class="btn btn--primary danger-btn"
          :disabled="deletingCategoryBusy"
          @click="doDeleteCategory"
        >
          {{ deletingCategoryBusy ? "Deleting…" : "Delete category" }}
        </button>
      </template>
    </Modal>
  </div>
</template>
<style scoped>
/* ═══════════════════════════════════════════════════════════════
   PAGE
═══════════════════════════════════════════════════════════════ */
.inv-admin { display: flex; flex-direction: column; gap: var(--sp-4, 1rem); }

.page-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--sp-4, 1rem);
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
.head-actions { display: flex; gap: var(--sp-2, 0.5rem); flex-wrap: wrap; }

/* ═══════════════════════════════════════════════════════════════
   SEARCH
═══════════════════════════════════════════════════════════════ */
.toolbar { display: flex; gap: var(--sp-3, 0.75rem); }
.search-wrap { position: relative; width: 100%; max-width: 420px; }
.search-icon {
  position: absolute;
  left: 0.85rem;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  stroke: var(--color-text-muted);
  stroke-width: 2;
  fill: none;
  pointer-events: none;
}
.search {
  width: 100%;
  padding: 0.65rem 1rem 0.65rem 2.3rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: #fff;
  font-size: var(--fs-sm, 0.85rem);
  transition: border-color 160ms ease;
}
.search:focus { outline: none; border-color: var(--color-gold); }

/* ═══════════════════════════════════════════════════════════════
   TABS
═══════════════════════════════════════════════════════════════ */
.tabs {
  display: flex;
  gap: var(--sp-2, 0.5rem);
  border-bottom: 1px solid var(--color-border-soft);
  margin-bottom: var(--sp-2, 0.5rem);
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
  align-items: flex-end;
  gap: var(--sp-3, 0.75rem);
  flex-wrap: wrap;
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
.category-head__desc {
  font-size: var(--fs-sm, 0.82rem);
  color: var(--color-text-muted);
  margin: 0.3rem 0 0;
  max-width: 60ch;
}
.category-head__actions { display: flex; gap: var(--sp-2, 0.5rem); flex-wrap: wrap; }

/* ═══════════════════════════════════════════════════════════════
   ITEM GRID — card-based
═══════════════════════════════════════════════════════════════ */
.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--sp-4, 1rem);
}

.item-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg, 14px);
  overflow: hidden;
  cursor: pointer;
  text-align: left;
  padding: 0;
  transition:
    transform 220ms ease,
    box-shadow 220ms ease,
    border-color 220ms ease;
  outline: none;
}
.item-card:hover,
.item-card:focus-visible {
  transform: translateY(-4px);
  box-shadow: 0 14px 34px rgba(26, 20, 23, 0.12);
  border-color: var(--color-gold);
}
.item-card:focus-visible {
  box-shadow:
    0 0 0 3px rgba(212, 175, 106, 0.35),
    0 14px 34px rgba(26, 20, 23, 0.12);
}
.item-card--draft { opacity: 0.9; }

.item-card__media {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--color-ivory, #fcf9f4);
}
.item-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 600ms ease;
}
.item-card:hover .item-card__media img { transform: scale(1.06); }

.item-card__placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    135deg,
    var(--color-ivory, #fcf9f4) 0%,
    rgba(196, 165, 130, 0.18) 100%
  );
}
.item-card__placeholder span {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 2.5rem;
  font-weight: 300;
  color: var(--color-gold, #d4af6a);
}

.item-card .badge {
  position: absolute;
  top: 0.65rem;
  left: 0.65rem;
  z-index: 1;
}

.item-card__body {
  padding: var(--sp-3, 0.85rem) var(--sp-4, 1rem) var(--sp-4, 1.1rem);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.item-card__title {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.05rem;
  font-weight: 500;
  margin: 0;
  color: var(--color-plum, #2b0f2e);
  line-height: 1.25;
}
.item-card__desc {
  font-size: var(--fs-sm, 0.82rem);
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-card__desc--muted {
  font-style: italic;
  color: var(--color-text-faint, #9a8f96);
}

.item-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.35rem;
}

/* ═══════════════════════════════════════════════════════════════
   PILLS & BADGES
═══════════════════════════════════════════════════════════════ */
.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.22rem 0.6rem;
  border-radius: 999px;
  font-size: var(--fs-xs, 0.72rem);
  font-weight: 500;
  line-height: 1.4;
  white-space: nowrap;
}
.pill--qty {
  background: rgba(43, 15, 46, 0.06);
  color: var(--color-plum, #2b0f2e);
}
.pill--price {
  background: rgba(212, 175, 106, 0.16);
  color: #7a5a1f;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: var(--fs-xs, 0.68rem);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  line-height: 1.4;
}
.badge--pub {
  background: rgba(61, 130, 88, 0.14);
  color: #2f6b47;
}
.badge--draft {
  background: rgba(150, 120, 40, 0.16);
  color: #8a6a1c;
}

/* ═══════════════════════════════════════════════════════════════
   EMPTY STATES
═══════════════════════════════════════════════════════════════ */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--sp-3, 0.75rem);
  padding: var(--sp-8, 3rem) var(--sp-4, 1rem);
  background: #fff;
  border: 1px dashed var(--color-border-soft);
  border-radius: var(--radius-lg, 14px);
  color: var(--color-text-muted);
}
.empty-state h3 {
  font-family: var(--font-display, "Fraunces", serif);
  font-size: 1.15rem;
  font-weight: 500;
  color: var(--color-plum, #2b0f2e);
  margin: 0;
}
.empty-state p {
  max-width: 42ch;
  font-size: var(--fs-sm, 0.85rem);
  margin: 0;
  line-height: 1.55;
}

.empty {
  font-size: var(--fs-sm, 0.85rem);
  color: var(--color-text-muted);
  padding: var(--sp-6, 2rem) var(--sp-4, 1rem);
  text-align: center;
  border: 1px dashed var(--color-border-soft);
  border-radius: var(--radius-lg, 14px);
  background: #fff;
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════════
   ACTION MODAL (item detail)
═══════════════════════════════════════════════════════════════ */
.action-modal {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3, 0.75rem);
}
.action-modal__image {
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-ivory, #fcf9f4);
}
.action-modal__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.action-modal__desc {
  font-size: var(--fs-sm, 0.85rem);
  color: var(--color-text-muted);
  line-height: 1.55;
  margin: 0;
}
.action-modal__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}
.action-modal__note {
  font-size: var(--fs-xs, 0.75rem);
  color: var(--color-text-muted);
  background: var(--color-ivory, #fcf9f4);
  border-left: 3px solid var(--color-gold);
  padding: 0.5rem 0.75rem;
  border-radius: 0 var(--radius-sm, 4px) var(--radius-sm, 4px) 0;
  margin: 0;
  line-height: 1.5;
}

.action-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-2, 0.5rem);
  width: 100%;
  flex-wrap: wrap;
}
.action-footer__right {
  display: flex;
  gap: var(--sp-2, 0.5rem);
  margin-left: auto;
}

/* ═══════════════════════════════════════════════════════════════
   FORMS (modal fields)
═══════════════════════════════════════════════════════════════ */
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: var(--sp-3, 0.75rem);
  font-size: var(--fs-sm, 0.85rem);
}
.field > span {
  font-weight: 500;
  color: var(--color-plum, #2b0f2e);
  font-size: var(--fs-xs, 0.78rem);
  letter-spacing: 0.02em;
}
.field input,
.field select,
.field textarea {
  width: 100%;
  padding: 0.55rem 0.75rem;
  border-radius: var(--radius-sm, 6px);
  border: 1px solid var(--color-border-soft);
  background: #fff;
  font-size: var(--fs-sm, 0.85rem);
  font-family: inherit;
  color: var(--color-text, #2b0f2e);
  transition: border-color 160ms ease, box-shadow 160ms ease;
}
.field textarea {
  resize: vertical;
  min-height: 3.5rem;
}
.field input:focus,
.field select:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--color-gold);
  box-shadow: 0 0 0 3px rgba(212, 175, 106, 0.18);
}
.field input[type="file"] {
  padding: 0.4rem 0.5rem;
  font-size: var(--fs-xs, 0.75rem);
  cursor: pointer;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-3, 0.75rem);
}
@media (max-width: 520px) {
  .grid-2 { grid-template-columns: 1fr; }
}

.image-preview {
  margin-top: 0.6rem;
  width: 100%;
  max-width: 220px;
  aspect-ratio: 4 / 3;
  border-radius: var(--radius-sm, 6px);
  overflow: hidden;
  border: 1px solid var(--color-border-soft);
  background: var(--color-ivory, #fcf9f4);
}
.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.err {
  margin: 0.25rem 0 0;
  padding: 0.5rem 0.7rem;
  font-size: var(--fs-xs, 0.78rem);
  color: #a12828;
  background: rgba(161, 40, 40, 0.08);
  border-radius: var(--radius-sm, 6px);
  line-height: 1.5;
}

/* ═══════════════════════════════════════════════════════════════
   DELETE CONFIRM
═══════════════════════════════════════════════════════════════ */
.delete-warning {
  font-size: var(--fs-sm, 0.9rem);
  color: var(--color-text, #2b0f2e);
  margin: 0 0 var(--sp-2, 0.5rem);
  line-height: 1.55;
}
.delete-warning strong {
  color: var(--color-plum, #2b0f2e);
  font-weight: 600;
}
.delete-note {
  font-size: var(--fs-xs, 0.78rem);
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.55;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTON VARIANTS
═══════════════════════════════════════════════════════════════ */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.6rem 1.1rem;
  border-radius: var(--radius-sm, 6px);
  font-size: var(--fs-sm, 0.85rem);
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 160ms ease;
}
.btn--sm {
  padding: 0.4rem 0.8rem;
  font-size: var(--fs-xs, 0.78rem);
}
.btn--outline {
  border: 1px solid var(--color-border-soft);
  background: #fff;
  color: var(--color-plum, #2b0f2e);
  transition: border-color 160ms ease, background 160ms ease;
}
.btn--outline:hover:not(:disabled) {
  border-color: var(--color-gold);
  background: var(--color-ivory, #fcf9f4);
}
.btn--outline.danger {
  color: #a12828;
  border-color: rgba(161, 40, 40, 0.25);
}
.btn--outline.danger:hover:not(:disabled) {
  background: rgba(161, 40, 40, 0.06);
  border-color: rgba(161, 40, 40, 0.5);
}
.btn--primary {
  background: var(--color-plum, #2b0f2e);
  color: #fff;
  border: 1px solid var(--color-plum, #2b0f2e);
  transition: background 160ms ease, transform 160ms ease;
}
.btn--primary:hover:not(:disabled) {
  background: #3d1a41;
}
.btn--primary.danger-btn {
  background: #a12828;
  border-color: #a12828;
}
.btn--primary.danger-btn:hover:not(:disabled) {
  background: #8a2020;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════════ */
@media (max-width: 640px) {
  .page-head {
    flex-direction: column;
    align-items: stretch;
  }
  .head-actions {
    justify-content: flex-start;
  }
  .search-wrap {
    max-width: 100%;
  }
  .category-head {
    flex-direction: column;
    align-items: stretch;
  }
  .category-head__actions {
    justify-content: flex-start;
  }
  .item-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: var(--sp-3, 0.75rem);
  }
  .item-card__body {
    padding: var(--sp-2, 0.55rem) var(--sp-3, 0.75rem) var(--sp-3, 0.75rem);
  }
  .action-footer {
    flex-direction: column-reverse;
    align-items: stretch;
  }
  .action-footer__right {
    margin-left: 0;
    justify-content: flex-end;
  }
  .action-footer > .btn {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .item-card,
  .item-card__media img,
  .btn,
  .tabs button,
  .field input,
  .field select,
  .field textarea {
    transition: none !important;
  }
  .item-card:hover,
  .item-card:focus-visible {
    transform: none;
  }
  .item-card:hover .item-card__media img {
    transform: none;
  }
}
</style>