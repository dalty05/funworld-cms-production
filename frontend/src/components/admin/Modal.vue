<script setup lang="ts">
import { watch, onUnmounted } from "vue";

const props = defineProps<{
  open: boolean;
  title: string;
  size?: "sm" | "md" | "lg";
  closeOnBackdrop?: boolean;
}>();

const emit = defineEmits<{ (e: "close"): void }>();

function close() { emit("close"); }

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") close();
}

watch(() => props.open, (v) => {
  if (v) {
    document.addEventListener("keydown", onKeydown);
    document.body.style.overflow = "hidden";
  } else {
    document.removeEventListener("keydown", onKeydown);
    document.body.style.overflow = "";
  }
});

onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
  document.body.style.overflow = "";
});
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal" @click.self="closeOnBackdrop !== false && close()">
        <div class="modal__panel" :class="`modal__panel--${size ?? 'md'}`">
          <header class="modal__header">
            <h3>{{ title }}</h3>
            <button class="modal__close" @click="close" aria-label="Close">×</button>
          </header>
          <div class="modal__body">
            <slot />
          </div>
          <footer v-if="$slots.footer" class="modal__footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal {
  position: fixed;
  inset: 0;
  background: rgba(43, 15, 46, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: var(--sp-5);
}
.modal__panel {
  background: #fff;
  border-radius: var(--radius-lg);
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 64px rgba(43, 15, 46, 0.25);
}
.modal__panel--sm { max-width: 420px; }
.modal__panel--md { max-width: 560px; }
.modal__panel--lg { max-width: 860px; }
.modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-5) var(--sp-6);
  border-bottom: 1px solid var(--color-border-soft);
}
.modal__header h3 {
  margin: 0;
  font-size: var(--fs-lg);
  font-family: var(--font-display);
  color: var(--color-plum);
}
.modal__close {
  font-size: 24px;
  line-height: 1;
  color: var(--color-text-muted);
  padding: 0 var(--sp-2);
}
.modal__close:hover { color: var(--color-plum); }
.modal__body {
  padding: var(--sp-6);
  overflow-y: auto;
  flex: 1;
}
.modal__footer {
  padding: var(--sp-4) var(--sp-6);
  border-top: 1px solid var(--color-border-soft);
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-3);
}

.modal-enter-active, .modal-leave-active { transition: opacity var(--dur-fast); }
.modal-enter-active .modal__panel, .modal-leave-active .modal__panel { transition: transform var(--dur-base) var(--ease-out); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal__panel { transform: scale(0.96) translateY(8px); }
.modal-leave-to .modal__panel { transform: scale(0.96); }
</style>