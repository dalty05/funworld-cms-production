// stores.ts
import { defineStore } from "pinia";
import { http } from "./api";

export interface CurrentUser {
  id: string;
  full_name: string;
  email: string;
  roles: string[];
  permissions: string[];
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as CurrentUser | null,
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
  },

  actions: {
    async loadFromToken() {
      const token = localStorage.getItem("fw_token");

      if (!token) {
        this.user = null;
        return;
      }

      this.loading = true;

      try {
        const { data } = await http.get("/auth/me");

        console.log("AUTH /me response:", data);

        const apiUser = data.data;

        this.user = {
          id: apiUser.id,
          full_name: apiUser.full_name,
          email: apiUser.email,
          roles: Array.isArray(apiUser.roles)
            ? apiUser.roles
            : [],
          permissions: Array.isArray(apiUser.permissions)
            ? apiUser.permissions
            : [],
        };
      } catch (error) {
        console.error("Failed to load authenticated user:", error);

        this.user = null;
        localStorage.removeItem("fw_token");
      } finally {
        this.loading = false;
      }
    },

    logout() {
      this.user = null;
      localStorage.removeItem("fw_token");
    },

    can(code: string): boolean {
      if (!this.user) {
        return false;
      }

      const permissions = this.user.permissions ?? [];

      // Exact permission
      if (permissions.includes(code)) {
        return true;
      }

      // X.view.all / X.view.own => X.view
      const base = code.includes(".")
        ? code.split(".").slice(0, -1).join(".")
        : null;

      if (base) {
        if (permissions.includes(`${base}.all`)) {
          return true;
        }

        if (permissions.includes(`${base}.own`)) {
          return true;
        }
      }

      return false;
    },
  },
});