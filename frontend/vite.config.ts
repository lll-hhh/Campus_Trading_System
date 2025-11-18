import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import UnoCSS from "unocss/vite";

export default defineConfig({
  plugins: [vue(), UnoCSS()],
  server: {
    port: 5173,
    host: "0.0.0.0"
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  }
});
