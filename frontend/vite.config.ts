import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const runtimePort = (globalThis as { process?: { env?: { PORT?: string } } }).process?.env?.PORT;
const previewPort = Number(runtimePort || 4173);

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
    fs: {
      strict: false,
    },
  },
  preview: {
    host: true,
    port: Number.isFinite(previewPort) ? previewPort : 4173,
    strictPort: true,
    allowedHosts: true,
  },
});
