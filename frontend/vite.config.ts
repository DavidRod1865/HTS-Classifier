/**
 * Vite configuration.
 *
 * Key things this does:
 * 1. Tailwind v4 via the Vite plugin (no PostCSS config needed)
 * 2. Path alias: "@/" maps to "./src/" so imports look clean
 * 3. Dev proxy: "/api" routes go to the FastAPI backend on port 8080
 *    This avoids CORS issues in development — the browser thinks
 *    everything comes from localhost:5173.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig(({ mode }) => ({
  plugins: [tailwindcss(), react()],

  resolve: {
    alias: {
      // "@/components/SearchBar" → "./src/components/SearchBar"
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    port: 5173,
    // Proxy API calls to the FastAPI backend in development.
    // In production, the frontend calls the backend directly via VITE_API_URL.
    proxy:
      mode === "development"
        ? {
            "/api": {
              target: "http://localhost:8080",
              changeOrigin: true,
            },
          }
        : undefined,
  },
}));