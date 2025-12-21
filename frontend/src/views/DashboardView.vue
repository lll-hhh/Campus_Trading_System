<template>
  <div class="space-y-6">
    <section class="rounded-3xl bg-white p-6 shadow">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-widest text-slate-400">campus-wide ops</p>
          <h1 class="text-3xl font-semibold text-slate-900">多数据库同步仪表盘</h1>
          <p class="mt-2 text-sm text-slate-500">
            总览跨库同步、冲突与市场动向。PC 与移动端均可实时掌握最新数据。
          </p>
        </div>
        <button class="rounded-full bg-indigo-600 px-4 py-2 text-sm text-white" :disabled="loading" @click="refresh">
          {{ loading ? '刷新中...' : '刷新数据' }}
        </button>
      </div>
    </section>

    <section class="grid gap-4 lg:grid-cols-[2fr,1fr]">
      <SyncStatusCard />
      <article class="space-y-3 rounded-2xl bg-white p-4 shadow">
        <h2 class="text-lg font-semibold text-slate-900">模式速览</h2>
        <ul class="space-y-2 text-sm text-slate-600">
          <li>• 实时同步任务保持 100% 完成率。</li>
          <li>• 大屏模式展示冲突趋势与 AI 建议。</li>
          <li>• 移动端推送异常摘要，便于随时处理。</li>
        </ul>
      </article>
    </section>

    <section class="grid gap-4 xl:grid-cols-2">
      <article class="space-y-3 rounded-2xl bg-white p-4 shadow">
        <header class="flex items-center justify-between">
          <div>
            <p class="text-xs uppercase text-slate-400">最近 7 天</p>
            <h2 class="text-lg font-semibold text-slate-900">每日统计</h2>
          </div>
          <span class="text-xs text-slate-500">{{ dailyStats.length }} 条记录</span>
        </header>
        <ul class="space-y-2 text-sm text-slate-600">
          <li v-for="stat in dailyStats" :key="stat.date" class="flex items-center justify-between border-b border-slate-100 pb-1">
            <span>{{ formatDate(stat.date) }}</span>
            <span>成功 {{ stat.sync_success }} · 冲突 {{ stat.sync_conflicts }}</span>
          </li>
        </ul>
      </article>
      <article class="space-y-3 rounded-2xl bg-white p-4 shadow">
        <header>
          <p class="text-xs uppercase text-slate-400">同步日志</p>
          <h2 class="text-lg font-semibold text-slate-900">最新任务</h2>
        </header>
        <ul class="space-y-2 text-sm text-slate-600">
          <li v-for="log in syncLogs" :key="log.id" class="rounded border border-slate-100 p-2">
            <div class="flex items-center justify-between">
              <span class="font-medium">{{ log.status }}</span>
              <span class="text-xs text-slate-400">{{ formatDate(log.started_at) }}</span>
            </div>
            <p class="text-xs text-slate-400">配置 #{{ log.config_id ?? '—' }}</p>
          </li>
        </ul>
      </article>
    </section>

    <section class="grid gap-4 xl:grid-cols-2">
      <SyncStatChart />
      <ConflictTable />
    </section>

    <section class="rounded-2xl bg-white p-4 shadow">
      <header class="flex items-center justify-between">
        <div>
          <p class="text-xs uppercase text-slate-400">最新上架</p>
          <h2 class="text-lg font-semibold text-slate-900">市场快照</h2>
        </div>
        <button class="text-xs text-slate-500" :disabled="loading" @click="refresh">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </header>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="text-left text-xs uppercase text-slate-500">
              <th class="py-2">标题</th>
              <th class="py-2">分类</th>
              <th class="py-2">价格</th>
              <th class="py-2">状态</th>
              <th class="py-2">时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="latestItems.length === 0">
              <td colspan="5" class="py-6 text-center text-slate-400">暂无数据</td>
            </tr>
            <tr v-for="item in latestItems" :key="item.id" class="border-t">
              <td class="py-2 font-medium">{{ item.title }}</td>
              <td class="py-2 text-slate-500">{{ item.category ?? '—' }}</td>
              <td class="py-2">
                {{ item.price.toFixed(2) }} {{ item.currency }}
              </td>
              <td class="py-2">
                <span class="rounded-full bg-slate-100 px-2 py-1 text-xs">{{ item.status }}</span>
              </td>
              <td class="py-2 text-slate-500">{{ formatDate(item.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';

import ConflictTable from '@/components/ConflictTable.vue';
import SyncStatChart from '@/components/SyncStatChart.vue';
import SyncStatusCard from '@/components/SyncStatusCard.vue';
import { useDashboardStore } from '@/stores/dashboard';

const dashboardStore = useDashboardStore();
const { dailyStats, syncLogs, latestItems, loading, error } = storeToRefs(dashboardStore);

function refresh() {
  dashboardStore.refreshAll();
}

function formatDate(input: string | null) {
  if (!input) return '—';
  return new Date(input).toLocaleString();
}

onMounted(() => {
  dashboardStore.refreshAll();
});
</script>
