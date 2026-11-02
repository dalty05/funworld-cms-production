<script setup lang="ts">
import { ref, computed } from "vue";

// Replace this with your actual Funworld Events WhatsApp number (include country code, no + or spaces)
const WHATSAPP_NUMBER = "254700000000"; 

const enquiryName = ref("");
const enquiryEmail = ref("");
const enquiryMessage = ref("");

const whatsappLink = computed(() => {
  const text = `Hello Funworld Events!%0A%0A*Name:* ${enquiryName.value}%0A*Email:* ${enquiryEmail.value}%0A%0A*Message:*%0A${enquiryMessage.value}`;
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${text}`;
});

function submitWhatsApp() {
  if (!enquiryName.value || !enquiryMessage.value) {
    alert("Please fill in your name and message.");
    return;
  }
  // Open WhatsApp in a new tab
  window.open(whatsappLink.value, "_blank");
}
</script>

<template>
  <div class="about-page">
    <!-- HERO SECTION (Dark background with overlapping gallery) -->
    <section class="about-hero">
      <div class="about-hero__inner">
        <div class="gallery-wrap">
          <div class="gallery-item gallery-item--left">
            <!-- Replace with actual event image -->
            <img src="https://images.unsplash.com/photo-1511795409834-ef04bbd61622?auto=format&fit=crop&q=80&w=400" alt="Event setup detail" />
          </div>
          <div class="gallery-item gallery-item--center">
            <!-- Replace with actual event image -->
            <img src="https://images.unsplash.com/photo-1519225421980-715cb0215aed?auto=format&fit=crop&q=80&w=800" alt="Beautiful event setup" />
          </div>
          <div class="gallery-item gallery-item--right">
            <!-- Replace with actual event image -->
            <img src="https://images.unsplash.com/photo-1478146896981-b80fe463b330?auto=format&fit=crop&q=80&w=400" alt="Event detail" />
          </div>
        </div>
        <p class="hero-caption">Elevating events with elegance and precision.</p>
      </div>
    </section>

    <!-- WELCOME SECTION (3 Columns) -->
    <section class="about-content">
      <div class="about-content__inner">
        
        <!-- Column 1: Welcome -->
        <div class="content-col">
          <h2 class="col-title">Welcome</h2>
          <p class="col-text">
            Funworld Events has grown from a small décor crew into a full event partner. We handle weddings, corporate gatherings, kids' parties, and everything in between.
          </p>
          <p class="col-text">
            Our foundation is simple: we show up, we deliver exactly what we promise, and we maintain the same high standard every single time.
          </p>
        </div>

        <div class="col-divider"></div>

        <!-- Column 2: Our Story -->
        <div class="content-col">
          <h2 class="col-title">Our Story</h2>
          <ul class="story-list">
            <li>
              <strong>Founded with a vision</strong>
              <span>To make premium event rentals accessible and stress-free.</span>
            </li>
            <li>
              <strong>Built on reliability</strong>
              <span>Punctual delivery, professional setup, and meticulous teardown.</span>
            </li>
            <li>
              <strong>Endless variety</strong>
              <span>From intimate backyard gatherings to large-scale corporate galas.</span>
            </li>
            <li>
              <strong>Client-first approach</strong>
              <span>Your vision is our blueprint. We listen, adapt, and execute.</span>
            </li>
          </ul>
        </div>

        <div class="col-divider"></div>

        <!-- Column 3: Useful Info -->
        <div class="content-col">
          <h2 class="col-title">Useful Info</h2>
          <ul class="useful-list">
            <li>
              <span class="label">Car parking</span>
              <span class="value">Available at all major venues</span>
            </li>
            <li>
              <span class="label">Delivery</span>
              <span class="value">Nationwide logistics available</span>
            </li>
            <li>
              <span class="label">Setup & Teardown</span>
              <span class="value">Included in most packages</span>
            </li>
            <li>
              <span class="label">Customization</span>
              <span class="value">Bespoke layouts and themes</span>
            </li>
            <li>
              <span class="label">Support</span>
              <span class="value">Dedicated event coordinator</span>
            </li>
          </ul>
        </div>

      </div>
    </section>

    <!-- BOTTOM SECTION (Floating Card) -->
    <section class="about-bottom-wrapper">
      <div class="floating-card">
        
        <!-- Left: Join Us -->
        <div class="bottom-col">
          <h2 class="bottom-title">Join Us</h2>
          <div class="social-links">
            <!-- Add your actual social media links here -->
            <a href="#" target="_blank" rel="noopener noreferrer" aria-label="Facebook" class="social-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"/></svg>
            </a>
            <a href="#" target="_blank" rel="noopener noreferrer" aria-label="Instagram" class="social-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
            </a>
            <a href="#" target="_blank" rel="noopener noreferrer" aria-label="X (Twitter)" class="social-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            </a>
            <a href="#" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn" class="social-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            </a>
          </div>
          <div class="join-text">
            <p>Stay updated with our latest setups, behind-the-scenes looks, and seasonal offers.</p>
            <p>Subscribe to our newsletter for inspiration and event planning tips.</p>
          </div>
        </div>

        <!-- Right: WhatsApp Quick Form -->
        <div class="bottom-col">
          <h2 class="bottom-title">Quick Enquiry</h2>
          <form @submit.prevent="submitWhatsApp" class="quick-form">
            <div class="form-group">
              <input v-model="enquiryName" type="text" placeholder="Your Name" required />
            </div>
            <div class="form-group">
              <input v-model="enquiryEmail" type="email" placeholder="Email Address (Optional)" />
            </div>
            <div class="form-group">
              <textarea v-model="enquiryMessage" placeholder="Tell us about your event..." rows="3" required></textarea>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn--whatsapp">
                Send via WhatsApp
                <!-- Small WhatsApp Icon inside button -->
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" style="margin-left: 8px;">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
              </button>
            </div>
          </form>
        </div>

      </div>
    </section>
  </div>
</template>

<style scoped>
/* ── Page Wrapper ─────────────────────────────────────────── */
.about-page {
  background: var(--color-ivory);
  color: var(--color-charcoal);
  font-family: var(--font-body);
}

/* ── HERO SECTION ─────────────────────────────────────────── */
.about-hero {
  background-color: #3a3531; /* Dark, muted earth tone */
  padding: 5rem 1.25rem 3rem;
  position: relative;
  overflow: hidden;
}

.about-hero__inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gallery-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  width: 100%;
  max-width: 900px;
  position: relative;
}

.gallery-item {
  position: relative;
  background: var(--color-ivory);
  padding: 0.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.gallery-item img {
  display: block;
  object-fit: cover;
  width: 100%;
  height: 100%;
}

/* Center Image (Main) */
.gallery-item--center {
  width: 55%;
  aspect-ratio: 4 / 3;
  z-index: 2;
}

/* Side Images (Smaller, lower) */
.gallery-item--left,
.gallery-item--right {
  width: 25%;
  aspect-ratio: 3 / 4;
  z-index: 1;
  transform: translateY(20px);
}

.hero-caption {
  margin-top: 3rem;
  font-family: var(--font-display);
  font-size: 1.1rem;
  color: var(--color-ivory);
  letter-spacing: 0.05em;
  font-style: italic;
}

/* ── CONTENT SECTION (3 Cols) ─────────────────────────────── */
.about-content {
  padding: 5rem 1.25rem;
  background: var(--color-ivory);
}

.about-content__inner {
  max-width: 1120px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1px 1fr 1px 1fr;
  gap: 2rem;
}

.content-col {
  display: flex;
  flex-direction: column;
}

.col-divider {
  background: var(--color-clay);
  width: 100%;
  height: 100%;
}

.col-title {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 400;
  font-style: italic;
  color: var(--color-plum);
  margin: 0 0 1.5rem;
  border-bottom: 1px solid var(--color-clay);
  padding-bottom: 0.5rem;
  display: inline-block;
}

.col-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--color-text-muted);
  margin: 0 0 1rem;
}

/* Story List */
.story-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.story-list li {
  margin-bottom: 1.25rem;
}

.story-list strong {
  display: block;
  font-size: 0.9rem;
  color: var(--color-charcoal);
  margin-bottom: 0.25rem;
}

.story-list span {
  display: block;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  line-height: 1.4;
}

/* Useful List */
.useful-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.useful-list li {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}

.useful-list .label {
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--color-clay);
  margin-bottom: 0.15rem;
}

.useful-list .value {
  font-size: 0.9rem;
  color: var(--color-charcoal);
}

/* ── BOTTOM SECTION (Floating Card) ───────────────────────── */
.about-bottom-wrapper {
  background: #f4efea; /* Slightly darker than ivory to contrast the floating card */
  padding: 4rem 1.25rem 6rem;
  position: relative;
}

.floating-card {
  max-width: 1120px;
  margin: -8rem auto 0; /* Negative margin to pull it up over the content above */
  background: var(--color-ivory);
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(26, 20, 23, 0.08);
  border-top: 4px solid var(--color-plum); /* Accent line */
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  position: relative;
  z-index: 10;
  border-radius: 2px;
}

.bottom-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 400;
  color: var(--color-plum);
  margin: 0 0 1.5rem;
}

.social-links {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.social-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-ivory);
  border: 1px solid var(--color-clay);
  color: var(--color-plum);
  border-radius: 50%; /* Circular icons */
  text-decoration: none;
  transition: all 200ms ease;
}

.social-icon:hover {
  background: var(--color-plum);
  color: var(--color-ivory);
  border-color: var(--color-plum);
}

.join-text p {
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--color-text-muted);
  margin: 0 0 1rem;
}

/* Form Styles */
.quick-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--color-charcoal);
  background: #faf8f5;
  border: 1px solid var(--color-clay);
  border-radius: 2px;
  transition: border-color 200ms ease, outline 200ms ease;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: 2px solid var(--color-gold);
  outline-offset: -1px;
  border-color: transparent;
  background: var(--color-ivory);
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.8rem 2rem;
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ivory);
  background: var(--color-plum);
  border: 1px solid var(--color-plum);
  border-radius: 2px;
  cursor: pointer;
  transition: background 180ms ease, border-color 180ms ease;
}

.btn--whatsapp {
  background: #25D366; /* Standard WhatsApp Green */
  border-color: #25D366;
  color: #fff;
}

.btn--whatsapp:hover {
  background: #128C7E;
  border-color: #128C7E;
}

.btn:focus-visible {
  outline: 2px solid var(--color-gold);
  outline-offset: 2px;
}

/* ── RESPONSIVE ───────────────────────────────────────────── */
@media (max-width: 900px) {
  .about-content__inner {
    grid-template-columns: 1fr;
    gap: 3rem;
  }

  .col-divider {
    display: none;
  }

  .floating-card {
    grid-template-columns: 1fr;
    gap: 3rem;
    padding: 2rem;
    margin-top: -4rem;
  }
}

@media (max-width: 600px) {
  .gallery-wrap {
    flex-direction: column;
    gap: 1.5rem;
  }

  .gallery-item--center {
    width: 100%;
  }

  .gallery-item--left,
  .gallery-item--right {
    display: none; /* Hide side images on very small screens */
  }

  .about-hero {
    padding: 3rem 1.25rem 2rem;
  }

  .hero-caption {
    margin-top: 1.5rem;
    text-align: center;
  }
}
</style>