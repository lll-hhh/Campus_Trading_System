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
import { useMessage } from 'naive-ui'
import SyncTrendChart from '@/components/charts/SyncTrendChart.vue'
import ConflictPieChart from '@/components/charts/ConflictPieChart.vue'
import DatabaseStatusChart from '@/components/charts/DatabaseStatusChart.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import { http } from '@/lib/http'

const message = useMessage()
const loading = ref(false)

// 关键指标
const keyMetrics = ref([
  { label: '今日同步', value: '0', trend: 0, icon: '🔄', gradient: 'from-blue-500 to-blue-600' },
  { label: '冲突数量', value: '0', trend: 0, icon: '⚠️', gradient: 'from-red-500 to-red-600' },
  { label: '活跃用户', value: '0', trend: 0, icon: '👥', gradient: 'from-green-500 to-green-600' },
  { label: '总交易额', value: '¥0', trend: 0, icon: '💰', gradient: 'from-purple-500 to-purple-600' }
])

// 同步趋势数据
const syncTrendData = ref<any[]>([])

// 冲突数据
const conflictData = ref<any[]>([])

// 数据库状态
const databaseStatus = ref<any[]>([])

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
        label: '今日同步', 
        value: stats.today_sync_count?.toLocaleString() || '0', 
        trend: stats.sync_trend || 0, 
        icon: '🔄', 
        gradient: 'from-blue-500 to-blue-600' 
      },
      { 
        label: '冲突数量', 
        value: stats.conflict_count?.toString() || '0', 
        trend: stats.conflict_trend || 0, 
        icon: '⚠️', 
        gradient: 'from-red-500 to-red-600' 
      },
      { 
        label: '活跃用户', 
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
        gradient: 'from-purple-500 to-purple-600' 
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

// 加载同步趋势数据
const loadSyncTrends = async () => {
  try {
    // 从 daily_stats 表获取数据
    const response = await http.get('/admin/tables/daily_stats', {
      params: { page: 1, page_size: 14, sort_by: 'stat_date', sort_order: 'desc' }
    })
    const rows = response.data.items || response.data.data || []
    if (rows.length > 0) {
      syncTrendData.value = rows.map((row: any) => ({
        date: row.stat_date,
        sync_success: row.sync_success_count || 0,
        sync_conflicts: row.sync_conflict_count || 0,
        ai_requests: row.ai_request_count || 0,
        inventory_changes: row.inventory_changes ?? row.inventory_change_count ?? 0
      })).reverse()
    }
  } catch (error) {
    console.error('加载同步趋势失败:', error)
  }
}

// 加载冲突数据
const loadConflictData = async () => {
  try {
    const response = await http.get('/admin/tables/conflict_records', {
      params: { page: 1, page_size: 100 }
    })
    const rows = response.data.items || response.data.data || []
    if (rows.length > 0) {
      // 按冲突类型分组统计
      const typeCount: Record<string, number> = {}
      rows.forEach((row: any) => {
        const type = row.conflict_type || '其他'
        typeCount[type] = (typeCount[type] || 0) + 1
      })
      conflictData.value = Object.entries(typeCount).map(([type, count]) => ({
        type,
        count
      }))
    }
  } catch (error) {
    console.error('加载冲突数据失败:', error)
  }
}

// 加载数据库状态
const loadDatabaseStatus = async () => {
  try {
    const response = await http.get('/admin/database/status')
    const payload = response.data
    if (payload && typeof payload === 'object') {
      databaseStatus.value = Object.entries(payload).map(([key, info]: [string, any]) => ({
        name: info?.db_type ? `${key.toUpperCase()} (${info.db_type})` : key.toUpperCase(),
        connections: info?.active_connections ?? info?.object_count ?? 0,
        syncLatency: info?.latency ?? info?.avg_latency ?? 0,
        errorRate: Array.isArray(info?.errors) ? info.errors.length : (info?.error_count ?? 0)
      }))
    }
  } catch (error) {
    console.error('加载数据库状态失败:', error)
    // 使用默认数据
    databaseStatus.value = [
      { name: 'MySQL', connections: 0, syncLatency: 0, errorRate: 0 },
      { name: 'MariaDB', connections: 0, syncLatency: 0, errorRate: 0 },
      { name: 'PostgreSQL', connections: 0, syncLatency: 0, errorRate: 0 },
      { name: 'SQLite', connections: 0, syncLatency: 0, errorRate: 0 }
    ]
  }
}

// 同步活动热力图
const loadHeatmapData = async () => {
  try {
    const { data } = await http.get('/admin/operations/performance/heatmap', { params: { days: 7 } })
    if (Array.isArray(data?.data) && data.data.length) {
      heatmapData.value = data.data.map((item: any) => ({
        hour: Number(item.hour ?? item.Hour ?? 0),
        day: String(item.day ?? item.Day ?? 0),
        value: Number(item.value ?? 0)
      }))
      return
    }
  } catch (error) {
    console.error('加载同步热力图失败:', error)
  }
  // fallback 随机数据
  heatmapData.value = Array.from({ length: 168 }, (_, i) => ({
    hour: i % 24,
    day: Math.floor(i / 24).toString(),
    value: Math.floor(Math.random() * 100)
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
      loadSyncTrends(),
      loadConflictData(),
      loadDatabaseStatus(),
      loadHeatmapData()
    ])
    message.success('数据刷新成功')
  } catch (error) {
    message.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const exportReport = () => {
  // 构建 CSV 内容
  let csvContent = '数据分析报表\n\n'
  
  // 关键指标
  csvContent += '关键指标\n'
  csvContent += '指标,数值,趋势\n'
  keyMetrics.value.forEach(m => {
    csvContent += `${m.label},${m.value},${m.trend}%\n`
  })
  
  // 顶级卖家
  csvContent += '\n顶级卖家\n'
  csvContent += '用户名,销售量,销售额,评分\n'
  topSellers.value.forEach(s => {
    csvContent += `${s.username},${s.total_sales},¥${s.total_revenue},${s.rating}\n`
  })
  
  // 分类分析
  csvContent += '\n分类分析\n'
  csvContent += '分类,商品数,已售,售罄率,均价,总收入\n'
  categoryAnalysis.value.forEach(c => {
    csvContent += `${c.category_name},${c.item_count},${c.sold_count},${c.sell_through_rate}%,¥${c.avg_price},¥${c.total_revenue}\n`
  })
  
  // 下载
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `数据分析报表_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  
  message.success('报表导出成功')
}

onMounted(async () => {
  await refreshData()
})
</script>
