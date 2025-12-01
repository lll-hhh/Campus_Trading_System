import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import UnoCSS from "unocss/vite";

export default defineConfig({
  plugins: [vue(), UnoCSS()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    // 👇👇👇 新增代理配置 👇👇👇
    proxy: {
      '/api/v1': {
        // 注意：在 Docker 网络中，后端服务的名字通常是 docker-compose.yml 里的服务名
        // 这里假设你的后端服务名叫 'gateway'，端口是 8000
        target: 'http://gateway:8000', 
        changeOrigin: true,
        // 如果后端接口本身就包含 /api 前缀，就不需要 rewrite
        // 如果后端接口是 /v1/auth... 而前端请求是 /api/v1/auth...，则需要去掉 /api
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
   
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  }
});
