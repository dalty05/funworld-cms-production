<!-- QuoteRequest.vue -->

<script setup lang="ts">
import LeadForm from "../components/LeadForm.vue";
</script>

<template>
  <section class="section">
    <div class="container quote-grid">
      <div>
        <p class="eyebrow">Get a quote</p>
        <h1>Tell us about your event.</h1>
        <p class="lead">
          The more you share, the more accurate the quote. We'll review
          your details and come back within a few hours on business days.
        </p>

        <ul class="checklist">
          <li>Tailored pricing for your date and guest count</li>
          <li>Package recommendations if you're not sure where to start</li>
          <li>No obligation — just clarity on what's possible</li>
        </ul>
      </div>

      <LeadForm channel="website_inquiry" />
    </div>
  </section>
</template>

<style scoped>
.quote-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: var(--sp-7);
  align-items: start;
}
@media (max-width: 900px) { .quote-grid { grid-template-columns: 1fr; } }

.checklist {
  list-style: none;
  padding: 0;
  margin: var(--sp-6) 0 0;
  display: grid;
  gap: var(--sp-3);
  color: var(--color-text-muted);
}
.checklist li::before {
  content: "◆";
  color: var(--color-gold);
  margin-right: var(--sp-2);
  font-size: 0.7em;
}
</style>