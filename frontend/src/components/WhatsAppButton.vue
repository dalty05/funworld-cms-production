<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useSettingsStore } from "../stores/settings";

const props = defineProps<{
  /** If omitted, uses company_phone from public settings. */
  phone?: string;
  message: string;
  sourceRef?: string;
  label?: string;
  variant?: "solid" | "ghost";
  floating?: boolean;
}>();

const settings = useSettingsStore();
onMounted(() => settings.load());

const resolvedPhone = computed<string | null>(() => {
  const explicit = props.phone?.replace(/\D/g, "");
  if (explicit) return explicit;
  return settings.whatsappPhone();
});

const link = computed<string | null>(() => {
  const digits = resolvedPhone.value;
  if (!digits) return null;
  const text = props.sourceRef
    ? `${props.message}\n\n[ref: ${props.sourceRef}]`
    : props.message;
  return `https://wa.me/${digits}?text=${encodeURIComponent(text)}`;
});
</script>

<template>
  <a
    v-if="link"
    :href="link"
    target="_blank"
    rel="noopener"
    class="wa-btn"
    :class="[`wa-btn--${variant ?? 'solid'}`, { 'wa-btn--floating': floating }]"
    :aria-label="floating ? (label ?? 'Chat on WhatsApp') : undefined"
  >
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.5 3.5A11.9 11.9 0 0 0 12 0C5.4 0 0 5.4 0 12c0 2.1.6 4.1 1.6 5.9L0 24l6.3-1.6a12 12 0 0 0 5.7 1.5h.1c6.6 0 12-5.4 12-12 0-3.2-1.3-6.2-3.6-8.4zM12 21.8c-1.8 0-3.5-.5-5-1.3l-.4-.2-3.7 1 1-3.6-.2-.4a9.8 9.8 0 0 1-1.5-5.3c0-5.4 4.4-9.8 9.8-9.8 2.6 0 5 1 6.9 2.9a9.7 9.7 0 0 1 2.9 6.9c0 5.4-4.4 9.8-9.8 9.8zm5.4-7.3c-.3-.1-1.8-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.7 1-.9 1.1-.2.2-.4.2-.7.1-.3-.1-1.2-.5-2.4-1.4-.9-.8-1.5-1.7-1.7-2-.2-.3 0-.5.1-.7.1-.1.3-.4.5-.6.1-.2.2-.3.3-.5.1-.2 0-.4 0-.5 0-.1-.7-1.7-1-2.3-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.4s1 2.8 1.2 3c.1.2 1.9 2.9 4.7 4.1.7.3 1.2.5 1.6.6.7.2 1.3.2 1.8.1.5-.1 1.8-.7 2-1.4.2-.7.2-1.3.2-1.4 0-.1-.2-.2-.4-.3z"/>
    </svg>
    <span v-if="!floating">{{ label ?? "Chat on WhatsApp" }}</span>
  </a>
</template>

<style scoped>
.wa-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-pill);
  font-weight: 600;
  font-size: var(--fs-sm);
  transition: all var(--dur-base) var(--ease-out);
}
.wa-btn svg { width: 18px; height: 18px; }
.wa-btn--solid {
  background: #25D366;
  color: #0b2310;
  box-shadow: 0 6px 24px rgba(37, 211, 102, 0.28);
}
.wa-btn--solid:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 32px rgba(37, 211, 102, 0.36);
}
.wa-btn--ghost {
  background: transparent;
  border: 1px solid rgba(37, 211, 102, 0.5);
  color: #25D366;
}
.wa-btn--ghost:hover {
  background: rgba(37, 211, 102, 0.08);
  border-color: #25D366;
}
.wa-btn--floating {
  position: fixed;
  right: 1.25rem;
  bottom: 1.25rem;
  z-index: 60;
  width: 56px;
  height: 56px;
  padding: 0;
  border-radius: 50%;
  background: rgba(37, 211, 102, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: #0b2310;
  box-shadow: 0 12px 32px rgba(37, 211, 102, 0.4);
}
.wa-btn--floating svg { width: 26px; height: 26px; }
.wa-btn--floating:hover {
  transform: scale(1.06);
  background: #25D366;
}
</style>