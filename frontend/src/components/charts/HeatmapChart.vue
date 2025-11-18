<template>
  <div ref="chartRef" class="h-96 w-full"></div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface HeatmapData {
  hour: number
  day: string
  value: number
}

const props = defineProps<{
  data: HeatmapData[]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  const heatmapData = props.data.map(item => [item.hour, item.day, item.value])
  
  const option: echarts.EChartsOption = {
    title: {
      text: '同步活动热力图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 600
      }
    },
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const hour = hours[params.data[0]]
        const day = days[params.data[1]]
        const value = params.data[2]
        return `${day} ${hour}<br/>活动量: ${value}`
      }
    },
    grid: {
      height: '70%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: days,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#eef2ff', '#6366f1', '#4338ca']
      }
    },
    series: [
      {
        name: '同步活动',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: false
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
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
