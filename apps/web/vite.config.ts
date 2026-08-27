/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Modules 3 and 4 are owned by another module owner and don't set CORS headers
// (they're designed as internal services). Rather than reach into their code
// (AGENTS.md §11.2), Module 1 proxies them so the browser talks same-origin.
export default defineConfig(({ mode: _mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api/academy": {
        target: "http://localhost:8004",
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/api\/academy/, "/academy"),
      },
      "/api/identity": {
        target: "http://localhost:8003",
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/api\/identity/, "/identity"),
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
}));
