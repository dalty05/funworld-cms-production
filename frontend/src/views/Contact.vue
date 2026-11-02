
<!-- Contact.vue -->

<script setup lang="ts">
import { reactive, ref } from "vue";
import WhatsAppButton from "../components/WhatsAppButton.vue";
import { getWhatsAppLink } from "../api";

const form = reactive({
  full_name: "",
  email: "",
  phone: "",
  subject: "",
  message: "",
});

const submitting = ref(false);
const done = ref(false);
const error = ref<string | null>(null);

async function submit() {
  if (submitting.value) return;

  submitting.value = true;
  error.value = null;

  // Open synchronously from the submit action to avoid popup blocking
  // while waiting for the backend to return the WhatsApp link.
  const whatsappWindow = window.open("about:blank", "_blank");

  if (!whatsappWindow) {
    error.value =
      "Your browser blocked the WhatsApp window. Please allow pop-ups and try again.";
    submitting.value = false;
    return;
  }

  whatsappWindow.opener = null;

  try {
    const lines = [
      "Hello Funworld Events!",
      "",
      "I'd like to get in touch. Here are my details:",
      "",
      `Name: ${form.full_name.trim()}`,
    ];

    if (form.phone.trim()) {
      lines.push(`Phone: ${form.phone.trim()}`);
    }

    if (form.email.trim()) {
      lines.push(`Email: ${form.email.trim()}`);
    }

    if (form.subject.trim()) {
      lines.push(`Subject: ${form.subject.trim()}`);
    }

    lines.push("", "Message:", form.message.trim());

    const link = await getWhatsAppLink({
      kind: "custom",
      text: lines.join("\n"),
      ref: "contact_page",
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
  <section class="section">
    <div class="container contact-grid">
      <div>
        <p class="eyebrow">Say hello</p>
        <h1>Let's talk about your event.</h1>
        <p class="lead">
          Whether it's a wedding, a launch, or a school funday, we'd love to
          hear what you're planning. We respond within a few hours on
          business days.
        </p>

        <ul class="contact-list">
          <li>
            <strong>Email</strong>
            <a href="mailto:hello@funworld.example">
              hello@funworld.example
            </a>
          </li>
          <li>
            <strong>Phone</strong>
            <a href="tel:+254785068486">+254785068486</a>
          </li>
          <li>
            <strong>WhatsApp</strong>
            <WhatsAppButton
              phone="254785068486"
              message="Hello Funworld Events! I'd like to plan an event."
              source-ref="contact_page"
              variant="ghost"
            />
          </li>
        </ul>
      </div>

      <form
        v-if="!done"
        class="glass form"
        @submit.prevent="submit"
      >
        <label>
          <span>Your name *</span>
          <input
            v-model="form.full_name"
            type="text"
            required
            autocomplete="name"
          />
        </label>

        <label>
          <span>Email</span>
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
          />
        </label>

        <label>
          <span>Phone</span>
          <input
            v-model="form.phone"
            type="tel"
            autocomplete="tel"
          />
        </label>

        <label>
          <span>Subject</span>
          <input v-model="form.subject" type="text" />
        </label>

        <label>
          <span>Message *</span>
          <textarea
            v-model="form.message"
            rows="5"
            required
          ></textarea>
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>

        <button
          class="btn btn--primary"
          type="submit"
          :disabled="submitting"
        >
          {{ submitting ? "Preparing WhatsApp…" : "Continue to WhatsApp" }}
        </button>
      </form>

      <div v-else class="glass form form--done">
        <h3>Your message is ready.</h3>
        <p>
          WhatsApp has opened with your message. Review it and tap Send
          to contact Funworld Events.
        </p>
      </div>
    </div>
  </section>
</template>






<style scoped>
.contact-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: var(--sp-7);
  align-items: start;
}
@media (max-width: 900px) { .contact-grid { grid-template-columns: 1fr; } }

.contact-list {
  list-style: none;
  padding: 0;
  margin: var(--sp-6) 0 0;
  display: grid;
  gap: var(--sp-4);
}
.contact-list li { display: flex; flex-direction: column; gap: var(--sp-1); }
.contact-list strong {
  font-size: var(--fs-xs);
  letter-spacing: var(--ls-wide);
  text-transform: uppercase;
  color: var(--color-gold);
}
.contact-list a { font-size: var(--fs-lg); color: var(--color-plum); }

.form { padding: var(--sp-6); display: grid; gap: var(--sp-4); }
.form label {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--color-plum);
  font-weight: 500;
}
.form input, .form textarea {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: rgba(255, 255, 255, 0.85);
}
.form input:focus, .form textarea:focus {
  outline: none;
  border-color: var(--color-gold);
  box-shadow: 0 0 0 3px rgba(201, 164, 92, 0.18);
}
.form--done { text-align: center; padding: var(--sp-8); }
.form-error { color: #B91C1C; font-size: var(--fs-sm); margin: 0; }
</style>