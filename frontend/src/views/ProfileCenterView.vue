<template>
  <div class="space-y-6">
    <section class="rounded-3xl bg-white p-6 shadow">
      <h1 class="text-2xl font-semibold text-slate-900">账号中心</h1>
      <p class="mt-2 text-sm text-slate-500">
        登录后可同步云端偏好，接收 AI 定价建议与消息推送。如果是管理员，还可进入专属的运维面板。
      </p>
      <div class="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">
        <span class="rounded-full bg-slate-100 px-3 py-1">多角色支持</span>
        <span class="rounded-full bg-slate-100 px-3 py-1">JWT 鉴权</span>
        <span class="rounded-full bg-slate-100 px-3 py-1">邮箱提醒</span>
      </div>
    </section>

    <div class="grid gap-6 lg:grid-cols-2">
      <AuthPanel />
      <article class="space-y-4 rounded-2xl bg-white p-4 shadow">
        <AIChatBox />
        <section>
          <h2 class="text-base font-semibold text-slate-900">我的动态</h2>
          <ul class="mt-3 space-y-2 text-sm text-slate-600">
            <li v-if="displayName">欢迎回来，{{ displayName }}。</li>
            <li v-else>登录后即可查看最近搜索、收藏与同步任务。</li>
            <li v-if="roles.length">当前角色：{{ roles.join(' / ') }}</li>
            <li v-if="lastLoginAt">最近登录：{{ formatDate(lastLoginAt) }}</li>
          </ul>
        </section>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import AIChatBox from '@/components/AIChatBox.vue';
import AuthPanel from '@/components/AuthPanel.vue';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

const displayName = computed(() => authStore.displayName);
const roles = computed(() => authStore.roles);
const lastLoginAt = computed(() => authStore.lastLoginAt);

function formatDate(input: string | null) {
  if (!input) return '—';
  return new Date(input).toLocaleString();
}
</script>
