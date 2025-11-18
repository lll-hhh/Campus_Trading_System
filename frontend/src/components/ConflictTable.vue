<template>
  <div class="p-4 bg-white rounded-xl shadow space-y-3">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-sm text-slate-500">冲突记录</p>
        <h2 class="text-lg font-semibold">待处理事件</h2>
      </div>
  <button class="text-sm text-slate-500" :disabled="loadingConflicts" @click="fetch">
        {{ loadingConflicts ? '刷新中...' : '刷新' }}
      </button>
    </header>

    <p v-if="!isAdmin" class="text-sm text-slate-500">仅管理员可查看冲突详情。</p>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="text-left text-slate-500 text-xs uppercase">
            <th class="py-2">表</th>
            <th class="py-2">记录</th>
            <th class="py-2">来源 → 目标</th>
            <th class="py-2">时间</th>
            <th class="py-2">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="conflicts.length === 0">
            <td colspan="5" class="py-6 text-center text-slate-400">暂无冲突，运行稳定。</td>
          </tr>
          <tr v-for="conflict in conflicts" :key="conflict.id" class="border-t">
            <td class="py-2 font-mono text-xs">{{ conflict.table }}</td>
            <td class="py-2">#{{ conflict.record_id }}</td>
            <td class="py-2">
              <span class="font-semibold">{{ conflict.source }}</span>
              <span> → </span>
              <span class="font-semibold">{{ conflict.target }}</span>
            </td>
            <td class="py-2 text-slate-500">{{ formatDate(conflict.created_at) }}</td>
            <td class="py-2">
              <div class="flex gap-2 text-xs">
                <button
                  class="rounded bg-emerald-100 px-2 py-1 text-emerald-700"
                  @click="() => resolve(conflict.id, 'source')"
                >
                  采纳来源
                </button>
                <button
                  class="rounded bg-amber-100 px-2 py-1 text-amber-700"
                  @click="() => resolve(conflict.id, 'target')"
                >
                  保留目标
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';

import { useAuthStore } from '@/stores/auth';
import { useSyncStore } from '@/stores/sync';

const authStore = useAuthStore();
const syncStore = useSyncStore();
const { conflicts, loadingConflicts } = storeToRefs(syncStore);
const isAdmin = computed(() => authStore.isAdmin);

function fetch() {
  syncStore.fetchConflicts();
}

async function resolve(id: number, strategy: 'source' | 'target') {
  await syncStore.resolveConflict(id, strategy);
}

function formatDate(input: string) {
  return new Date(input).toLocaleString();
}

onMounted(() => {
  if (isAdmin.value) {
    fetch();
  }
});
</script>
