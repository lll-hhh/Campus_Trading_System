<template>
  <div class="p-4 bg-white rounded-xl shadow space-y-4">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-sm text-slate-500">认证中心</p>
        <h2 class="text-lg font-semibold">API 网关登录</h2>
      </div>
      <button
        v-if="isAuthenticated"
        class="text-xs text-rose-500"
        type="button"
        @click="handleLogout"
      >
        退出
      </button>
    </header>

    <form v-if="!isAuthenticated" class="space-y-3" @submit.prevent="handleSubmit">
      <label class="block text-sm font-medium text-slate-600">
        邮箱
        <input
          v-model="form.email"
          type="email"
          class="mt-1 w-full rounded border px-3 py-2"
          required
        />
      </label>
      <label class="block text-sm font-medium text-slate-600">
        密码
        <input
          v-model="form.password"
          type="password"
          class="mt-1 w-full rounded border px-3 py-2"
          required
        />
      </label>
      <button
        type="submit"
        class="w-full rounded bg-indigo-600 py-2 text-white"
        :disabled="loading"
      >
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>

    <section v-else class="space-y-2 text-sm text-slate-600">
      <p>
        欢迎，
        <span class="font-semibold">{{ displayName || '用户' }}</span>
      </p>
      <p class="text-xs text-slate-500">角色：{{ roles.join('、') || '未分配' }}</p>
      <p class="text-xs text-slate-400">最近登录：{{ lastLoginLabel }}</p>
    </section>

    <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const form = reactive({ email: 'admin@campuswap.dev', password: 'campuswap' });

const { loading, error, lastLoginAt, roles, displayName } = storeToRefs(authStore);
const isAuthenticated = computed(() => authStore.isAuthenticated);
const lastLoginLabel = computed(() => lastLoginAt.value ? new Date(lastLoginAt.value).toLocaleString() : '—');

async function handleSubmit() {
  await authStore.login(form);
}

function handleLogout() {
  authStore.logout();
}
</script>
