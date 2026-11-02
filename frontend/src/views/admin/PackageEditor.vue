<!-- PackageEditor -->
<script setup lang="ts">
import { onMounted, onBeforeUnmount, reactive, ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { http } from "../../api";
import { useAuthStore } from "../../stores";
import StatusPill from "../../components/admin/StatusPill.vue";
import Modal from "../../components/admin/Modal.vue";
import InventoryPicker, { type InventoryLine } from "../../components/admin/InventoryPicker.vue";
import { replacePackageInventory } from "../../api";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const packageId = route.params.id as string | undefined;
const isNew = !packageId || packageId === "new";

const categories = ref<any[]>([]);
const status = ref<string>("draft");
const saving = ref(false);
const error = ref<string | null>(null);
const showReject = ref(false);
const rejectReason = ref("");
const inventoryLines = ref<InventoryLine[]>([]);

const form = reactive({
  name: "",
  tagline: "",
  short_description: "",
  long_description: "",
  what_is_included: [] as string[],
  what_is_not_included: [] as string[],
  hero_image_url: "",
  gallery: [] as string[],
  category_id: "",
  price_amount: 0,
  price_note: "",
  currency: "KES",
  min_guests: 0,
  max_guests: 0,
  duration_hours: 0,
  availability_note: "",
  is_featured: false,
  seo_title: "",
  seo_description: "",
  rejection_reason: null as string | null, 
  
});
const selectedImage = ref<File | null>(null);
const imagePreview = ref<string | null>(null);

const displayedHeroImage = computed(
  () => imagePreview.value || form.hero_image_url
);

function onHeroImageChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  console.log("[Package Image] Input event triggered");
  console.log("[Package Image] Selected file:", file);

  if (!file) return;

  selectedImage.value = file;

  console.log("[Package Image] Stored in ref:", selectedImage.value);

  if (!file.type.startsWith("image/")) {
    error.value = "Please select a valid image.";
    input.value = "";
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    error.value = "Image must be smaller than 5 MB.";
    input.value = "";
    return;
  }

  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
  }

  selectedImage.value = file;
  imagePreview.value = URL.createObjectURL(file);
  error.value = null;
}

onBeforeUnmount(() => {
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
  }
});

const includedInput = ref("");
const notIncludedInput = ref("");



onMounted(async () => {
  try {
    const { data: cats } = await http.get("/admin/services/categories");
    categories.value = cats.data;

    if (!isNew) {
      const { data } = await http.get(`/admin/packages/${packageId}`);

      Object.assign(form, data.data);
      status.value = data.data.status;

      inventoryLines.value = (data.data.inventory_items ?? []).map(
        (row: any) => ({
          inventory_item_id: row.inventory_item_id,
          quantity: row.quantity,
          notes: row.notes ?? "",
        })
      );
    }
  } catch (e: any) {
    error.value = e?.message ?? "Failed to load package details.";
  }
});





const canSubmitForReview = computed(() =>
  ["draft", "rejected"].includes(status.value) && form.name.trim().length > 2
);

const canEdit = computed(() =>
  ["draft", "rejected", "published"].includes(status.value)
);

function addItem(list: "what_is_included" | "what_is_not_included", value: string) {
  const v = value.trim();
  if (!v) return;
  form[list] = [...form[list], v];
}

function removeItem(list: "what_is_included" | "what_is_not_included", i: number) {
  form[list] = form[list].filter((_, idx) => idx !== i);
}




// async function save() {
//   if (!canEdit.value) return;
//   saving.value = true;
//   error.value = null;
//   try {
//     if (isNew) {
//       const { data } = await http.post("/admin/packages", form, {
//         headers: { "Idempotency-Key": crypto.randomUUID() },
//       });
//       router.replace(`/admin/packages/${data.data.id}`);
//     } else {
//       await http.patch(`/admin/packages/${packageId}`, form);
//     }
//   } catch (e: any) {
//     error.value = e?.message ?? "Save failed.";
//   } finally {
//     saving.value = false;
//   }
// }

function normalizePayload() {
  return {
    name: form.name,
    tagline: form.tagline || null,
    short_description: form.short_description || null,
    long_description: form.long_description || null,
    what_is_included: form.what_is_included,
    what_is_not_included: form.what_is_not_included,
    hero_image_url: form.hero_image_url || null,
    gallery: form.gallery,
    category_id: form.category_id || null,
    price_amount: form.price_amount || null,
    price_note: form.price_note || null,
    currency: form.currency || "KES",
    min_guests: form.min_guests || null,
    max_guests: form.max_guests || null,
    duration_hours: form.duration_hours || null,
    availability_note: form.availability_note || null,
    is_featured: form.is_featured,
    seo_title: form.seo_title || null,
    seo_description: form.seo_description || null,
  };
}
async function uploadHeroImage(): Promise<string | null> {
  if (!selectedImage.value) {
    return form.hero_image_url || null;
  }

  const fd = new FormData();

  fd.append("file", selectedImage.value, selectedImage.value.name);

  const { data } = await http.post(
    "/admin/packages/upload-image",
    fd
  );

  const uploadedUrl = data?.data?.url;

  if (!uploadedUrl) {
    throw new Error("Image uploaded but no image URL was returned.");
  }

  // Keep the uploaded URL in the form.
  form.hero_image_url = uploadedUrl;
  selectedImage.value = null;

  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
    imagePreview.value = null;
  }

  return uploadedUrl;
}

async function save() {
  if (!canEdit.value || saving.value) return;

  if (!form.name.trim()) {
    error.value = "Package name is required.";
    return;
  }

  saving.value = true;
  error.value = null;

  try {
    // 1. Upload image if a new one was selected.
    await uploadHeroImage();

    // 2. Prepare package payload.
    const payload = normalizePayload();

    let savedId = packageId as string;

    // 3. Create or update package.
    if (isNew) {
      const { data } = await http.post("/admin/packages", payload, {
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });

      savedId = data.data.id;
    } else {
      await http.patch(`/admin/packages/${packageId}`, payload);
    }

    // 4. Save inventory associations.
    if (savedId) {
      await replacePackageInventory(savedId, inventoryLines.value);
    }

    // 5. Return to Packages listing.
    await router.replace("/admin/packages");

  } catch (e: any) {
    console.error("Package save failed:", e.response?.data ?? e);

    error.value =
      e.response?.data?.error?.message ??
      e?.message ??
      "Save failed.";
  } finally {
    saving.value = false;
  }
}


async function doTransition(action: string, body?: any) {
  try {
    await http.post(`/admin/packages/${packageId}/${action}`, body ?? {});
    showReject.value = false;
    if (!isNew) {
      const { data } = await http.get(`/admin/packages/${packageId}`);
      Object.assign(form, data.data);
      status.value = data.data.status;
    }
  } catch (e: any) {
    error.value = e?.message ?? "Action failed.";
  }
}


</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">{{ isNew ? "New" : "Edit" }}</p>
        <h1>{{ form.name || "Untitled package" }}</h1>
        <StatusPill :status="status" />
      </div>
      <div class="actions">
        <button v-if="canEdit" class="btn btn--outline" :disabled="saving" @click="save">Save</button>
        <button
          v-if="canSubmitForReview && !isNew"
          class="btn btn--primary"
          @click="doTransition('submit')"
        >Submit for review</button>
        <button
          v-if="status === 'pending_review' && auth.can('package.approve')"
          class="btn btn--primary"
          @click="doTransition('approve')"
        >Approve & publish</button>
        <button
          v-if="status === 'pending_review' && auth.can('package.approve')"
          class="btn btn--outline"
          @click="showReject = true"
        >Reject</button>
        <button
          v-if="status === 'published'"
          class="btn btn--outline"
          @click="doTransition('unpublish')"
        >Unpublish</button>
      </div>
    </div>

    <div v-if="status === 'rejected' && form.rejection_reason" class="rejection-banner">
      <strong>Rejected:</strong> {{ form.rejection_reason }}
    </div>

    <div class="grid">
      <div class="panel">
        <h3>Details</h3>
        <label class="field"><span>Name *</span><input v-model="form.name" /></label>
        <label class="field"><span>Tagline</span><input v-model="form.tagline" /></label>
        <label class="field"><span>Short description</span><input v-model="form.short_description" /></label>
        <label class="field"><span>Long description (HTML)</span><textarea v-model="form.long_description" rows="8" /></label>

        <h3>Inclusions</h3>
        <div class="chip-input">
          <input v-model="includedInput" placeholder="Add inclusion…" @keydown.enter.prevent="addItem('what_is_included', includedInput); includedInput = ''" />
          <button @click="addItem('what_is_included', includedInput); includedInput = ''">Add</button>
        </div>
        <ul class="chips">
          <li v-for="(item, i) in form.what_is_included" :key="i">
            {{ item }} <button @click="removeItem('what_is_included', i)">×</button>
          </li>
        </ul>

        <h3>Not included</h3>
        <div class="chip-input">
          <input v-model="notIncludedInput" placeholder="Add exclusion…" @keydown.enter.prevent="addItem('what_is_not_included', notIncludedInput); notIncludedInput = ''" />
          <button @click="addItem('what_is_not_included', notIncludedInput); notIncludedInput = ''">Add</button>
        </div>
        <ul class="chips">
          <li v-for="(item, i) in form.what_is_not_included" :key="i">
            {{ item }} <button @click="removeItem('what_is_not_included', i)">×</button>
          </li>
        </ul>
        <h3>Included inventory</h3>
        <InventoryPicker v-model="inventoryLines" />
      </div>

      <div class="panel">
        <h3>Pricing & logistics</h3>
        <div class="grid-2">
          <label class="field"><span>Price amount</span><input v-model.number="form.price_amount" type="number" /></label>
          <label class="field"><span>Currency</span><input v-model="form.currency" /></label>
        </div>
        <label class="field"><span>Price note</span><input v-model="form.price_note" placeholder="From / per person / for 50 guests" /></label>
        <div class="grid-2">
          <label class="field"><span>Min guests</span><input v-model.number="form.min_guests" type="number" /></label>
          <label class="field"><span>Max guests</span><input v-model.number="form.max_guests" type="number" /></label>
        </div>
        <label class="field"><span>Duration (hours)</span><input v-model.number="form.duration_hours" type="number" /></label>
        <label class="field"><span>Availability note</span><input v-model="form.availability_note" /></label>

        <h3>Category</h3>
        <label class="field">
          <select v-model="form.category_id">
            <option value="">No category</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>

        </label>
        

        <h3>Media & SEO</h3>


        <div class="field">
          <span>Hero image</span>

          <div v-if="displayedHeroImage" class="image-preview">
            <img :src="displayedHeroImage" alt="Package hero preview" />
          </div>

          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            @change="onHeroImageChange"
          />

          <small>
            Select an image for this package. Maximum size: 5 MB.
          </small>

          <small v-if="selectedImage">
            Selected: {{ selectedImage.name }}
          </small>
        </div>


        <label class="field"><span>SEO title</span><input v-model="form.seo_title" /></label>
        <label class="field"><span>SEO description</span><textarea v-model="form.seo_description" rows="2" /></label>
        <label class="check"><input type="checkbox" v-model="form.is_featured" /> <span>Feature on home</span></label>
      </div>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <Modal :open="showReject" title="Reject package" size="sm" @close="showReject = false">
      <label class="field"><span>Reason *</span><textarea v-model="rejectReason" rows="4" /></label>
      <template #footer>
        <button class="btn btn--outline" @click="showReject = false">Cancel</button>
        <button class="btn btn--primary" :disabled="!rejectReason.trim()" @click="doTransition('reject', { reason: rejectReason })">Reject</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: flex-end; gap: var(--sp-4); margin-bottom: var(--sp-6); flex-wrap: wrap; }
.page-head h1 { margin: var(--sp-2) 0; }
.actions { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.rejection-banner { padding: var(--sp-3); border-radius: var(--radius-md); background: #FEE2E2; color: #991B1B; margin-bottom: var(--sp-5); }
.grid { display: grid; grid-template-columns: 1.3fr 1fr; gap: var(--sp-5); align-items: start; }
@media (max-width: 1000px) { .grid { grid-template-columns: 1fr; } }
.panel { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); padding: var(--sp-5); }
.panel h3 { font-size: var(--fs-sm); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-gold); margin: var(--sp-5) 0 var(--sp-3); }
.panel h3:first-child { margin-top: 0; }
.field { display: grid; gap: var(--sp-2); margin-bottom: var(--sp-3); font-size: var(--fs-sm); color: var(--color-plum); font-weight: 500; }
.field input, .field textarea, .field select { padding: 0.55rem 0.85rem; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); background: #fff; font-size: var(--fs-sm); }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.chip-input { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.chip-input input { flex: 1; padding: 0.5rem 0.75rem; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); font-size: var(--fs-sm); }
.chip-input button { padding: 0 1rem; border-radius: var(--radius-md); background: var(--color-plum); color: var(--color-ivory); font-size: var(--fs-xs); }
.chips { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.chips li { display: inline-flex; gap: var(--sp-2); align-items: center; padding: 3px 10px; border-radius: var(--radius-pill); background: var(--color-ivory); font-size: var(--fs-xs); }
.chips li button { color: var(--color-coral); font-weight: 600; }
.check { display: flex; gap: var(--sp-2); align-items: center; font-size: var(--fs-sm); }
.err { color: #B91C1C; font-size: var(--fs-sm); }
.image-preview {
  width: 100%;
  max-width: 420px;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-radius: var(--radius-md);
  background: var(--color-ivory);
  border: 1px solid var(--color-border-soft);
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

</style>