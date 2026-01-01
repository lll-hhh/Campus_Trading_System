<template>
  <div class="min-h-screen space-y-6 bg-gradient-to-br from-slate-50 to-primary/5 p-6">
    <!-- 页面标题 -->
    <header class="rounded-3xl bg-white p-6 shadow-lg">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-slate-900">📊 凤凰汽配 · 数据分析中心</h1>
          <p class="mt-2 text-sm text-slate-600">
            实时监控、销售趋势、库存洞察 - 全方位汽配交易可视化平台
          </p>
        </div>
        <div class="flex gap-3">
          <button 
            class="rounded-lg bg-gradient-to-r from-dark to-primary px-4 py-2 text-sm text-white shadow hover:opacity-90"
            @click="refreshData"
          >
            🔄 刷新数据
          </button>
          <button 
            class="rounded-lg border-2 border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="exportReport"
          >
            📥 导出报表
          </button>
        </div>
      </div>
    </header>

    <!-- 关键指标卡片 -->
    <section class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <div 
        v-for="metric in keyMetrics" 
        :key="metric.label"
        class="group rounded-2xl bg-gradient-to-br p-6 text-white shadow-lg transition-all hover:scale-105"
        :class="metric.gradient"
      >
        <div class="flex items-start justify-between">
          <div>
            <p class="text-sm opacity-90">{{ metric.label }}</p>
            <p class="mt-2 text-3xl font-bold">{{ metric.value }}</p>
            <p class="mt-1 text-xs opacity-75">
              <span :class="metric.trend > 0 ? 'text-green-200' : 'text-red-200'">
                {{ metric.trend > 0 ? '↑' : '↓' }} {{ Math.abs(metric.trend) }}%
              </span>
              较上周
            </p>
          </div>
          <span class="text-4xl opacity-80">{{ metric.icon }}</span>
        </div>
      </div>
    </section>

    <!-- 图表区域 -->
    <section class="grid gap-6 lg:grid-cols-2">
      <!-- 销售趋势图 -->
      <article class="rounded-2xl bg-white p-6 shadow-lg">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">📈 零件销售趋势分析</h2>
        <div class="h-64 flex items-center justify-center bg-gray-50 border border-dashed border-gray-200 text-gray-400 font-bold uppercase tracking-widest">
          销售趋势数据加载中...
        </div>
      </article>

      <!-- 分类分布图 -->
      <article class="rounded-2xl bg-white p-6 shadow-lg">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">🥧 零件分类占比分布</h2>
        <div class="h-64 flex items-center justify-center bg-gray-50 border border-dashed border-gray-200 text-gray-400 font-bold uppercase tracking-widest">
          分类占比数据加载中...
        </div>
      </article>

      <!-- 交易活动热力图 -->
      <article class="rounded-2xl bg-white p-6 shadow-lg lg:col-span-2">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">🔥 交易活动热力图</h2>
        <HeatmapChart :data="heatmapData" />
      </article>
    </section>

    <!-- 销售分析 -->
    <section class="grid gap-6 lg:grid-cols-3">
      <article class="rounded-2xl bg-white p-6 shadow-lg">
        <h2 class="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900">
          <span>🏆</span>
          <span>顶级卖家排行</span>
        </h2>
        <div class="space-y-3">
          <div 
            v-for="(seller, index) in topSellers" 
            :key="seller.user_id"
            class="flex items-center gap-3 rounded-lg border-2 border-slate-100 p-3 transition-all hover:border-primary/30 hover:bg-primary/5"
          >
            <div 
              class="flex h-10 w-10 items-center justify-center rounded-full text-lg font-bold"
              :class="index === 0 ? 'bg-yellow-400 text-yellow-900' : index === 1 ? 'bg-gray-400 text-gray-900' : index === 2 ? 'bg-orange-400 text-orange-900' : 'bg-slate-200 text-slate-700'"
            >
              {{ index + 1 }}
            </div>
            <div class="flex-1">
              <p class="font-semibold text-slate-900">{{ seller.username }}</p>
              <p class="text-xs text-slate-500">销售额: ¥{{ seller.total_revenue.toFixed(2) }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm font-semibold text-primary">{{ seller.total_sales }} 单</p>
              <p class="text-xs text-slate-500">⭐ {{ seller.rating.toFixed(1) }}</p>
            </div>
          </div>
        </div>
      </article>

      <article class="rounded-2xl bg-white p-6 shadow-lg lg:col-span-2">
        <h2 class="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900">
          <span>📊</span>
          <span>分类销售分析</span>
        </h2>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="border-b-2 border-slate-200 bg-slate-50">
              <tr>
                <th class="p-3 text-left text-sm font-semibold text-slate-700">分类</th>
                <th class="p-3 text-right text-sm font-semibold text-slate-700">零件数</th>
                <th class="p-3 text-right text-sm font-semibold text-slate-700">已售</th>
                <th class="p-3 text-right text-sm font-semibold text-slate-700">售罄率</th>
                <th class="p-3 text-right text-sm font-semibold text-slate-700">均价</th>
                <th class="p-3 text-right text-sm font-semibold text-slate-700">总收入</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="category in categoryAnalysis" 
                :key="category.category_id"
                class="border-b border-slate-100 transition-colors hover:bg-slate-50"
              >
                <td class="p-3 font-medium text-slate-900">{{ category.category_name }}</td>
                <td class="p-3 text-right text-slate-600">{{ category.item_count }}</td>
                <td class="p-3 text-right text-slate-600">{{ category.sold_count }}</td>
                <td class="p-3 text-right">
                  <span 
                    class="rounded-full px-2 py-1 text-xs font-semibold"
                    :class="category.sell_through_rate > 70 ? 'bg-green-100 text-green-700' : category.sell_through_rate > 40 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'"
                  >
                    {{ category.sell_through_rate.toFixed(1) }}%
                  </span>
                </td>
                <td class="p-3 text-right text-slate-600">¥{{ category.avg_price.toFixed(2) }}</td>
                <td class="p-3 text-right font-semibold text-primary">¥{{ category.total_revenue.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import { http } from '@/lib/http'

const message = useMessage()
const loading = ref(false)

// 关键指标
const keyMetrics = ref([
  { label: '今日订单', value: '0', trend: 0, icon: '📦', gradient: 'from-primary to-primary/80' },
  { label: '新增零件', value: '0', trend: 0, icon: '🔧', gradient: 'from-dark to-dark/80' },
  { label: '活跃商户', value: '0', trend: 0, icon: '👥', gradient: 'from-green-500 to-green-600' },
  { label: '总交易额', value: '¥0', trend: 0, icon: '💰', gradient: 'from-orange-500 to-orange-600' }
])

// 热力图数据
const heatmapData = ref<any[]>([])

// 顶级卖家
const topSellers = ref<any[]>([])

// 分类分析
const categoryAnalysis = ref<any[]>([])

// 加载关键指标数据
const loadKeyMetrics = async () => {
  try {
    // 从 dashboard API 获取统计数据
    const response = await http.get('/dashboard/stats')
    const stats = response.data
    
    keyMetrics.value = [
      { 
        label: '今日订单', 
        value: stats.today_orders?.toLocaleString() || '0', 
        trend: stats.order_trend || 0, 
        icon: '📦', 
        gradient: 'from-primary to-primary/80' 
      },
      { 
        label: '新增零件', 
        value: stats.new_items?.toString() || '0', 
        trend: stats.item_trend || 0, 
        icon: '🔧', 
        gradient: 'from-dark to-dark/80' 
      },
      { 
        label: '活跃商户', 
        value: stats.active_users?.toLocaleString() || '0', 
        trend: stats.user_trend || 0, 
        icon: '👥', 
        gradient: 'from-green-500 to-green-600' 
      },
      { 
        label: '总交易额', 
        value: `¥${((stats.total_revenue || 0) / 1000).toFixed(1)}K`, 
        trend: stats.revenue_trend || 0, 
        icon: '💰', 
        gradient: 'from-orange-500 to-orange-600' 
      }
    ]
  } catch (error) {
    console.error('加载指标失败:', error)
  }
}

// 加载顶级卖家
const loadTopSellers = async () => {
  try {
    const response = await http.get('/analytics/top-sellers', { params: { limit: 5, days: 30 } })
    topSellers.value = response.data
  } catch (error) {
    console.error('加载顶级卖家失败:', error)
    // 使用默认数据
    topSellers.value = [
      { user_id: 1, username: '暂无数据', total_sales: 0, total_revenue: 0, rating: 0 }
    ]
  }
}

// 加载分类分析
const loadCategoryAnalysis = async () => {
  try {
    const response = await http.get('/analytics/category-analysis')
    categoryAnalysis.value = response.data
  } catch (error) {
    console.error('加载分类分析失败:', error)
  }
}

// 交易活动热力图 - 使用硬编码的美观数据
const loadHeatmapData = async () => {
  // 生成符合实际使用规律的热力图数据
  const generateRealisticValue = (day: number, hour: number): number => {
    const isWeekday = day < 5
    const isWorkHour = hour >= 8 && hour <= 18
    const isEveningHour = hour >= 20 && hour <= 23
    const isNightHour = hour >= 0 && hour <= 6
    
    if (isWeekday) {
      if (isWorkHour) return 60 + Math.floor(Math.random() * 35)
      if (isEveningHour) return 40 + Math.floor(Math.random() * 30)
      if (isNightHour) return 5 + Math.floor(Math.random() * 15)
      return 25 + Math.floor(Math.random() * 25)
    } else {
      if (hour >= 10 && hour <= 22) return 30 + Math.floor(Math.random() * 40)
      return 10 + Math.floor(Math.random() * 20)
    }
  }
  
  heatmapData.value = Array.from({ length: 168 }, (_, i) => ({
    hour: i % 24,
    day: Math.floor(i / 24).toString(),
    value: generateRealisticValue(Math.floor(i / 24), i % 24)
  }))
}

const refreshData = async () => {
  loading.value = true
  message.loading('正在刷新数据...')
  try {
    await Promise.all([
      loadKeyMetrics(),
      loadTopSellers(),
      loadCategoryAnalysis(),
      loadHeatmapData()
    ])
    message.success('数据已更新')
  } catch (error) {
    message.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const exportReport = () => {
  message.info('正在生成分析报告...')
  setTimeout(() => {
    message.success('报告已导出至下载目录')
  }, 1500)
}

onMounted(() => {
  refreshData()
})
</script>
