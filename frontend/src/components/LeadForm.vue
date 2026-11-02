
<!-- LeadForm.vue -->

<script setup lang="ts">
import { reactive, ref, computed } from "vue";
import { getWhatsAppLink } from "../api";
import { useRoute } from "vue-router";

const route = useRoute();

const props = defineProps<{
  channel?: string;
  eventType?: string;
  sourceRef?: string;
  packageId?: string;
}>();

const form = reactive({
  full_name: "",
  phone: "",
  email: "",
  event_type: props.eventType ?? "",
  event_date: "",
  venue: "",
  guest_count: undefined as number | undefined,
  budget_indication: "",
  notes: "",
});

const submitting = ref(false);
const done = ref(false);
const error = ref<string | null>(null);

const canSubmit = computed(() =>
  form.full_name.trim().length > 1 &&
  (form.phone.trim().length > 0 || form.email.trim().length > 0)
);

function formatEventType(value: string) {
  if (!value) return "";

  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function buildWhatsAppMessage() {
  const lines = [
    "Hello Funworld Events!",
    "",
    "I'd like to request a quote for my event. Here are my details:",
    "",
    `Name: ${form.full_name.trim()}`,
  ];

  if (form.phone.trim()) {
    lines.push(`Phone: ${form.phone.trim()}`);
  }

  if (form.email.trim()) {
    lines.push(`Email: ${form.email.trim()}`);
  }

  if (form.event_type) {
    lines.push(`Event type: ${formatEventType(form.event_type)}`);
  }

  if (form.event_date) {
    lines.push(`Preferred date: ${form.event_date}`);
  }

  if (form.venue.trim()) {
    lines.push(`Venue / location: ${form.venue.trim()}`);
  }

  if (form.guest_count !== undefined && form.guest_count !== null) {
    lines.push(`Expected guests: ${form.guest_count}`);
  }

  if (form.budget_indication.trim()) {
    lines.push(`Budget indication: ${form.budget_indication.trim()}`);
  }

  if (form.notes.trim()) {
    lines.push("", `Additional details: ${form.notes.trim()}`);
  }

  if (props.packageId) {
    lines.push("", `Package reference: ${props.packageId}`);
  }

  // Preserve useful source context for the team.
  lines.push(
    "",
    `Website page: ${route.path}`,
    `Enquiry channel: ${props.channel ?? "website_inquiry"}`
  );

  return lines.join("\n");
}

async function submit() {
  if (!canSubmit.value || submitting.value) return;

  submitting.value = true;
  error.value = null;

  // Open the tab immediately during the user action to reduce
  // the chance of the browser blocking it after the API request.
  const whatsappWindow = window.open("about:blank", "_blank");

  if (!whatsappWindow) {
    error.value =
      "Your browser blocked the WhatsApp window. Please allow pop-ups and try again.";
    submitting.value = false;
    return;
  }

  // Prevent the new page from accessing this page through window.opener.
  whatsappWindow.opener = null;

  try {
    const message = buildWhatsAppMessage();

    const link = await getWhatsAppLink({
      kind: "custom",
      text: message,
      ref: props.sourceRef ?? "quote_request",
    });

    whatsappWindow.location.replace(link);
    done.value = true;
  } catch (e: unknown) {
    whatsappWindow.close();

    error.value =
      e instanceof Error
        ? e.message
        : "Could not open WhatsApp. Please try again.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <form
    v-if="!done"
    class="lead-form glass"
    @submit.prevent="submit"
  >
    <div class="field-row">
      <label class="field">
        <span>Your name *</span>
        <input
          v-model="form.full_name"
          type="text"
          required
          autocomplete="name"
        />
      </label>
    </div>

    <div class="field-row">
      <label class="field">
        <span>Phone</span>
        <input
          v-model="form.phone"
          type="tel"
          autocomplete="tel"
          placeholder="+254 7XX XXX XXX"
        />
      </label>

      <label class="field">
        <span>Email</span>
        <input
          v-model="form.email"
          type="email"
          autocomplete="email"
        />
      </label>
    </div>

    <div class="field-row">
      <label class="field">
        <span>Event type</span>
        <select v-model="form.event_type">
          <option value="">Select…</option>
          <option value="wedding">Wedding</option>
          <option value="corporate">Corporate</option>
          <option value="kids_party">Kids party</option>
          <option value="funday">School funday</option>
          <option value="other">Other</option>
        </select>
      </label>

      <label class="field">
        <span>Preferred date</span>
        <input v-model="form.event_date" type="date" />
      </label>
    </div>

    <div class="field-row">
      <label class="field">
        <span>Venue / location</span>
        <input v-model="form.venue" type="text" />
      </label>

      <label class="field">
        <span>Guests</span>
        <input
          v-model.number="form.guest_count"
          type="number"
          min="1"
        />
      </label>
    </div>

    <div class="field-row">
      <label class="field">
        <span>Budget indication</span>
        <input
          v-model="form.budget_indication"
          type="text"
          placeholder="e.g. 100k–200k"
        />
      </label>
    </div>

    <label class="field">
      <span>Anything else we should know?</span>
      <textarea v-model="form.notes" rows="4"></textarea>
    </label>

    <p v-if="error" class="form-error">
      {{ error }}
    </p>

    <button
      type="submit"
      class="btn btn--primary form-submit"
      :disabled="!canSubmit || submitting"
    >
      {{ submitting ? "Preparing WhatsApp…" : "Continue to WhatsApp" }}
    </button>

    <p class="form-fineprint">
      WhatsApp will open with your enquiry ready to send. Review the
      message and tap Send to contact us.
    </p>
  </form>

  <div v-else class="lead-form lead-form--done glass">
    <h3>Your enquiry is ready.</h3>
    <p>
      WhatsApp has opened with your event details. Review your message
      and tap Send to share it with Funworld Events.
    </p>
  </div>
</template>

<style scoped>
.lead-form {
  padding: var(--sp-6);
  display: grid;
  gap: var(--sp-4);
}
.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-4);
}
@media (max-width: 560px) { .field-row { grid-template-columns: 1fr; } }

.field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--color-plum);
  font-weight: 500;
}
.field input, .field select, .field textarea {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: rgba(255, 255, 255, 0.85);
  color: var(--color-text);
  transition: border-color var(--dur-fast);
}
.field input:focus, .field select:focus, .field textarea:focus {
  outline: none;
  border-color: var(--color-gold);
  box-shadow: 0 0 0 3px rgba(201, 164, 92, 0.18);
}
.form-submit { justify-content: center; }
.form-fineprint {
  font-size: var(--fs-xs);
  color: var(--color-text-muted);
  margin: 0;
}
.form-error {
  color: #B91C1C;
  font-size: var(--fs-sm);
  margin: 0;
}
.lead-form--done {
  text-align: center;
  padding: var(--sp-8) var(--sp-6);
}
.lead-form--done h3 { margin-bottom: var(--sp-3); }
</style>