<template>
  <div class="p-4 bg-white rounded-xl shadow space-y-3">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-sm text-slate-500">统计</p>
        <h2 class="text-lg font-semibold">今日同步概览</h2>
      </div>
      <span class="text-xs text-slate-400">{{ status?.daily_stat.date ?? '—' }}</span>
    </header>
    <div ref="chartRef" class="h-64"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref } from 'vue';
import * as echarts from 'echarts/core';
import { PieChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { storeToRefs } from 'pinia';

import { useSyncStore } from '@/stores/sync';

echarts.use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const syncStore = useSyncStore();
const { status } = storeToRefs(syncStore);
const chartRef = ref<HTMLDivElement | null>(null);
let instance: echarts.ECharts | null = null;

function renderChart() {
  if (!chartRef.value) return;
  if (!instance) {
    instance = echarts.init(chartRef.value);
  }

  const success = status.value?.daily_stat.sync_success ?? 0;
  const conflicts = status.value?.daily_stat.sync_conflicts ?? 0;

  instance.setOption({
    tooltip: {
      trigger: 'item'
    },
    legend: {
      bottom: 0
    },
    series: [
      {
        name: '同步次数',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        data: [
          { value: success, name: '成功' },
          { value: conflicts, name: '冲突' }
        ]
      }
    ]
  });
}

watch(
  () => status.value?.daily_stat,
  () => {
    renderChart();
  },
  { deep: true }
);

onMounted(() => {
  renderChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (instance) {
    instance.dispose();
    instance = null;
  }
});

function handleResize() {
  instance?.resize();
}
</script>
