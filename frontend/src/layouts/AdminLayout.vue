<script setup lang="ts">
import { RouterView, RouterLink, useRoute, useRouter } from "vue-router";
import { computed, ref } from "vue";
import { useAuthStore } from "../stores";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const sidebarOpen = ref(false);

const nav = computed(() => [
  { to: "/admin", label: "Dashboard", icon: "home", show: true },
  { to: "/admin/blog", label: "Content", icon: "pen", show: auth.can("content.view") },
  { to: "/admin/users", label: "Users", icon: "user-cog", show: auth.can("user.view") },
  { to: "/admin/roles", label: "Roles", icon: "shield", show: auth.can("role.view") },
  { to: "/admin/audit", label: "Audit log", icon: "history", show: auth.can("audit.view") },
  
  { to: "/admin/services", label: "Services", icon: "grid", show: auth.can("service.view") },
  { to: "/admin/packages", label: "Packages", icon: "box", show: auth.can("package.view") },  
  { to: "/admin/inventory", label: "Inventory", icon: "box", show: auth.can("inventory.view") },
  { to: "/admin/gallery", label: "Gallery", icon: "image", show: auth.can("gallery.view") },
  { to: "/admin/analytics", label: "Analytics", icon: "chart", show: auth.can("settings.view") },
  { to: "/admin/settings", label: "Settings", icon: "settings", show: auth.can("settings.view") },

].filter(x => x.show));

function logout() {
  auth.logout();
  router.push("/admin/login");
}
</script>

<template>
  <div class="admin">
    <aside class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
      <RouterLink to="/admin" class="sidebar__brand" @click="sidebarOpen = false">
        <span class="sidebar__mark">F</span>
        <span class="sidebar__name">Funworld <em>Admin</em></span>
      </RouterLink>

      <nav class="sidebar__nav">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="sidebar__link"
          :class="{ 'sidebar__link--active': route.path.startsWith(item.to) }"
          @click="sidebarOpen = false"
        >
          <span class="sidebar__dot" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar__footer">
        <RouterLink to="/" class="sidebar__public" target="_blank">
          View public site ↗
        </RouterLink>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <button class="topbar__menu" @click="sidebarOpen = !sidebarOpen" aria-label="Toggle menu">
          <span /><span /><span />
        </button>

        <div class="topbar__search">
          <input placeholder="Search enquiries, bookings, customers…" />
        </div>

        <div class="topbar__actions">
          <div class="user-chip">
            <span class="user-chip__avatar">
              {{ (auth.user?.full_name ?? "?")[0].toUpperCase() }}
            </span>
            <span class="user-chip__name">{{ auth.user?.full_name }}</span>
            <button class="user-chip__logout" @click="logout">Sign out</button>
          </div>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin {
  display: grid;
  grid-template-columns: 260px 1fr;
  min-height: 100vh;
  background: #F5F2EC;
}
/* .sidebar {
  background: var(--color-plum);
  color: var(--color-ivory);
  display: flex;
  flex-direction: column;
  padding: var(--sp-5) 0;
  position: sticky;
  top: 0;
  height: 100vh;
} */



.sidebar {
  background: var(--color-plum);
  color: var(--color-ivory);
  display: flex;
  flex-direction: column;
  padding: var(--sp-5) 0;
  position: sticky;
  top: 0;
  height: 100vh;
  height: 100dvh;
  box-sizing: border-box;
  overflow: hidden;
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior-y: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(201, 164, 92, 0.45) transparent;
}

.sidebar__nav::-webkit-scrollbar {
  width: 5px;
}

.sidebar__nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar__nav::-webkit-scrollbar-thumb {
  background: rgba(201, 164, 92, 0.45);
  border-radius: 10px;
}




.sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: 0 var(--sp-5) var(--sp-6);
  font-family: var(--font-display);
}
.sidebar__mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-gold);
  color: var(--color-plum);
  font-weight: 600;
}
.sidebar__name { font-size: var(--fs-lg); }
.sidebar__name em { font-style: italic; color: var(--color-gold); }
/* .sidebar__nav {
  display: flex;
  flex-direction: column;
  flex: 1;
} */
.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-5);
  font-size: var(--fs-sm);
  color: rgba(252, 249, 244, 0.7);
  transition: all var(--dur-fast);
}
.sidebar__link:hover {
  color: var(--color-ivory);
  background: rgba(201, 164, 92, 0.08);
}
.sidebar__link--active {
  color: var(--color-ivory);
  background: rgba(201, 164, 92, 0.14);
  border-left: 3px solid var(--color-gold);
  padding-left: calc(var(--sp-5) - 3px);
}
.sidebar__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.4;
}
.sidebar__link--active .sidebar__dot { opacity: 1; background: var(--color-gold); }
.sidebar__footer {
  padding: var(--sp-4) var(--sp-5) 0;
  border-top: 1px solid rgba(201, 164, 92, 0.12);
}
.sidebar__public {
  font-size: var(--fs-xs);
  color: rgba(252, 249, 244, 0.5);
}

.main { display: flex; flex-direction: column; min-width: 0; }
.topbar {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  height: 64px;
  padding: 0 var(--sp-6);
  background: var(--color-ivory);
  border-bottom: 1px solid var(--color-border-soft);
  position: sticky;
  top: 0;
  z-index: 10;
}
.topbar__menu {
  display: none;
  flex-direction: column;
  gap: 4px;
  padding: var(--sp-2);
}
.topbar__menu span { display: block; width: 20px; height: 2px; background: var(--color-plum); }
.topbar__search { flex: 1; max-width: 480px; }
.topbar__search input {
  width: 100%;
  padding: 0.6rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: rgba(255, 255, 255, 0.9);
  font-size: var(--fs-sm);
}
.topbar__search input:focus {
  outline: none;
  border-color: var(--color-gold);
}
.topbar__actions { margin-left: auto; }
.user-chip {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  font-size: var(--fs-sm);
}
.user-chip__avatar {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-gold);
  color: var(--color-plum);
  font-weight: 600;
}
.user-chip__name { color: var(--color-plum); font-weight: 500; }
.user-chip__logout {
  color: var(--color-text-muted);
  font-size: var(--fs-xs);
  padding: 0.4rem 0.8rem;
  border-radius: var(--radius-md);
  transition: background var(--dur-fast);
}
.user-chip__logout:hover { background: rgba(43, 15, 46, 0.05); }

.content { padding: var(--sp-6); flex: 1; }

@media (max-width: 900px) {
  .admin { grid-template-columns: 1fr; }
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: 260px;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform var(--dur-base) var(--ease-out);
  }
  .sidebar--open { transform: translateX(0); }
  .topbar__menu { display: flex; }
}
</style>