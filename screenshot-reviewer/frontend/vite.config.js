import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import pkg from "./package.json";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p, // keep `/api` prefix intact
        configure: (proxy, options) => {
          console.log(
            `[Vite Proxy] → ${options.target} (handling ${options.context})`
          );
        },
      },
    },
    host: "0.0.0.0",
    open: false,
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
  configure: (proxy, options) => {
    console.log(`[Vite Proxy Active] Target: ${options.target}`);
  },
});