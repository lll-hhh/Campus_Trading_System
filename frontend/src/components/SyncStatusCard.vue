<template>
  <div class="p-4 bg-white rounded-xl shadow space-y-4">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-sm text-slate-500">同步状态</p>
        <h2 class="text-lg font-semibold">多库运行概览</h2>
      </div>
      <div class="flex gap-2">
  <button class="text-sm text-slate-500" :disabled="loadingStatus" @click="handleRefresh">
          {{ loadingStatus ? '刷新中...' : '刷新' }}
        </button>
        <button
          v-if="isAdmin"
          class="text-sm rounded bg-indigo-600 px-3 py-1 text-white"
          :disabled="runningManual"
          @click="handleManualRun"
        >
          {{ runningManual ? '执行中...' : '立即同步' }}
        </button>
      </div>
    </header>

    <section class="grid gap-4 md:grid-cols-3">
      <article class="rounded border p-3">
        <p class="text-xs uppercase tracking-wide text-slate-500">目标数据库</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <span v-for="target in targets" :key="target" class="rounded-full bg-slate-100 px-3 py-1 text-xs">
            {{ target }}
          </span>
        </div>
      </article>
      <article class="rounded border p-3">
        <p class="text-xs uppercase tracking-wide text-slate-500">冲突待处理</p>
        <p class="text-2xl font-semibold text-amber-600">{{ status?.conflicts ?? 0 }}</p>
        <p class="text-xs text-slate-400">最近同步：{{ lastRunLabel }}</p>
      </article>
      <article class="rounded border p-3">
        <p class="text-xs uppercase tracking-wide text-slate-500">今日成功率</p>
        <p class="text-2xl font-semibold text-emerald-600">{{ successRate }}%</p>
        <p class="text-xs text-slate-400">成功 {{ status?.daily_stat.sync_success ?? 0 }} 次</p>
      </article>
    </section>

    <section class="grid gap-3 md:grid-cols-2">
      <article class="rounded border p-3 text-sm">
        <p>模式：{{ status?.mode ?? '加载中' }}</p>
        <p>环境：{{ status?.environment ?? '-' }}</p>
      </article>
      <article class="rounded border p-3 text-sm">
        <p>最近刷新：{{ lastUpdatedLabel }}</p>
      </article>
    </section>

    <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';

import { useAuthStore } from '@/stores/auth';
import { useSyncStore } from '@/stores/sync';

const syncStore = useSyncStore();
const authStore = useAuthStore();

const { status, loadingStatus, runningManual, lastUpdated, error } = storeToRefs(syncStore);
const targets = computed(() => status.value?.targets ?? []);
const successRate = computed(() => syncStore.successRate);
const lastRunLabel = computed(() =>
  status.value?.last_run ? new Date(status.value.last_run).toLocaleString() : '—'
);
const lastUpdatedLabel = computed(() =>
  lastUpdated.value ? new Date(lastUpdated.value).toLocaleString() : '尚未同步'
);
const isAdmin = computed(() => authStore.isAdmin);

function handleRefresh() {
  syncStore.fetchStatus();
}

function handleManualRun() {
  syncStore.triggerManualRun();
}

onMounted(() => {
  syncStore.fetchStatus();
  if (isAdmin.value) {
    syncStore.fetchConflicts();
  }
});

watch(isAdmin, (value) => {
  if (value) {
    syncStore.fetchConflicts();
  }
});
</script>
