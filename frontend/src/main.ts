// // main.ts
// import { createApp } from "vue";
// import { createPinia } from "pinia";
// import App from "./App.vue";
// import router from "./router";
// import "./styles/base.css";

// const app = createApp(App);
// app.use(createPinia());
// app.use(router);
// app.mount("#app");



 // main.ts
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/base.css";
import { useSettingsStore } from "./stores/settings.ts";

async function bootstrap() {
  const app = createApp(App);
  const pinia = createPinia();

  // Initialize Pinia before the router so route guards can access stores.
  app.use(pinia);
  app.use(router);

  // Wait for the initial route and its authentication guards.
  await router.isReady();

  useSettingsStore(pinia).load();


  app.mount("#app");
}

bootstrap().catch((error) => {
  console.error("Application initialization failed:", error);
});



// second version MagicString.ts

// import { createApp } from "vue";
// import { createPinia } from "pinia";
// import App from "./App.vue";
// import router from "./router";
// import "./styles/base.css";
// import { http } from "./api";

// const app = createApp(App);
// app.use(createPinia());
// app.use(router);

// // ─── Analytics: track every route change ────────────────────────────
// function getSessionId(): string {
//   let id = localStorage.getItem("fw_sid");
//   if (!id) {
//     id = crypto.randomUUID();
//     localStorage.setItem("fw_sid", id);
//   }
//   return id;
// }

// router.afterEach((to) => {
//   // Skip admin routes
//   if (to.path.startsWith("/admin")) return;

//   // Debounce: don't fire if the same route just fired 1s ago
//   const now = Date.now();
//   const last = Number(localStorage.getItem("fw_last_track") || 0);
//   if (now - last < 1000) return;
//   localStorage.setItem("fw_last_track", String(now));

//   http.post("/track", {
//     session_id: getSessionId(),
//     path: to.fullPath,
//     referrer: document.referrer || null,
//   }).catch(() => {});
// });

// app.mount("#app");


