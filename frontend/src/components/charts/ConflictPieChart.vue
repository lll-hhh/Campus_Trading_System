<template>
  <div ref="chartRef" class="h-80 w-full"></div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface ConflictData {
  type: string
  count: number
}

const props = defineProps<{
  data: ConflictData[]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const option: echarts.EChartsOption = {
    title: {
      text: '冲突类型分布',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 50
    },
    series: [
      {
        name: '冲突类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: props.data.map(item => ({
          value: item.count,
          name: item.type
        })),
        color: ['#ef4444', '#f59e0b', '#8b5cf6', '#06b6d4']
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
