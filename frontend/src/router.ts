// router.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  { path: "/", name: "home", component: () => import("./views/Home.vue") },
  { path: "/about", name: "about", component: () => import("./views/About.vue") },
  { path: "/services", name: "services", component: () => import("./views/Services.vue") },
  { path: "/services/:slug", name: "service", component: () => import("./views/ServiceDetail.vue") },
  { path: "/packages", name: "packages", component: () => import("./views/Packages.vue") },
  { path: "/packages/:slug", name: "package", component: () => import("./views/PackageDetail.vue") },
  { path: "/gallery", name: "gallery", component: () => import("./views/Gallery.vue") },


  { path: "/blog", name: "blog", component: () => import("./views/Blog.vue") },
  { path: "/blog/category/:cat", name: "blog-category", component: () => import("./views/Blog.vue") },
  { path: "/blog/:slug", name: "blog-post", component: () => import("./views/BlogPost.vue") },

  { path: "/contact", name: "contact", component: () => import("./views/Contact.vue") },
  { path: "/get-a-quote", name: "quote", component: () => import("./views/QuoteRequest.vue") },
  { path: "/booking/:packageSlug", name: "booking", component: () => import("./views/Booking.vue") },
  { path: "/terms", name: "terms", component: () => import("./views/Legal.vue"), props: { kind: "terms" } },
  { path: "/privacy", name: "privacy", component: () => import("./views/Legal.vue"), props: { kind: "privacy" } },
  {
    path: "/rentals",
    name: "rentals",
    component: () => import("./views/RentalsView.vue"),
  },

  {
    path: "/rentals/:category",
    name: "rental-category",
    component: () => import("./views/RentalCategoryView.vue"),
    props: true,
  },
  


  // Admin
  {
    path: "/admin/login",
    name: "admin-login",
    component: () => import("./views/Login.vue"),
  },
  {
    path: "/admin",
    component: () => import("./layouts/AdminLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      { path: "", name: "admin-home", component: () => import("./views/admin/Dashboard.vue") },

      // Enquiries — "new" must come before ":id"
      // Blog
      { path: "blog", name: "admin-blog", component: () => import("./views/admin/PostList.vue") },
      { path: "blog/posts/new", name: "admin-post-new", component: () => import("./views/admin/PostEditor.vue") },
      { path: "blog/posts/:id", name: "admin-post-edit", component: () => import("./views/admin/PostEditor.vue") },

      // Users — "new" before ":id"
      { path: "users/new", name: "admin-user-new", component: () => import("./views/admin/UserNew.vue") },
      { path: "users/:id", name: "admin-user", component: () => import("./views/admin/UserDetail.vue") },
      { path: "users", name: "admin-users", component: () => import("./views/admin/Users.vue") },
      

      // Roles — "new" before list
      { path: "roles/new", name: "admin-role-new", component: () => import("./views/admin/RoleNew.vue") },
      { path: "roles", name: "admin-roles", component: () => import("./views/admin/Roles.vue") },

      { path: "audit", name: "admin-audit", component: () => import("./views/admin/Audit.vue") },
      

      { path: "services", name: "admin-services", component: () => import("./views/admin/Services.vue") },
      

      // Packages — "new" before ":id"
      { path: "packages/new", name: "admin-package-new", component: () => import("./views/admin/PackageEditor.vue") },
      { path: "packages/:id", name: "admin-package", component: () => import("./views/admin/PackageEditor.vue") },
      { path: "packages", name: "admin-packages", component: () => import("./views/admin/Packages.vue") },


      { path: "inventory", name: "admin-inventory", component: () => import("./views/admin/Inventory.vue") },
      { path: "gallery", name: "admin-gallery", component: () => import("./views/admin/Gallery.vue") },
      { path: "analytics", name: "admin-analytics", component: () => import("./views/admin/Analytics.vue") },
      { path: "settings", name: "admin-settings", component: () => import("./views/admin/Settings.vue") },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, saved) {
    if (saved) return saved;
    if (to.hash) return { el: to.hash, behavior: "smooth" };
    return { top: 0 };
  },
});

import { useAuthStore } from "./stores";

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return;
  const auth = useAuthStore();
  if (!auth.isAuthenticated) {
    await auth.loadFromToken();
  }
  if (!auth.isAuthenticated) {
    return { name: "admin-login", query: { next: to.fullPath } };
  }
});

export default router;