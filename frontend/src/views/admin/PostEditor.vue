<!-- PostEditor.vue -->
<script setup lang="ts">
import { onMounted, reactive, ref, onBeforeUnmount , computed, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { http } from "../../api";

const route = useRoute();
const router = useRouter();
const postId = computed(() => typeof route.params.id === "string" ? route.params.id : undefined);
const isNew = computed(() => !postId.value || postId.value === "new");
const post = reactive<any>({
  title: "",
  body_markdown: "",
  excerpt: "",
  featured_image_url: "",
  featured_image_alt: "",
  seo_title: "",
  seo_description: "",
  category_slugs: [],
  tag_slugs: [],
  featured: false,
});
const hasValidTitle = computed(() => !isNew || post.title.trim().length >= 3);

const status = ref<string>("draft");
const slug = ref<string>("");
const saving = ref(false);
const loadingPost = ref(false);
const message = ref<string | null>(null);
const categories = ref<any[]>([]);
const tags = ref<any[]>([]);
const suggestions = ref<any[]>([]);

const previewHtml = computed(() => post.body_markdown); // backend renders; UI shows markdown here
const selectedImage = ref<File | null>(null);
const imagePreview = ref<string | null>(null);

const displayedImage = computed(
  () => imagePreview.value || post.featured_image_url
);
async function load() {
  const [c, t] = await Promise.all([
    http.get("/admin/blog/categories"),
    http.get("/admin/blog/tags"),
  ]);
  categories.value = c.data.data;
  tags.value = t.data.data;

  if (!isNew.value && postId.value) {
    loadingPost.value = true;
    try {
      const { data } = await http.get(`/admin/blog/posts/${postId.value}`);
      Object.assign(post, data.data);
      status.value = data.data.status;
      slug.value = data.data.slug;
      await nextTick();
    } finally {
      loadingPost.value = false;
    }
  }
}
function onFeaturedImageChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (!file) return;

  if (!["image/jpeg", "image/png", "image/webp", "image/gif"].includes(file.type)) {
    message.value = "Choose a JPG, PNG, WebP or GIF image.";
    input.value = "";
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    message.value = "Image must be smaller than 5 MB.";
    input.value = "";
    return;
  }

  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
  }

  selectedImage.value = file;
  imagePreview.value = URL.createObjectURL(file);
  message.value = null;
}

async function uploadFeaturedImage() {
  if (!selectedImage.value) return;

  const fd = new FormData();
  fd.append("file", selectedImage.value, selectedImage.value.name);

  const endpoint = isNew.value
    ? "/admin/blog/upload-image"
    : "/admin/blog/upload-image/edit";

  const { data } = await http.post(endpoint, fd);

  const uploadedUrl = data?.data?.url;

  if (!uploadedUrl) {
    throw new Error("Image uploaded but no image URL was returned.");
  }

  post.featured_image_url = uploadedUrl;

  selectedImage.value = null;

  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
    imagePreview.value = null;
  }
}

async function save() {

  if (saving.value) return;
  if (!hasValidTitle.value) {
    message.value = "Enter a title with at least 3 characters.";
    return;
  }
  saving.value = true;
  message.value = null;
  try {
    await uploadFeaturedImage();
    if (isNew.value) {
      const { data } = await http.post("/admin/blog/posts", {
        title: post.title,
        body_markdown: post.body_markdown,
        excerpt: post.excerpt,
        featured_image_url: post.featured_image_url,
        featured_image_alt: post.featured_image_alt,
        seo_title: post.seo_title,
        seo_description: post.seo_description,
        canonical_url: post.canonical_url,
        og_image_url: post.og_image_url,
        featured: post.featured,
        category_slugs: post.category_slugs,
        tag_slugs: post.tag_slugs,
      });
      await router.replace(`/admin/blog/posts/${data.data.id}`);
    } else {
      await http.patch(`/admin/blog/posts/${postId.value}`, {
        title: post.title,
        body_markdown: post.body_markdown,
        excerpt: post.excerpt,
        featured_image_url: post.featured_image_url,
        featured_image_alt: post.featured_image_alt,
        seo_title: post.seo_title,
        seo_description: post.seo_description,
        category_slugs: post.category_slugs,
        tag_slugs: post.tag_slugs,
        featured: post.featured,
      });
    }
    message.value = "Saved.";
  } catch (e: any) {
    const details = e?.details;
    const detailText = details
      ? Object.entries(details).map(([field, messages]) =>
          `${field}: ${Array.isArray(messages) ? messages.join(", ") : String(messages)}`
        ).join("; ")
      : "";
    message.value = [e?.message ?? "Save failed.", detailText].filter(Boolean).join(" ");
  } finally {
    saving.value = false;
  }
}

async function transition(action: string, body?: any) {
  if (!postId.value || isNew.value) return;
  const { data } = await http.post(`/admin/blog/posts/${postId.value}/${action}`, body ?? {});
  status.value = data.data.status ?? status.value;
  message.value = `Done: ${action}`;
}

// Auto-save every 20s when dirty
let dirtyTimer: any;
watch(post, () => {
  if (isNew.value || loadingPost.value) return;
  clearTimeout(dirtyTimer);
  dirtyTimer = setTimeout(() => save(), 20000);
}, { deep: true });
watch(selectedImage, (file) => {
  if (!file || isNew.value || loadingPost.value) return;

  clearTimeout(dirtyTimer);

  dirtyTimer = setTimeout(() => {
    save();
  }, 20000);
});
watch(() => route.params.id, () => load());

// Link suggestions
watch(() => post.body_markdown, async (v) => {
  if (!v || v.length < 40) { suggestions.value = []; return; }
  const { data } = await http.post("/admin/blog/suggest-links", { text: v });
  suggestions.value = data.data;
});
onBeforeUnmount(() => {
  clearTimeout(dirtyTimer);

  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value);
  }
});

onMounted(load);
</script>

<template>
  <section class="section">
    <div class="container editor">
      <div class="editor__main">
        <input v-model="post.title" class="title-input" placeholder="Post title" />
          <p v-if="isNew && !hasValidTitle" class="msg">Enter a title with at least 3 characters.</p>
        <textarea
          v-model="post.body_markdown"
          class="md-input"
          rows="24"
          placeholder="Write in Markdown…"
        />
      </div>

      <aside class="editor__aside">
        <div class="panel">
          <p class="eyebrow">Status</p>
          <p class="status">{{ status }}</p>
          <div class="actions">
            <button class="btn btn--outline" @click="save" :disabled="saving || !hasValidTitle">
              {{ saving ? "Saving…" : "Save draft" }}
            </button>
            <button v-if="status === 'draft' || status === 'rejected'"
                    class="btn btn--primary" @click="transition('submit')">
              Submit for review
            </button>
            <button v-if="status === 'review'"
                    class="btn btn--primary" @click="transition('approve')">
              Approve
            </button>
            <button v-if="status === 'review'"
                    class="btn btn--outline" @click="transition('reject', { reason: 'Needs more detail' })">
              Reject
            </button>
            <button v-if="status === 'scheduled'"
                    class="btn btn--primary" @click="transition('publish')">
              Publish now
            </button>
            <button v-if="status === 'published'"
                    class="btn btn--outline" @click="transition('archive')">
              Archive
            </button>
          </div>
          <p v-if="message" class="msg">{{ message }}</p>
        </div>

        <div class="panel">
          <p class="eyebrow">Excerpt</p>
          <textarea v-model="post.excerpt" rows="3" placeholder="Short summary" />
        </div>

        <div class="panel">
          <p class="eyebrow">Featured image</p>

          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            @change="onFeaturedImageChange"
          />

          <div v-if="displayedImage" class="image-preview">
            <img
              :src="displayedImage"
              :alt="post.featured_image_alt || post.title || 'Blog featured image'"
            />
          </div>

          <input
            v-model="post.featured_image_alt"
            placeholder="Alt text (required)"
          />

          <p class="image-hint">
            JPG, PNG, WebP or GIF. Maximum 5 MB.
          </p>
        </div>

        <div class="panel">
          <p class="eyebrow">Categories</p>
          <label v-for="c in categories" :key="c.id" class="check">
            <input type="checkbox" :value="c.slug" v-model="post.category_slugs" />
            <span>{{ c.name }}</span>
          </label>
        </div>

        <div class="panel">
          <p class="eyebrow">Tags</p>
          <label v-for="t in tags" :key="t.id" class="check">
            <input type="checkbox" :value="t.slug" v-model="post.tag_slugs" />
            <span>{{ t.name }}</span>
          </label>
        </div>

        <div class="panel">
          <p class="eyebrow">SEO</p>
          <input v-model="post.seo_title" placeholder="SEO title" />
          <textarea v-model="post.seo_description" rows="3" placeholder="SEO description (max 320)" />
        </div>

        <div v-if="suggestions.length" class="panel">
          <p class="eyebrow">Suggested internal links</p>
          <ul>
            <li v-for="s in suggestions" :key="s.url">
              <a :href="s.url" target="_blank">{{ s.label }}</a>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.editor { display: grid; grid-template-columns: 1fr 360px; gap: var(--sp-6); align-items: start; }
@media (max-width: 1000px) { .editor { grid-template-columns: 1fr; } }

.title-input {
  width: 100%;
  font-family: var(--font-display);
  font-size: var(--fs-3xl);
  padding: var(--sp-3) 0;
  border: 0;
  background: transparent;
  color: var(--color-plum);
  margin-bottom: var(--sp-4);
}
.title-input:focus { outline: none; }

.md-input {
  width: 100%;
  font-family: "SF Mono", Menlo, monospace;
  font-size: var(--fs-sm);
  padding: var(--sp-4);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.85);
  line-height: 1.5;
  resize: vertical;
}

.editor__aside { display: grid; gap: var(--sp-4); position: sticky; top: calc(var(--header-h) + var(--sp-4)); }
.panel { padding: var(--sp-4); border-radius: var(--radius-md); background: var(--color-ivory); border: 1px solid var(--color-border-soft); }
.panel .eyebrow { margin-bottom: var(--sp-2); }
.panel input, .panel textarea {
  width: 100%; padding: 0.5rem 0.75rem; margin-bottom: var(--sp-2);
  border-radius: var(--radius-sm); border: 1px solid var(--color-border-soft);
  background: #fff; font-size: var(--fs-sm);
}
.check { display: flex; gap: var(--sp-2); align-items: center; font-size: var(--fs-sm); padding: var(--sp-1) 0; }
.status { font-weight: 600; text-transform: capitalize; margin-bottom: var(--sp-3); }
.actions { display: grid; gap: var(--sp-2); }
.msg { font-size: var(--fs-xs); color: var(--color-gold); margin-top: var(--sp-2); }
.image-preview {
  width: 100%;
  aspect-ratio: 16 / 9;
  margin: var(--sp-3) 0;
  overflow: hidden;
  border-radius: var(--radius-md);
  background: #eee;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-hint {
  font-size: var(--fs-xs);
  color: var(--color-text-muted);
}
</style>