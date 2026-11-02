<script setup lang="ts">
import { RouterLink } from "vue-router";
const year = new Date().getFullYear();
</script>

<template>
  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-col footer-col--brand">
          <h3 class="footer-brand">Funworld <em>Events</em></h3>
          <p class="footer-tag">Crafting unforgettable celebrations across Kenya — weddings, corporate, kids' parties, and fundays, all under one roof.</p>
        </div>

        <div class="footer-col">
          <h4>Services</h4>
          <RouterLink to="/services/weddings">Weddings</RouterLink>
          <RouterLink to="/services/corporate">Corporate</RouterLink>
          <RouterLink to="/services/kids">Kids Parties</RouterLink>
          <RouterLink to="/services/school-fundays">School Fundays</RouterLink>
        </div>

        <div class="footer-col">
          <h4>Explore</h4>
          <RouterLink to="/packages">Packages</RouterLink>
          <RouterLink to="/gallery">Gallery</RouterLink>
          <RouterLink to="/blog">Journal</RouterLink>
          <RouterLink to="/about">About</RouterLink>
        </div>

        <div class="footer-col">
          <h4>Contact</h4>
          <a href="mailto:hello@funworld.example">hello@funworld.example</a>
          <a href="tel:+254785068486">+254785068486</a>
          <a href="https://wa.me/254785068486" target="_blank" rel="noopener">WhatsApp</a>
        </div>
      </div>

      <div class="footer-bottom">
        <p>© {{ year }} Funworld Events. All rights reserved.</p>
        <div class="footer-legal">
          <RouterLink to="/privacy">Privacy</RouterLink>
          <RouterLink to="/terms">Terms</RouterLink>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  background: var(--color-plum);
  color: rgba(252, 249, 244, 0.75);
  padding: var(--sp-9) 0 var(--sp-6);
  font-size: var(--fs-sm);
}
.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: var(--sp-7);
  padding-bottom: var(--sp-7);
  border-bottom: 1px solid rgba(201, 164, 92, 0.15);
}
.footer-col { display: flex; flex-direction: column; gap: var(--sp-2); }
.footer-col h4 {
  color: var(--color-gold);
  font-family: var(--font-body);
  font-size: var(--fs-xs);
  letter-spacing: var(--ls-wide);
  text-transform: uppercase;
  margin-bottom: var(--sp-2);
}
.footer-col a {
  color: rgba(252, 249, 244, 0.72);
  transition: color var(--dur-fast);
}
.footer-col a:hover { color: var(--color-gold); }

.footer-brand {
  font-family: var(--font-display);
  color: var(--color-ivory);
  font-size: var(--fs-2xl);
  margin: 0 0 var(--sp-3);
}
.footer-brand em { font-style: italic; color: var(--color-gold); }
.footer-tag { max-width: 40ch; line-height: var(--lh-snug); }

.footer-bottom {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
  padding-top: var(--sp-6);
  font-size: var(--fs-xs);
}
.footer-legal { display: flex; gap: var(--sp-5); }

@media (max-width: 900px) {
  .footer-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 560px) {
  .footer-grid { grid-template-columns: 1fr; }
  .footer-bottom { flex-direction: column; }
}
</style>