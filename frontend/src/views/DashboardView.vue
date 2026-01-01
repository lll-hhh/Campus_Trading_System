<template>
  <div class="dashboard-view min-h-screen bg-[#f4f4f4]">
    <!-- Header Section -->
    <div class="bg-[#2e3235] text-white py-8 mb-8">
      <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6">
        <div>
          <h1 class="text-3xl font-black tracking-tighter uppercase italic">
            Management <span class="text-primary">Dashboard</span>
            <span class="block text-sm font-normal tracking-widest mt-1 opacity-60 italic">PHOENIX AUTO PARTS / OPERATIONS OVERVIEW</span>
          </h1>
        </div>
        <n-button type="primary" size="large" class="uppercase font-bold italic tracking-widest" :loading="loading" @click="refresh">
          Refresh Data
        </n-button>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 pb-12 space-y-8">
      <!-- Top Stats -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="bg-white border border-gray-200 p-8">
          <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-2">System Status</div>
          <div class="text-4xl font-black text-[#2e3235] italic uppercase">Operational</div>
          <div class="mt-4 text-xs font-bold text-gray-400 uppercase tracking-tighter">Database Connection: Stable</div>
        </div>
        <div class="bg-white border border-gray-200 p-8">
          <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-2">Availability</div>
          <div class="text-4xl font-black text-[#2e3235] italic uppercase">99.9%</div>
          <div class="mt-4 text-xs font-bold text-gray-400 uppercase tracking-tighter">Uptime Last 30 Days</div>
        </div>
        <div class="bg-white border border-gray-200 p-8">
          <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-2">Avg Response</div>
          <div class="text-4xl font-black text-[#2e3235] italic uppercase">12ms</div>
          <div class="mt-4 text-xs font-bold text-gray-400 uppercase tracking-tighter">Global Latency</div>
        </div>
      </div>

      <!-- Middle Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div class="bg-white border border-gray-200 p-8">
          <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
            <span class="w-2 h-6 bg-primary"></span>
            业务统计
          </h2>
          <div class="space-y-4">
            <div v-for="stat in dailyStats" :key="stat.date" class="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
              <span class="text-sm font-bold uppercase tracking-tighter text-gray-500">{{ formatDate(stat.date) }}</span>
              <div class="flex gap-4">
                <span class="text-xs font-black uppercase italic">成交: {{ stat.trade_count }}</span>
                <span class="text-xs font-black uppercase italic text-primary">咨询: {{ stat.inquiry_count }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white border border-gray-200 p-8">
          <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
            <span class="w-2 h-6 bg-primary"></span>
            系统日志
          </h2>
          <div class="space-y-4">
            <div v-for="log in systemLogs" :key="log.id" class="p-4 bg-gray-50 border border-gray-100">
              <div class="flex justify-between items-start mb-2">
                <span class="text-xs font-black uppercase italic text-primary">{{ log.status }}</span>
                <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{{ formatDate(log.started_at) }}</span>
              </div>
              <p class="text-[10px] font-bold uppercase tracking-tighter text-gray-500">操作员 ID: #{{ log.config_id ?? 'SYSTEM' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Market Snapshot -->
      <div class="bg-white border border-gray-200 p-8">
        <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
          <span class="w-2 h-6 bg-primary"></span>
          Market Snapshot
        </h2>
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b-2 border-[#2e3235]">
                <th class="py-4 text-[10px] font-black uppercase tracking-widest">Part Title</th>
                <th class="py-4 text-[10px] font-black uppercase tracking-widest">Category</th>
                <th class="py-4 text-[10px] font-black uppercase tracking-widest">Price</th>
                <th class="py-4 text-[10px] font-black uppercase tracking-widest">Status</th>
                <th class="py-4 text-[10px] font-black uppercase tracking-widest">Published</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-if="latestItems.length === 0">
                <td colspan="5" class="py-6 text-center text-slate-400">暂无数据</td>
              </tr>
              <tr v-for="item in latestItems" :key="item.id" class="border-t">
                <td class="py-2 font-medium">{{ item.title }}</td>
                <td class="py-2 text-slate-500">{{ item.category ?? '—' }}</td>
                <td class="py-2">
                  ¥{{ item.price.toFixed(2) }}
                </td>
                <td class="py-2">
                  <span class="rounded-full bg-slate-100 px-2 py-1 text-xs">{{ item.status }}</span>
                </td>
                <td class="py-2 text-slate-400">{{ formatDate(item.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';

import { useDashboardStore } from '@/stores/dashboard';

const dashboardStore = useDashboardStore();
const { dailyStats, systemLogs, latestItems, loading, error } = storeToRefs(dashboardStore);

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
