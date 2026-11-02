<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { http } from "../../api";
import Modal from "../../components/admin/Modal.vue";

// ─── State ──────────────────────────────────────────────────────────
const albums = ref<any[]>([]);
const images = ref<any[]>([]);
const categories = ref<any[]>([]);

const activeAlbumId = ref<string>(""); // "" = all images
const showAlbumModal = ref(false);
const editingAlbum = ref<any | null>(null);
const savingAlbum = ref(false);
const albumError = ref<string | null>(null);
const albumForm = ref({
  name: "",
  slug: "",
  description: "",
  category_id: "",
  sort_order: 0,
});

const showUploadModal = ref(false);
const uploadFile = ref<File | null>(null);
const uploadPreview = ref<string | null>(null);
const uploadAltText = ref("");
const uploadCaption = ref("");
const uploadAlbumId = ref("");
const uploadCategoryId = ref("");
const uploading = ref(false);
const uploadError = ref<string | null>(null);

const showEditImage = ref(false);
const editingImage = ref<any | null>(null);
const imageForm = ref({
  alt_text: "",
  caption: "",
  album_id: "",
  category_id: "",
  is_featured: false,
});
const savingImage = ref(false);

const showDeleteAlbum = ref(false);
const deletingAlbum = ref<any | null>(null);
const deleteAlbumError = ref<string | null>(null);
const deletingAlbumBusy = ref(false);

// ─── Load ───────────────────────────────────────────────────────────
async function load() {
  const [albRes, imgRes, catRes] = await Promise.all([
    http.get("/admin/gallery/albums"),
    http.get("/admin/gallery/images"),
    http.get("/admin/services/categories"),
  ]);
  albums.value = albRes.data.data ?? [];
  images.value = imgRes.data.data ?? [];
  categories.value = catRes.data.data ?? [];
}
onMounted(load);

const filteredImages = computed(() => {
  if (!activeAlbumId.value) return images.value;
  return images.value.filter((i) => i.album_id === activeAlbumId.value);
});

const activeAlbum = computed(() =>
  albums.value.find((a) => a.id === activeAlbumId.value) ?? null
);

// ─── Album CRUD ─────────────────────────────────────────────────────
function openCreateAlbum() {
  editingAlbum.value = null;
  albumError.value = null;
  albumForm.value = { name: "", slug: "", description: "", category_id: "", sort_order: 0 };
  showAlbumModal.value = true;
}

function openEditAlbum(album: any) {
  editingAlbum.value = album;
  albumError.value = null;
  albumForm.value = {
    name: album.name,
    slug: album.slug,
    description: album.description ?? "",
    category_id: album.category_id ?? "",
    sort_order: album.sort_order ?? 0,
  };
  showAlbumModal.value = true;
}

function autoSlugAlbum() {
  if (albumForm.value.slug) return;
  albumForm.value.slug = albumForm.value.name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

async function saveAlbum() {
  albumError.value = null;
  if (!albumForm.value.name.trim()) {
    albumError.value = "Name is required.";
    return;
  }
  savingAlbum.value = true;
  try {
    const payload: any = {
      name: albumForm.value.name,
      description: albumForm.value.description || null,
      category_id: albumForm.value.category_id || null,
      sort_order: albumForm.value.sort_order,
    };
    if (editingAlbum.value) {
      await http.patch(`/admin/gallery/albums/${editingAlbum.value.id}`, payload);
    } else {
      payload.slug = albumForm.value.slug || null;
      await http.post("/admin/gallery/albums", payload, {
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
    }
    showAlbumModal.value = false;
    await load();
  } catch (e: any) {
    albumError.value = e?.message ?? "Save failed.";
  } finally {
    savingAlbum.value = false;
  }
}

async function toggleAlbumPublish(album: any) {
  const action = album.is_published ? "unpublish" : "publish";
  await http.post(`/admin/gallery/albums/${album.id}/${action}`);
  await load();
}

function confirmDeleteAlbum(album: any) {
  deletingAlbum.value = album;
  deleteAlbumError.value = null;
  showDeleteAlbum.value = true;
}

async function doDeleteAlbum() {
  if (!deletingAlbum.value) return;
  deleteAlbumError.value = null;
  deletingAlbumBusy.value = true;
  try {
    await http.delete(`/admin/gallery/albums/${deletingAlbum.value.id}`);
    showDeleteAlbum.value = false;
    deletingAlbum.value = null;
    if (activeAlbumId.value === deletingAlbum.value?.id) activeAlbumId.value = "";
    await load();
  } catch (e: any) {
    deleteAlbumError.value = e?.message ?? "Delete failed.";
  } finally {
    deletingAlbumBusy.value = false;
  }
}

// ─── Upload ─────────────────────────────────────────────────────────
function openUpload() {
  uploadFile.value = null;
  uploadPreview.value = null;
  uploadAltText.value = "";
  uploadCaption.value = "";
  uploadAlbumId.value = activeAlbumId.value;
  uploadCategoryId.value = activeAlbum.value?.category_id ?? "";
  uploadError.value = null;
  showUploadModal.value = true;
}

function onFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (!files || !files.length) return;
  const file = files[0];
  uploadFile.value = file;
  uploadPreview.value = URL.createObjectURL(file);
}

async function doUpload() {
  if (!uploadFile.value) {
    uploadError.value = "Please select a file.";
    return;
  }
  if (!uploadAltText.value.trim()) {
    uploadError.value = "Alt text is required.";
    return;
  }
  uploading.value = true;
  uploadError.value = null;

  try {
    const fd = new FormData();
    fd.append("file", uploadFile.value);
    fd.append("alt_text", uploadAltText.value.trim());
    if (uploadCaption.value.trim()) fd.append("caption", uploadCaption.value.trim());
    if (uploadAlbumId.value) fd.append("album_id", uploadAlbumId.value);
    if (uploadCategoryId.value) fd.append("category_id", uploadCategoryId.value);

    await http.post("/admin/gallery/images", fd, {
      headers: {
        "Content-Type": "multipart/form-data",
        "Idempotency-Key": crypto.randomUUID(),
      },
    });
    showUploadModal.value = false;
    await load();
  } catch (e: any) {
    uploadError.value = e?.message ?? "Upload failed.";
  } finally {
    uploading.value = false;
  }
}

// ─── Image actions ──────────────────────────────────────────────────
function openEditImage(img: any) {
  editingImage.value = img;
  imageForm.value = {
    alt_text: img.alt_text,
    caption: img.caption ?? "",
    album_id: img.album_id ?? "",
    category_id: img.category_id ?? "",
    is_featured: img.is_featured,
  };
  showEditImage.value = true;
}

async function saveImage() {
  if (!editingImage.value) return;
  savingImage.value = true;
  try {
    await http.patch(`/admin/gallery/images/${editingImage.value.id}`, {
      alt_text: imageForm.value.alt_text,
      caption: imageForm.value.caption || null,
      album_id: imageForm.value.album_id || null,
      category_id: imageForm.value.category_id || null,
      is_featured: imageForm.value.is_featured,
    });
    showEditImage.value = false;
    await load();
  } finally {
    savingImage.value = false;
  }
}

async function toggleImagePublish(img: any) {
  const action = img.is_published ? "unpublish" : "publish";
  await http.post(`/admin/gallery/images/${img.id}/${action}`);
  await load();
}

async function deleteImage(img: any) {
  if (!confirm(`Delete this image? This cannot be undone.`)) return;
  await http.delete(`/admin/gallery/images/${img.id}`);
  await load();
}
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">Content</p>
        <h1>Gallery</h1>
      </div>
      <div class="head-actions">
        <button class="btn btn--outline" @click="openCreateAlbum">New album</button>
        <button class="btn btn--primary" @click="openUpload">Upload image</button>
      </div>
    </div>

    <div class="layout">
      <!-- Albums sidebar -->
      <aside class="albums">
        <button
          class="album"
          :class="{ active: activeAlbumId === '' }"
          @click="activeAlbumId = ''"
        >
          <span>All images</span>
          <span class="album__count">{{ images.length }}</span>
        </button>

        <button
          v-for="a in albums"
          :key="a.id"
          class="album"
          :class="{ active: activeAlbumId === a.id }"
          @click="activeAlbumId = a.id"
        >
          <span>
            {{ a.name }}
            <span v-if="a.is_published" class="dot dot--pub" title="Published" />
            <span v-else class="dot dot--draft" title="Draft" />
          </span>
          <span class="album__count">{{ a.image_count }}</span>
        </button>

        <p v-if="!albums.length" class="albums__empty">
          No albums yet. Create one to group photos.
        </p>
      </aside>

      <!-- Images panel -->
      <main class="panel">
        <div class="panel__head">
          <div>
            <h3>{{ activeAlbum?.name ?? "All images" }}</h3>
            <p class="panel__meta">
              {{ filteredImages.length }} image{{ filteredImages.length === 1 ? "" : "s" }}
              <template v-if="activeAlbum">
                · <span v-if="activeAlbum.is_published">Published</span>
                <span v-else>Draft</span>
              </template>
            </p>
          </div>
          <div v-if="activeAlbum" class="panel__actions">
            <button class="btn btn--outline btn--sm" @click="openEditAlbum(activeAlbum)">Edit album</button>
            <button class="btn btn--outline btn--sm" @click="toggleAlbumPublish(activeAlbum)">
              {{ activeAlbum.is_published ? "Unpublish" : "Publish" }}
            </button>
            <button class="btn btn--outline btn--sm danger" @click="confirmDeleteAlbum(activeAlbum)">Delete album</button>
          </div>
        </div>

        <div v-if="!filteredImages.length" class="empty">
          <p>No images yet.</p>
          <button class="btn btn--primary" @click="openUpload">Upload the first one</button>
        </div>

        <div v-else class="images">
          <div v-for="img in filteredImages" :key="img.id" class="image">
            <div class="image__media">
              <img :src="img.thumb_url" :alt="img.alt_text" loading="lazy" />
              <span v-if="!img.is_published" class="image__badge image__badge--draft">Draft</span>
              <span v-if="img.is_featured" class="image__badge image__badge--featured">Featured</span>
            </div>
            <div class="image__meta">
              <p class="image__alt">{{ img.alt_text }}</p>
              <p v-if="img.caption" class="image__caption">{{ img.caption }}</p>
            </div>
            <div class="image__actions">
              <button class="btn btn--outline btn--xs" @click="openEditImage(img)">Edit</button>
              <button class="btn btn--outline btn--xs" @click="toggleImagePublish(img)">
                {{ img.is_published ? "Unpublish" : "Publish" }}
              </button>
              <button class="btn btn--outline btn--xs danger" @click="deleteImage(img)">Delete</button>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- Album modal -->
    <Modal
      :open="showAlbumModal"
      :title="editingAlbum ? 'Edit album' : 'New album'"
      size="sm"
      @close="showAlbumModal = false"
    >
      <label class="field">
        <span>Name *</span>
        <input v-model="albumForm.name" @blur="autoSlugAlbum" placeholder="Molly & Brian's Wedding" />
      </label>

      <label v-if="!editingAlbum" class="field">
        <span>Slug</span>
        <input v-model="albumForm.slug" placeholder="molly-brian-wedding" />
      </label>

      <label class="field">
        <span>Description</span>
        <textarea v-model="albumForm.description" rows="3" />
      </label>

      <label class="field">
        <span>Category</span>
        <select v-model="albumForm.category_id">
          <option value="">No category</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </label>

      <label class="field">
        <span>Sort order</span>
        <input v-model.number="albumForm.sort_order" type="number" />
      </label>

      <p v-if="albumError" class="err">{{ albumError }}</p>

      <template #footer>
        <button class="btn btn--outline" @click="showAlbumModal = false">Cancel</button>
        <button class="btn btn--primary" :disabled="savingAlbum || !albumForm.name.trim()" @click="saveAlbum">
          {{ savingAlbum ? "Saving…" : (editingAlbum ? "Save" : "Create") }}
        </button>
      </template>
    </Modal>

    <!-- Upload modal -->
    <Modal :open="showUploadModal" title="Upload image" size="md" @close="showUploadModal = false">
      <label class="field">
        <span>File *</span>
        <input type="file" accept="image/*" @change="onFileChange" />
      </label>

      <div v-if="uploadPreview" class="upload-preview">
        <img :src="uploadPreview" alt="Preview" />
      </div>

      <label class="field">
        <span>Alt text * (describe the image for accessibility)</span>
        <input v-model="uploadAltText" placeholder="Bride and groom at the altar with white flowers" />
      </label>

      <label class="field">
        <span>Caption (optional, shown in lightbox)</span>
        <input v-model="uploadCaption" placeholder="Molly & Brian — 14 Nov 2026" />
      </label>

      <label class="field">
        <span>Album</span>
        <select v-model="uploadAlbumId">
          <option value="">No album</option>
          <option v-for="a in albums" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </label>

      <label class="field">
        <span>Category</span>
        <select v-model="uploadCategoryId">
          <option value="">No category</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </label>

      <p v-if="uploadError" class="err">{{ uploadError }}</p>

      <template #footer>
        <button class="btn btn--outline" @click="showUploadModal = false">Cancel</button>
        <button class="btn btn--primary" :disabled="uploading || !uploadFile || !uploadAltText.trim()" @click="doUpload">
          {{ uploading ? "Uploading…" : "Upload" }}
        </button>
      </template>
    </Modal>

    <!-- Edit image modal -->
    <Modal :open="showEditImage" title="Edit image" size="sm" @close="showEditImage = false">
      <div v-if="editingImage" class="edit-preview">
        <img :src="editingImage.thumb_url" :alt="editingImage.alt_text" />
      </div>

      <label class="field">
        <span>Alt text *</span>
        <input v-model="imageForm.alt_text" />
      </label>

      <label class="field">
        <span>Caption</span>
        <input v-model="imageForm.caption" />
      </label>

      <label class="field">
        <span>Album</span>
        <select v-model="imageForm.album_id">
          <option value="">No album</option>
          <option v-for="a in albums" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </label>

      <label class="field">
        <span>Category</span>
        <select v-model="imageForm.category_id">
          <option value="">No category</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </label>

      <label class="check">
        <input type="checkbox" v-model="imageForm.is_featured" />
        <span>Featured</span>
      </label>

      <template #footer>
        <button class="btn btn--outline" @click="showEditImage = false">Cancel</button>
        <button class="btn btn--primary" :disabled="savingImage || !imageForm.alt_text.trim()" @click="saveImage">
          {{ savingImage ? "Saving…" : "Save" }}
        </button>
      </template>
    </Modal>

    <!-- Delete album confirm -->
    <Modal :open="showDeleteAlbum" title="Delete album" size="sm" @close="showDeleteAlbum = false">
      <p class="delete-warning">
        Delete <strong>{{ deletingAlbum?.name }}</strong>?
      </p>
      <p class="delete-note">
        This will also delete all {{ deletingAlbum?.image_count ?? 0 }} image{{ (deletingAlbum?.image_count ?? 0) === 1 ? "" : "s" }} inside it.
        This cannot be undone.
      </p>
      <p v-if="deleteAlbumError" class="err">{{ deleteAlbumError }}</p>
      <template #footer>
        <button class="btn btn--outline" @click="showDeleteAlbum = false">Keep album</button>
        <button class="btn btn--primary danger-btn" :disabled="deletingAlbumBusy" @click="doDeleteAlbum">
          {{ deletingAlbumBusy ? "Deleting…" : "Delete album" }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-4);
  flex-wrap: wrap;
  margin-bottom: var(--sp-5);
}
.page-head h1 { margin: 0; }
.head-actions { display: flex; gap: var(--sp-2); }

.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: var(--sp-5);
  align-items: start;
}
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }

.albums {
  background: #fff;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  padding: var(--sp-3);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}
.album {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-3);
  border-radius: var(--radius-md);
  font-size: var(--fs-sm);
  color: var(--color-plum);
  text-align: left;
  transition: background var(--dur-fast);
}
.album:hover { background: rgba(201, 164, 92, 0.06); }
.album.active { background: rgba(201, 164, 92, 0.14); font-weight: 600; }
.album__count {
  font-size: var(--fs-xs);
  color: var(--color-text-muted);
  background: var(--color-ivory);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}
.dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-left: 6px;
}
.dot--pub { background: #10B981; }
.dot--draft { background: #9CA3AF; }
.albums__empty {
  font-size: var(--fs-xs);
  color: var(--color-text-muted);
  padding: var(--sp-3);
  text-align: center;
}

.panel {
  background: #fff;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  padding: var(--sp-5);
}
.panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--sp-3);
  flex-wrap: wrap;
  margin-bottom: var(--sp-5);
}
.panel__head h3 { margin: 0 0 var(--sp-1); font-size: var(--fs-lg); }
.panel__meta { font-size: var(--fs-sm); color: var(--color-text-muted); margin: 0; }
.panel__actions { display: flex; gap: var(--sp-2); flex-wrap: wrap; }

.images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--sp-4);
}
.image {
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-ivory);
  display: flex;
  flex-direction: column;
}
.image__media {
  aspect-ratio: 4 / 3;
  overflow: hidden;
  position: relative;
}
.image__media img { width: 100%; height: 100%; object-fit: cover; }
.image__badge {
  position: absolute;
  top: var(--sp-2);
  left: var(--sp-2);
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}
.image__badge--draft { background: rgba(255,255,255,0.9); color: #6B7280; }
.image__badge--featured { background: var(--color-gold); color: var(--color-plum); left: auto; right: var(--sp-2); }

.image__meta { padding: var(--sp-3); flex: 1; }
.image__alt { font-size: var(--fs-xs); color: var(--color-plum); margin: 0 0 4px; }
.image__caption { font-size: var(--fs-xs); color: var(--color-text-muted); margin: 0; }

.image__actions {
  display: flex;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3) var(--sp-3);
  flex-wrap: wrap;
}

.btn--xs { padding: 0.3rem 0.6rem; font-size: 11px; }
.btn--sm { padding: 0.35rem 0.7rem; font-size: var(--fs-xs); }
.danger { color: #B91C1C; border-color: #B91C1C; }
.danger-btn { background: #B91C1C; color: #fff; border-color: #B91C1C; }
.danger-btn:hover { background: #991B1B; }

.empty {
  text-align: center;
  padding: var(--sp-8) var(--sp-5);
  color: var(--color-text-muted);
}
.empty p { margin-bottom: var(--sp-4); }

.field {
  display: grid;
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
  font-size: var(--fs-sm);
  color: var(--color-plum);
  font-weight: 500;
}
.field input, .field textarea, .field select {
  padding: 0.55rem 0.85rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: #fff;
  font-size: var(--fs-sm);
}
.field input[type="file"] { padding: var(--sp-2); }
.field input:focus, .field textarea:focus, .field select:focus {
  outline: none;
  border-color: var(--color-gold);
}

.upload-preview,
.edit-preview {
  margin: var(--sp-3) 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  max-height: 260px;
}
.upload-preview img,
.edit-preview img { width: 100%; height: auto; display: block; }

.check { display: flex; gap: var(--sp-2); align-items: center; font-size: var(--fs-sm); }

.err { color: #B91C1C; font-size: var(--fs-sm); white-space: pre-wrap; }

.delete-warning { font-size: var(--fs-base); color: var(--color-plum); margin: 0 0 var(--sp-3); }
.delete-note { font-size: var(--fs-sm); color: var(--color-text-muted); margin: 0 0 var(--sp-3); }
</style>