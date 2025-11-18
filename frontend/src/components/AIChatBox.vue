<template>
  <div class="p-4 bg-white rounded-xl shadow space-y-3">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-sm text-slate-500">AI 助手</p>
        <h2 class="text-lg font-semibold">智能定价 & 风险提醒</h2>
      </div>
      <button class="text-xs text-indigo-600" @click="refreshInsights">刷新</button>
    </header>
    <section class="h-48 overflow-y-auto text-sm space-y-2">
      <p v-if="insights.length === 0" class="text-slate-400">暂无建议，刷新试试～</p>
      <article
        v-for="insight in insights"
        :key="insight.id"
        class="p-2 bg-slate-50 rounded border border-slate-100"
      >
        <p class="font-medium">{{ insight.title }}</p>
        <p class="text-slate-500">{{ insight.description }}</p>
        <p class="text-xs text-slate-400">{{ insight.timestamp }}</p>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface InsightCard {
  id: number;
  title: string;
  description: string;
  timestamp: string;
}

const insights = ref<InsightCard[]>([]);

function refreshInsights() {
  insights.value = [
    {
      id: Date.now(),
      title: 'AI 定价建议 · 耳机',
      description: '建议定价 120 元，较同类商品高 8%，可附带配件提升价值。',
      timestamp: new Date().toLocaleString()
    }
  ];
}
</script>
