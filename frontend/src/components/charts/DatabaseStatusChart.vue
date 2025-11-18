<template>
  <div ref="chartRef" class="h-80 w-full"></div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface DatabaseStatus {
  name: string
  connections: number
  syncLatency: number
  errorRate: number
}

const props = defineProps<{
  data: DatabaseStatus[]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const databases = props.data.map(d => d.name)
  const connections = props.data.map(d => d.connections)
  const latency = props.data.map(d => d.syncLatency)
  const errorRate = props.data.map(d => d.errorRate)
  
  const option: echarts.EChartsOption = {
    title: {
      text: '数据库状态监控',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['连接数', '同步延迟(ms)', '错误率(%)'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: databases
    },
    yAxis: [
      {
        type: 'value',
        name: '连接数',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '延迟/错误率',
        position: 'right',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '连接数',
        type: 'bar',
        data: connections,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#60a5fa' }
          ])
        }
      },
      {
        name: '同步延迟(ms)',
        type: 'line',
        yAxisIndex: 1,
        data: latency,
        itemStyle: {
          color: '#f59e0b'
        }
      },
      {
        name: '错误率(%)',
        type: 'line',
        yAxisIndex: 1,
        data: errorRate,
        itemStyle: {
          color: '#ef4444'
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
