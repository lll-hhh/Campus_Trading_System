<template>
  <div class="space-y-6">
    <section class="rounded-3xl border border-amber-200 bg-amber-50 p-6 text-amber-900">
      <p class="text-xs uppercase tracking-widest">Admin Console</p>
      <h1 class="mt-2 text-3xl font-semibold">同步与风控作业区</h1>
      <p class="mt-2 text-sm text-amber-800/80">
        查看跨库状态、处理冲突、触发手动同步。该区域仅向具有 market_admin 角色的用户展示全部内容。
      </p>
    </section>

    <section v-if="!isAdmin" class="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center">
      <h2 class="text-xl font-semibold text-slate-800">你当前没有管理员权限</h2>
      <p class="mt-2 text-sm text-slate-500">请联系平台负责人开通 market_admin 角色，或者前往市场页继续浏览。</p>
      <RouterLink class="mt-4 inline-flex items-center rounded-full bg-indigo-600 px-4 py-2 text-white" to="/market">
        返回市场中心
      </RouterLink>
    </section>

    <template v-else>
      <section class="grid gap-4 xl:grid-cols-2">
        <SyncStatusCard />
        <ConflictTable />
      </section>

      <section class="grid gap-4 lg:grid-cols-2">
        <article class="rounded-2xl bg-white p-4 shadow">
          <header class="flex items-center justify-between">
            <div>
              <p class="text-xs uppercase text-slate-400">快速操作</p>
              <h3 class="text-lg font-semibold text-slate-900">常用指令</h3>
            </div>
            <button class="text-sm text-indigo-600" :disabled="triggering" @click="triggerSync">
              {{ triggering ? '执行中...' : '立即同步' }}
            </button>
          </header>
          <ul class="mt-4 space-y-3 text-sm text-slate-600">
            <li class="flex items-center justify-between rounded border border-slate-100 p-3">
              <span>回放滞留事件</span>
              <span class="text-xs text-slate-400">Redis Stream</span>
            </li>
            <li class="flex items-center justify-between rounded border border-slate-100 p-3">
              <span>导出冲突报告</span>
              <span class="text-xs text-slate-400">CSV</span>
            </li>
            <li class="flex items-center justify-between rounded border border-slate-100 p-3">
              <span>开启 AI 审核模式</span>
              <span class="text-xs text-slate-400">实验室</span>
            </li>
          </ul>
        </article>
        <article class="rounded-2xl bg-white p-4 shadow">
          <header>
            <p class="text-xs uppercase text-slate-400">策略提醒</p>
            <h3 class="text-lg font-semibold text-slate-900">风控概览</h3>
          </header>
          <ul class="mt-4 space-y-2 text-sm text-slate-600">
            <li>• 发布高峰集中在 18:00-22:00，建议开启限流。</li>
            <li>• 近两日共有 4 条高风险交易等待审核。</li>
            <li>• 邮件告警配置完整，最近一次发送 5 分钟前。</li>
          </ul>
        </article>
      </section>

      <section class="rounded-2xl bg-white p-4 shadow">
        <header class="flex items-center justify-between">
          <div>
            <p class="text-xs uppercase text-slate-400">趋势分析</p>
            <h3 class="text-lg font-semibold text-slate-900">同步走势</h3>
          </div>
          <RouterLink class="text-sm text-indigo-600" to="/dashboard">查看仪表盘</RouterLink>
        </header>
        <SyncStatChart />
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import ConflictTable from '@/components/ConflictTable.vue';
import SyncStatChart from '@/components/SyncStatChart.vue';
import SyncStatusCard from '@/components/SyncStatusCard.vue';
import { useAuthStore } from '@/stores/auth';
import { useSyncStore } from '@/stores/sync';

const authStore = useAuthStore();
const syncStore = useSyncStore();
const { runningManual } = storeToRefs(syncStore);
const isAdmin = computed(() => authStore.isAdmin);
const triggering = computed(() => runningManual.value);

function triggerSync() {
  syncStore.triggerManualRun();
}
</script>
