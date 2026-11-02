import { defineStore } from "pinia";
import { ref } from "vue";
import { getPublicSettings, type PublicSettings } from "../api";

export const useSettingsStore = defineStore("settings", () => {
  const loaded = ref(false);
  const settings = ref<PublicSettings>({});
  let inflight: Promise<void> | null = null;

  async function load(): Promise<void> {
    if (loaded.value) return;
    if (inflight) return inflight;
    inflight = (async () => {
      try {
        settings.value = await getPublicSettings();
      } catch {
        settings.value = {};
      } finally {
        loaded.value = true;
        inflight = null;
      }
    })();
    return inflight;
  }

  function get(key: string, fallback: string | null = null): string | null {
    const v = settings.value[key];
    return v == null || v === "" ? fallback : v;
  }

  /** Digits-only E.164-ish phone for wa.me links. */
  function whatsappPhone(): string | null {
    const raw = get("company_phone");
    if (!raw) return null;
    const digits = raw.replace(/\D/g, "");
    return digits || null;
  }

  return { loaded, settings, load, get, whatsappPhone };
});