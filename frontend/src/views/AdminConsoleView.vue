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
            <li class="flex flex-col gap-2 rounded border border-slate-100 p-3 md:flex-row md:items-center md:justify-between">
              <div>
                <span>回放滞留事件</span>
                <span class="ml-2 text-xs text-slate-400">Redis Stream</span>
              </div>
              <n-button size="small" type="primary" secondary :loading="replaying" @click="replayStalled">
                回放最近失败任务
              </n-button>
            </li>
            <li class="flex flex-col gap-2 rounded border border-slate-100 p-3 md:flex-row md:items-center md:justify-between">
              <div>
                <span>导出冲突报告</span>
                <span class="ml-2 text-xs text-slate-400">CSV</span>
              </div>
              <n-button size="small" ghost :loading="exportingConflicts" @click="exportConflicts">
                下载最新报告
              </n-button>
            </li>
            <li class="flex flex-col gap-2 rounded border border-slate-100 p-3 md:flex-row md:items-center md:justify-between">
              <div>
                <span>开启 AI 审核模式</span>
                <span class="ml-2 text-xs text-slate-400">实验室</span>
              </div>
              <n-button
                size="small"
                type="success"
                :loading="aiAuditLoading"
                :secondary="aiAuditEnabled"
                @click="toggleAiAudit"
              >{{ aiAuditEnabled ? '关闭 AI 审核' : '立即开启' }}</n-button>
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
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useMessage } from 'naive-ui';

import ConflictTable from '@/components/ConflictTable.vue';
import SyncStatChart from '@/components/SyncStatChart.vue';
import SyncStatusCard from '@/components/SyncStatusCard.vue';
import { useAuthStore } from '@/stores/auth';
import { useSyncStore } from '@/stores/sync';
import { http as api } from '@/lib/http';

const authStore = useAuthStore();
const syncStore = useSyncStore();
const { runningManual } = storeToRefs(syncStore);
const isAdmin = computed(() => authStore.isAdmin);
const triggering = computed(() => runningManual.value);
const message = useMessage();

const replaying = ref(false);
const exportingConflicts = ref(false);
const aiAuditEnabled = ref(false);
const aiAuditLoading = ref(false);

async function replayStalled() {
  if (replaying.value) return;
  replaying.value = true;
  try {
    await api.post('/admin/operations/sync/replay');
    message.success('已触发回放最近失败任务');
  } catch (error) {
    console.error('回放滞留事件失败:', error);
    message.error('回放失败，请稍后重试');
  } finally {
    replaying.value = false;
  }
}

async function exportConflicts() {
  if (exportingConflicts.value) return;
  exportingConflicts.value = true;
  try {
    const response = await api.get('/admin/operations/conflicts/export', {
      responseType: 'blob',
    });
    const disposition = response.headers['content-disposition'] as string | undefined;
    let filename = `conflicts-${Date.now()}.csv`;
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
      const encoded = match?.[1] || match?.[2];
      if (encoded) {
        filename = decodeURIComponent(encoded);
      }
    }
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    message.success('冲突报告已导出');
  } catch (error) {
    console.error('导出冲突报告失败:', error);
    message.error('导出失败，请稍后再试');
  } finally {
    exportingConflicts.value = false;
  }
}

async function fetchAiAuditStatus() {
  try {
    const { data } = await api.get('/admin/operations/ai/audit-mode');
    aiAuditEnabled.value = Boolean(data?.enabled);
  } catch (error) {
    console.error('获取 AI 审核状态失败:', error);
  }
}

async function toggleAiAudit() {
  if (aiAuditLoading.value) return;
  aiAuditLoading.value = true;
  try {
    const next = !aiAuditEnabled.value;
    await api.post('/admin/operations/ai/audit-mode', { enabled: next });
    aiAuditEnabled.value = next;
    message.success(next ? 'AI 审核模式已开启' : 'AI 审核模式已关闭');
  } catch (error) {
    console.error('切换 AI 审核模式失败:', error);
    message.error('操作失败，请稍后重试');
  } finally {
    aiAuditLoading.value = false;
  }
}

watch(
  () => isAdmin.value,
  (authorized) => {
    if (authorized) {
      fetchAiAuditStatus();
    }
  },
  { immediate: true }
);

function triggerSync() {
  syncStore.triggerManualRun();
}
</script>
