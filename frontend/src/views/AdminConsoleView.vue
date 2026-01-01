<template>
  <div class="admin-console min-h-screen bg-[#f4f4f4]">
    <!-- Header Section -->
    <div class="bg-[#2e3235] text-white py-8 mb-8">
      <div class="max-w-7xl mx-auto px-4">
        <h1 class="text-3xl font-black tracking-tighter uppercase italic">
          Admin <span class="text-primary">Console</span>
          <span class="block text-sm font-normal tracking-widest mt-1 opacity-60 italic">PHOENIX AUTO PARTS / OPERATIONS & RISK CONTROL</span>
        </h1>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 pb-12">
      <section v-if="!isAdmin" class="bg-white border-2 border-dashed border-gray-200 p-12 text-center">
        <h2 class="text-2xl font-black uppercase italic tracking-widest text-gray-400 mb-4">Access Denied</h2>
        <p class="text-sm font-bold uppercase tracking-tighter text-gray-500 mb-8">You do not have the required MARKET_ADMIN permissions.</p>
        <n-button type="primary" size="large" class="uppercase font-bold italic tracking-widest" @click="router.push('/marketplace')">
          Return to Marketplace
        </n-button>
      </section>

      <template v-else>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div class="bg-white border border-gray-200 p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              快速操作
            </h2>
            <div class="space-y-4">
              <div class="flex flex-col md:flex-row md:items-center justify-between p-4 bg-gray-50 border border-gray-100 gap-4">
                <div>
                  <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">系统维护</div>
                  <div class="text-sm font-black uppercase italic">清理系统缓存</div>
                </div>
                <n-button size="small" type="primary" secondary class="uppercase font-bold italic">
                  立即执行
                </n-button>
              </div>

              <div class="flex flex-col md:flex-row md:items-center justify-between p-4 bg-gray-50 border border-gray-100 gap-4">
                <div>
                  <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">数据备份</div>
                  <div class="text-sm font-black uppercase italic">导出全量数据 (JSON)</div>
                </div>
                <n-button size="small" ghost class="uppercase font-bold italic">
                  下载备份
                </n-button>
              </div>

              <div class="flex flex-col md:flex-row md:items-center justify-between p-4 bg-gray-50 border border-gray-100 gap-4">
                <div>
                  <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">实验室</div>
                  <div class="text-sm font-black uppercase italic">AI 智能审核模式</div>
                </div>
                <n-button
                  size="small"
                  type="success"
                  :loading="aiAuditLoading"
                  :secondary="aiAuditEnabled"
                  @click="toggleAiAudit"
                  class="uppercase font-bold italic"
                >
                  {{ aiAuditEnabled ? '禁用 AI' : '启用 AI' }}
                </n-button>
              </div>
            </div>
          </div>

          <div class="bg-[#2e3235] text-white p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              Risk Overview
            </h2>
            <ul class="space-y-4">
              <li class="flex items-start gap-3">
                <span class="text-primary font-black mt-1">»</span>
                <p class="text-xs font-bold uppercase tracking-widest opacity-60 leading-relaxed">Peak traffic detected between 18:00-22:00. Rate limiting recommended.</p>
              </li>
              <li class="flex items-start gap-3">
                <span class="text-primary font-black mt-1">»</span>
                <p class="text-xs font-bold uppercase tracking-widest opacity-60 leading-relaxed">4 High-risk transactions pending manual review.</p>
              </li>
              <li class="flex items-start gap-3">
                <span class="text-primary font-black mt-1">»</span>
                <p class="text-xs font-bold uppercase tracking-widest opacity-60 leading-relaxed">Alert system fully operational. Last check: 5m ago.</p>
              </li>
            </ul>
          </div>
        </div>

        <div class="bg-white border border-gray-200 p-8">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-black uppercase italic tracking-tighter flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              系统运行概览
            </h2>
            <n-button quaternary type="primary" @click="router.push('/admin/dashboard')" class="uppercase font-bold italic tracking-widest">
              查看完整仪表盘
            </n-button>
          </div>
          <div class="h-64 flex items-center justify-center bg-gray-50 border border-dashed border-gray-200 text-gray-400 font-bold uppercase tracking-widest">
            系统监控数据加载中...
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useMessage } from 'naive-ui';

import { useAuthStore } from '@/stores/auth';
import { http as api } from '@/lib/http';

const authStore = useAuthStore();
const router = useRouter();
const isAdmin = computed(() => authStore.isAdmin);
const message = useMessage();

const aiAuditEnabled = ref(false);
const aiAuditLoading = ref(false);

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

fetchAiAuditStatus();
</script>

<style scoped>
.admin-console {
  font-family: 'Inter', sans-serif;
}
</style>
