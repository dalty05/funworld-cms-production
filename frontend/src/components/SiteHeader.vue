<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { RouterLink, useRoute } from "vue-router";

const scrolled = ref(false);
const mobileOpen = ref(false);
const route = useRoute();

function onScroll() {
  scrolled.value = window.scrollY > 24;
}
onMounted(() => window.addEventListener("scroll", onScroll, { passive: true }));
onUnmounted(() => window.removeEventListener("scroll", onScroll));

function closeMenu() { mobileOpen.value = false; }
</script>

<template>
  <header class="site-header" :class="{ 'site-header--scrolled': scrolled }">
    <div class="container site-header__inner">
      <RouterLink to="/" class="brand" @click="closeMenu">
        <span class="brand__mark">F</span>
        <span class="brand__name">Funworld <em>Events</em></span>
      </RouterLink>

      <nav class="nav" :class="{ 'nav--open': mobileOpen }">
        <RouterLink to="/services" @click="closeMenu">Services</RouterLink>
        <RouterLink to="/packages" @click="closeMenu">Packages</RouterLink>
        <RouterLink to="/rentals" @click="closeMenu">Rentals</RouterLink>
        <RouterLink to="/gallery" @click="closeMenu">Gallery</RouterLink>
        <RouterLink to="/blog" @click="closeMenu">Journal</RouterLink>
        <RouterLink to="/about" @click="closeMenu">About</RouterLink>
        <RouterLink to="/contact" @click="closeMenu">Contact</RouterLink>
        <RouterLink to="/get-a-quote" class="btn btn--primary nav__cta" @click="closeMenu">
          Get a Quote
        </RouterLink>
      </nav>

      <button
        class="menu-toggle"
        :aria-expanded="mobileOpen"
        aria-label="Toggle menu"
        @click="mobileOpen = !mobileOpen"
      >
        <span /><span /><span />
      </button>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: fixed;
  inset: 0 0 auto 0;
  z-index: 50;
  transition: all var(--dur-base) var(--ease-out);
}
.site-header--scrolled {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-bottom: var(--glass-border);
  box-shadow: var(--shadow-soft);
}
.site-header__inner {
  height: var(--header-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-6);
}
.brand {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  font-family: var(--font-display);
}
.brand__mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: var(--radius-pill);
  background: var(--color-gold);
  color: var(--color-plum);
  font-weight: 600;
  font-size: var(--fs-lg);
}
.brand__name {
  font-size: var(--fs-lg);
  color: var(--color-plum);
}
.brand__name em {
  font-style: italic;
  color: var(--color-gold);
}

.nav {
  display: flex;
  align-items: center;
  gap: var(--sp-6);
  font-weight: 500;
  font-size: var(--fs-sm);
}
.nav a { color: var(--color-plum); transition: color var(--dur-fast); }
.nav a:hover { color: var(--color-gold); }
.nav .nav__cta { color: var(--color-plum); }
.nav .nav__cta:hover { color: var(--color-plum); }

.menu-toggle {
  display: none;
  flex-direction: column;
  gap: 5px;
  padding: var(--sp-2);
}
.menu-toggle span {
  display: block;
  width: 24px;
  height: 2px;
  background: var(--color-plum);
  transition: all var(--dur-fast);
}

@media (max-width: 900px) {
  .menu-toggle { display: flex; }
  .nav {
    position: fixed;
    inset: var(--header-h) 0 0 0;
    flex-direction: column;
    align-items: flex-start;
    padding: var(--sp-6) var(--container-pad);
    gap: var(--sp-5);
    background: var(--color-ivory);
    transform: translateX(100%);
    transition: transform var(--dur-base) var(--ease-out);
  }
  .nav--open { transform: translateX(0); }
  .nav a { font-size: var(--fs-lg); }
}
</style>