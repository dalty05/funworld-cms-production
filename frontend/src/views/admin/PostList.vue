<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { http } from "../../api";



import Modal from "../../components/admin/Modal.vue";





const posts = ref<any[]>([]);
const status = ref<string>("");


const showCatModal = ref(false);
const showTagModal = ref(false);
const newCategory = ref({ slug: "", name: "", description: "" });
const newTag = ref({ slug: "", name: "" });
const catError = ref<string | null>(null);
const tagError = ref<string | null>(null);

async function createCategory() {
  catError.value = null;
  try {
    await http.post("/admin/blog/categories", newCategory.value);
    showCatModal.value = false;
    newCategory.value = { slug: "", name: "", description: "" };
  } catch (e: any) {
    catError.value = e?.message ?? "Failed";
  }
}

async function createTag() {
  tagError.value = null;
  try {
    await http.post("/admin/blog/tags", newTag.value);
    showTagModal.value = false;
    newTag.value = { slug: "", name: "" };
  } catch (e: any) {
    tagError.value = e?.message ?? "Failed";
  }
}







async function load() {
  const { data } = await http.get("/admin/blog/posts", {
    params: status.value ? { status: status.value } : {},
  });
  posts.value = data.data;
}
onMounted(load);
</script>

<template>
  <section class="section">
    <div class="container">
      <div class="head">
        <div>
          <p class="eyebrow">Content</p>
          <h1>Blog Posts</h1>
        </div>
        <!-- <RouterLink to="/admin/blog/posts/new" class="btn btn--primary">New post</RouterLink> -->
         
        <div class="head-actions">
          <button class="btn btn--outline" @click="showCatModal = true">New category</button>
          <button class="btn btn--outline" @click="showTagModal = true">New tag</button>
          <RouterLink to="/admin/blog/posts/new" class="btn btn--primary">New post</RouterLink>
        </div>
      </div>

      <div class="filters">
        <button v-for="s in ['', 'draft', 'review', 'scheduled', 'published', 'archived']"
                :key="s" :class="{ active: status === s }" @click="status = s; load()">
          {{ s || "All" }}
        </button>
      </div>

      <table class="posts">
        <thead>
          <tr><th>Title</th><th>Status</th><th>Updated</th><th>Views</th></tr>
        </thead>
        <tbody>
          <tr v-for="p in posts" :key="p.id">
            <td>
              <RouterLink :to="`/admin/blog/posts/${p.id}`">{{ p.title }}</RouterLink>
            </td>
            <td><span class="badge" :class="`badge--${p.status}`">{{ p.status }}</span></td>
            <td>{{ new Date(p.updated_at).toLocaleDateString() }}</td>
            <td>{{ p.view_count ?? 0 }}</td>
          </tr>
        </tbody>
      </table>
    </div>







    <Modal :open="showCatModal" title="New blog category" size="sm" @close="showCatModal = false">
      <label class="field"><span>Slug *</span><input v-model="newCategory.slug" placeholder="kids-parties" /></label>
      <label class="field"><span>Name *</span><input v-model="newCategory.name" placeholder="Kids Parties" /></label>
      <label class="field"><span>Description</span><textarea v-model="newCategory.description" rows="2" /></label>
      <p v-if="catError" class="err">{{ catError }}</p>
      <template #footer>
        <button class="btn btn--outline" @click="showCatModal = false">Cancel</button>
        <button class="btn btn--primary" @click="createCategory">Create</button>
      </template>
    </Modal>

    <Modal :open="showTagModal" title="New blog tag" size="sm" @close="showTagModal = false">
      <label class="field"><span>Slug *</span><input v-model="newTag.slug" placeholder="nairobi" /></label>
      <label class="field"><span>Name *</span><input v-model="newTag.name" placeholder="Nairobi" /></label>
      <p v-if="tagError" class="err">{{ tagError }}</p>
      <template #footer>
        <button class="btn btn--outline" @click="showTagModal = false">Cancel</button>
        <button class="btn btn--primary" @click="createTag">Create</button>
      </template>
    </Modal>











  </section>
</template>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-6); }
.filters { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-5); }
.filters button {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border-soft);
  font-size: var(--fs-sm);
  color: var(--color-plum);
}
.filters button.active { background: var(--color-plum); color: var(--color-ivory); border-color: var(--color-plum); }
table.posts { width: 100%; border-collapse: collapse; }
table.posts th, table.posts td { padding: var(--sp-3) var(--sp-4); text-align: left; border-bottom: 1px solid var(--color-border-soft); }
table.posts th { font-size: var(--fs-xs); letter-spacing: var(--ls-wide); text-transform: uppercase; color: var(--color-gold); }
.badge { padding: 2px 10px; border-radius: var(--radius-pill); font-size: var(--fs-xs); text-transform: uppercase; letter-spacing: 0.05em; }
.badge--draft { background: #EFE6D5; color: #6B6B6B; }
.badge--review { background: #FEF3C7; color: #92400E; }
.badge--scheduled { background: #DBEAFE; color: #1E40AF; }
.badge--published { background: #D1FAE5; color: #065F46; }
.badge--archived { background: #E5E7EB; color: #4B5563; }
.badge--rejected { background: #FEE2E2; color: #991B1B; }




.head-actions { display: flex; gap: var(--sp-2); }
.field { display: grid; gap: var(--sp-2); margin-bottom: var(--sp-4); font-size: var(--fs-sm); color: var(--color-plum); font-weight: 500; }
.field input, .field textarea { padding: 0.6rem 0.9rem; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); background: #fff; font-size: var(--fs-sm); }
.err { color: #B91C1C; font-size: var(--fs-sm); }
</style>