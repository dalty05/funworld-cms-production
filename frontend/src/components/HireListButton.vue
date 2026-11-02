
<script setup lang="ts">
import { useHireListStore } from "../stores/hireList";

const store = useHireListStore();
</script>

<template>
  <Transition name="hire-button">
    <button
      v-if="store.totalItems > 0 && !store.isOpen"
      class="hire-list-button"
      type="button"
      aria-label="Open your hire list"
      title="View your hire list"
      @click="store.openDrawer()"
    >
      <!-- Shopping bag icon -->
      <svg
        viewBox="0 0 24 24"
        width="23"
        height="23"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
        <line x1="3" y1="6" x2="21" y2="6" />
        <path d="M16 10a4 4 0 0 1-8 0" />
      </svg>

      <span class="hire-list-button__label">
        Hire List
      </span>

      <span class="hire-list-button__badge">
        {{ store.totalItems }}
      </span>
    </button>
  </Transition>
</template>

<style scoped>
.hire-list-button {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 90;

  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;

  min-height: 58px;
  padding: 0 1.4rem;

  background: var(--color-plum, #2b0f2e);
  color: var(--color-ivory, #fcf9f4);

  border: 1px solid rgba(212, 175, 106, 0.45);
  border-radius: 50px;

  box-shadow: 0 8px 28px rgba(43, 15, 46, 0.25);

  font-family: var(--font-body, Manrope, sans-serif);
  font-size: 0.9rem;
  font-weight: 600;

  cursor: pointer;
  transition:
    transform 200ms ease,
    background 200ms ease,
    box-shadow 200ms ease;
}

.hire-list-button:hover {
  background: var(--color-charcoal, #1a1417);
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(43, 15, 46, 0.32);
}

.hire-list-button:focus-visible {
  outline: 2px solid var(--color-gold, #d4af6a);
  outline-offset: 4px;
}

.hire-list-button__badge {
  display: flex;
  align-items: center;
  justify-content: center;

  min-width: 24px;
  height: 24px;
  padding: 0 5px;

  border-radius: 50%;
  background: var(--color-gold, #d4af6a);
  color: var(--color-charcoal, #1a1417);

  font-size: 0.75rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

/* Entry and exit animation */
.hire-button-enter-active,
.hire-button-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}

.hire-button-enter-from,
.hire-button-leave-to {
  opacity: 0;
  transform: translateY(15px);
}

@media (max-width: 600px) {
  .hire-list-button {
    bottom: 1rem;
    right: 1rem;
    min-height: 52px;
    padding: 0 1.1rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hire-list-button,
  .hire-button-enter-active,
  .hire-button-leave-active {
    transition: none;
  }
}
</style>
