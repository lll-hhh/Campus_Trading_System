<template>
  <div ref="chartRef" class="h-80 w-full"></div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface DailyStat {
  date: string
  sync_success: number
  sync_conflicts: number
  ai_requests: number
  inventory_changes: number
}

const props = defineProps<{
  data: DailyStat[]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const dates = props.data.map(d => d.date.slice(5, 10)) // MM-DD格式
  const success = props.data.map(d => d.sync_success)
  const conflicts = props.data.map(d => d.sync_conflicts)
  const aiRequests = props.data.map(d => d.ai_requests)
  
  const option: echarts.EChartsOption = {
    title: {
      text: '同步趋势分析',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['同步成功', '同步冲突', 'AI请求'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    toolbox: {
      feature: {
        saveAsImage: { title: '保存为图片' },
        dataZoom: { title: { zoom: '区域缩放', back: '还原' } },
        restore: { title: '还原' }
      }
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '次数'
    },
    series: [
      {
        name: '同步成功',
        type: 'line',
        smooth: true,
        data: success,
        itemStyle: {
          color: '#10b981'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
          ])
        }
      },
      {
        name: '同步冲突',
        type: 'line',
        smooth: true,
        data: conflicts,
        itemStyle: {
          color: '#ef4444'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
          ])
        }
      },
      {
        name: 'AI请求',
        type: 'line',
        smooth: true,
        data: aiRequests,
        itemStyle: {
          color: '#8b5cf6'
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

const resizeChart = () => {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeChart)
})

watch(() => props.data, () => {
  initChart()
}, { deep: true })
</script>
