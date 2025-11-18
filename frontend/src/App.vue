<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b bg-white/80 backdrop-blur">
      <div class="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <RouterLink class="text-2xl font-semibold text-indigo-600" to="/dashboard">CampuSwap</RouterLink>
        <nav class="flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <RouterLink
            v-for="item in visibleLinks"
            :key="item.to"
            :to="item.to"
            class="rounded-full px-4 py-1"
            :class="isActive(item.to) ? 'bg-indigo-600 text-white' : 'hover:text-indigo-600'"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="flex items-center gap-3 text-sm">
          <span v-if="authStore.isAuthenticated" class="text-slate-500">{{ authStore.displayName || '已登录用户' }}</span>
          <RouterLink v-else class="text-indigo-600" to="/profile">登录</RouterLink>
          <button
            v-if="authStore.isAuthenticated"
            class="rounded-full border border-slate-200 px-3 py-1"
            type="button"
            @click="logout"
          >
            退出
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-4 py-6">
      <router-view />
    </main>

    <footer class="border-t bg-white">
      <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4 text-xs text-slate-500">
  <p>© {{ currentYear }} CampuSwap · 多库同步与智能二手交易平台</p>
        <p>FastAPI · Vue 3 · Redis Streams · AI Pricing</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';

import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const route = useRoute();

const currentYear = new Date().getFullYear();

const links = [
  { label: '仪表盘', to: '/dashboard' },
  { label: '市场', to: '/market' },
  { label: '管理员', to: '/admin', roles: ['market_admin'] },
  { label: '账号中心', to: '/profile' }
];

const visibleLinks = computed(() =>
  links.filter((link) => {
    if (!link.roles) return true;
    return link.roles.some((role) => authStore.roles.includes(role));
  })
);

function isActive(path: string) {
  return route.path.startsWith(path);
}

function logout() {
  authStore.logout();
}

onMounted(() => {
  authStore.fetchProfile();
});
</script>
