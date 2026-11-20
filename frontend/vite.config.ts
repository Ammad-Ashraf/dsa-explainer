import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development the API runs separately (python -m dsa_explainer serve); Vite forwards /api to it.
// In production the backend serves the built app from frontend/dist itself.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: false } },
  },
  build: { outDir: "dist", sourcemap: false, chunkSizeWarningLimit: 900 },
});
