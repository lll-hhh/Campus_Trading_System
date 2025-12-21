import { createApp } from 'vue';
import { createPinia } from 'pinia';
import naive from 'naive-ui';

import App from './App.vue';
import router from './router';

import 'uno.css';

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);
app.use(router);
app.use(naive);

// 初始化 auth store 的 storage 监听器
import { useAuthStore } from './stores/auth';
const authStore = useAuthStore();
authStore.initStorageListener();

app.mount('#app');
