import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import UnoCSS from "unocss/vite";

export default defineConfig({
  plugins: [vue(), UnoCSS()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    // 代理配置：Docker 环境使用 gateway 容器名
    proxy: {
      '/api/v1': {
        // Docker 内部使用 gateway 容器名
        target: 'http://gateway:8000',
        changeOrigin: true,
      },
      '/images': {
        // 代理图片请求到后端服务器
        target: 'http://gateway:8000',
        changeOrigin: true,
      }
    }
   
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  }
});
