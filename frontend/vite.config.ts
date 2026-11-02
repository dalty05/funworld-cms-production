import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    port: 5173,
    // Allow Vite to serve HMR/CSS assets on localhost:5173.
    // Do NOT restrict to a ngrok hostname — that causes
    // ERR_CONNECTION_REFUSED when the asset is requested from
    // localhost:5173.
    allowedHosts: ["local", "localhost", "127.0.0.1", ".ngrok-free.dev", ".ngrok.io"],

    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },

  build: {
    target: "es2020",
    cssCodeSplit: true,
    sourcemap: false,

    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["vue", "vue-router", "pinia", "axios"],
        },
      },
    },
  },
});