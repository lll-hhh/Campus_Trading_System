<template>
  <div class="min-h-screen space-y-6 bg-gradient-to-br from-slate-50 to-blue-50 p-6">
    <!-- 页面标题 -->
    <header class="rounded-3xl bg-white p-6 shadow-lg">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-slate-900">📊 数据分析中心</h1>
          <p class="mt-2 text-sm text-slate-600">
            实时监控、趋势分析、智能洞察 - 全方位数据可视化平台
          </p>
        </div>
        <div class="flex gap-3">
          <button 
            class="rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2 text-sm text-white shadow hover:from-blue-700 hover:to-indigo-700"
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
      <!-- 同步趋势图 -->
      <article class="rounded-2xl bg-white p-6 shadow-lg">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">📈 同步趋势分析</h2>
        <SyncTrendChart :data="syncTrendData" />
      </article>

      <!-- 冲突分布图 -->
      <article class="rounded-2xl bg-white p-6 shadow-lg">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">🥧 冲突类型分布</h2>
        <ConflictPieChart :data="conflictData" />
      </article>

      <!-- 数据库状态 -->
      <article class="rounded-2xl bg-white p-6 shadow-lg lg:col-span-2">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">💾 数据库实时监控</h2>
        <DatabaseStatusChart :data="databaseStatus" />
      </article>

      <!-- 活动热力图 -->
      <article class="rounded-2xl bg-white p-6 shadow-lg lg:col-span-2">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">🔥 同步活动热力图</h2>
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
            class="flex items-center gap-3 rounded-lg border-2 border-slate-100 p-3 transition-all hover:border-blue-300 hover:bg-blue-50"
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
              <p class="text-sm font-semibold text-blue-600">{{ seller.total_sales }} 单</p>
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
                <th class="p-3 text-right text-sm font-semibold text-slate-700">商品数</th>
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
                <td class="p-3 text-right font-semibold text-blue-600">¥{{ category.total_revenue.toFixed(2) }}</td>
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
import SyncTrendChart from '@/components/charts/SyncTrendChart.vue'
import ConflictPieChart from '@/components/charts/ConflictPieChart.vue'
import DatabaseStatusChart from '@/components/charts/DatabaseStatusChart.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'

// 关键指标
const keyMetrics = ref([
  { label: '今日同步', value: '1,234', trend: 12.5, icon: '🔄', gradient: 'from-blue-500 to-blue-600' },
  { label: '冲突数量', value: '23', trend: -8.3, icon: '⚠️', gradient: 'from-red-500 to-red-600' },
  { label: '活跃用户', value: '856', trend: 15.7, icon: '👥', gradient: 'from-green-500 to-green-600' },
  { label: '总交易额', value: '¥45.2K', trend: 23.1, icon: '💰', gradient: 'from-purple-500 to-purple-600' }
])

// 同步趋势数据
const syncTrendData = ref([
  { date: '2025-01-12', sync_success: 450, sync_conflicts: 12, ai_requests: 89, inventory_changes: 234 },
  { date: '2025-01-13', sync_success: 520, sync_conflicts: 8, ai_requests: 102, inventory_changes: 267 },
  { date: '2025-01-14', sync_success: 490, sync_conflicts: 15, ai_requests: 95, inventory_changes: 221 },
  { date: '2025-01-15', sync_success: 610, sync_conflicts: 6, ai_requests: 118, inventory_changes: 289 },
  { date: '2025-01-16', sync_success: 580, sync_conflicts: 10, ai_requests: 110, inventory_changes: 256 },
  { date: '2025-01-17', sync_success: 670, sync_conflicts: 4, ai_requests: 132, inventory_changes: 312 },
  { date: '2025-01-18', sync_success: 720, sync_conflicts: 3, ai_requests: 145, inventory_changes: 345 }
])

// 冲突数据
const conflictData = ref([
  { type: '版本冲突', count: 45 },
  { type: '数据不一致', count: 23 },
  { type: '约束违反', count: 12 },
  { type: '其他', count: 8 }
])

// 数据库状态
const databaseStatus = ref([
  { name: 'MySQL', connections: 85, syncLatency: 12, errorRate: 0.5 },
  { name: 'MariaDB', connections: 78, syncLatency: 15, errorRate: 0.3 },
  { name: 'PostgreSQL', connections: 92, syncLatency: 10, errorRate: 0.2 },
  { name: 'SQLite', connections: 45, syncLatency: 5, errorRate: 0.1 }
])

// 热力图数据
const heatmapData = ref(
  Array.from({ length: 168 }, (_, i) => ({
    hour: i % 24,
    day: Math.floor(i / 24).toString(),
    value: Math.floor(Math.random() * 100)
  }))
)

// 顶级卖家
const topSellers = ref([
  { user_id: 1, username: '张同学', total_sales: 45, total_revenue: 12500, rating: 4.8 },
  { user_id: 2, username: '李老板', total_sales: 38, total_revenue: 10800, rating: 4.9 },
  { user_id: 3, username: '王大妈', total_sales: 32, total_revenue: 8900, rating: 4.7 },
  { user_id: 4, username: '赵小姐', total_sales: 28, total_revenue: 7600, rating: 4.6 },
  { user_id: 5, username: '钱先生', total_sales: 25, total_revenue: 6800, rating: 4.5 }
])

// 分类分析
const categoryAnalysis = ref([
  { category_id: 1, category_name: '电子产品', item_count: 234, sold_count: 189, sell_through_rate: 80.8, avg_price: 450, total_revenue: 85050 },
  { category_id: 2, category_name: '图书教材', item_count: 512, sold_count: 287, sell_through_rate: 56.1, avg_price: 35, total_revenue: 10045 },
  { category_id: 3, category_name: '生活用品', item_count: 178, sold_count: 98, sell_through_rate: 55.1, avg_price: 68, total_revenue: 6664 },
  { category_id: 4, category_name: '运动器材', item_count: 89, sold_count: 56, sell_through_rate: 62.9, avg_price: 120, total_revenue: 6720 },
  { category_id: 5, category_name: '服装配饰', item_count: 156, sold_count: 112, sell_through_rate: 71.8, avg_price: 85, total_revenue: 9520 }
])

const refreshData = () => {
  console.log('刷新数据...')
  // TODO: 调用API刷新数据
}

const exportReport = () => {
  console.log('导出报表...')
  // TODO: 实现报表导出功能
}

onMounted(() => {
  // TODO: 从API加载数据
})
</script>
