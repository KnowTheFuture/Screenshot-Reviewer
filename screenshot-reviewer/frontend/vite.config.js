import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import pkg from "./package.json";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 0,
    open: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
  },
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.js",
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
});
