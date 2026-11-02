<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { http } from "../api";
import { useAuthStore } from "../stores";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const form = reactive({ email: "", password: "" });
const error = ref<string | null>(null);
const loading = ref(false);

async function submit() {
  error.value = null;
  loading.value = true;
  try {
    const { data } = await http.post("/auth/login", form);
    localStorage.setItem("fw_token", data.data.tokens.access_token);
    await auth.loadFromToken();
    router.push((route.query.next as string) ?? "/admin");
  } catch (e: any) {
    error.value = e?.message ?? "Login failed";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="login">
    <form class="login__form" @submit.prevent="submit">
      <p class="eyebrow">Admin</p>
      <h1>Welcome back</h1>
      <label>
        <span>Email</span>
        <input v-model="form.email" type="email" required autocomplete="email" />
      </label>
      <label>
        <span>Password</span>
        <input v-model="form.password" type="password" required autocomplete="current-password" />
      </label>
      <p v-if="error" class="err">{{ error }}</p>
      <button class="btn btn--primary" :disabled="loading">
        {{ loading ? "Signing in…" : "Sign in" }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.login { min-height: 100vh; display: grid; place-items: center; background: var(--color-plum); padding: var(--sp-5); }
.login__form {
  width: min(420px, 100%);
  background: var(--color-ivory);
  border-radius: var(--radius-lg);
  padding: var(--sp-7);
  display: grid;
  gap: var(--sp-4);
}
.login__form h1 { margin: 0 0 var(--sp-3); }
.login__form label { display: grid; gap: var(--sp-2); font-size: var(--fs-sm); color: var(--color-plum); font-weight: 500; }
.login__form input {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: #fff;
}
.login__form input:focus { outline: none; border-color: var(--color-gold); }
.err { color: #B91C1C; font-size: var(--fs-sm); margin: 0; }
</style>