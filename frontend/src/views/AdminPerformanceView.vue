<template>
  <div class="admin-performance-container">
    <!-- 顶部标题栏 -->
    <div class="header-bar">
      <h1>📊 数据库性能监控中心</h1>
      <n-space>
        <n-button type="primary" @click="refreshAllData">
          🔄 刷新所有数据
        </n-button>
        <n-button @click="toggleAutoRefresh">
          {{ autoRefresh ? '⏸️ 暂停自动刷新' : '▶️ 启动自动刷新' }}
        </n-button>
      </n-space>
    </div>

    <!-- 实时性能指标卡片 -->
    <div class="metrics-grid">
      <n-card title="🔥 系统实时状态" :bordered="false" class="metric-card">
        <n-statistic label="总用户数" :value="stats.totalUsers">
          <template #suffix>人</template>
        </n-statistic>
        <n-divider />
        <n-statistic label="在线用户" :value="stats.onlineUsers" class="text-success">
          <template #suffix>人</template>
        </n-statistic>
      </n-card>

      <n-card title="📦 商品统计" :bordered="false" class="metric-card">
        <n-statistic label="在售商品" :value="stats.availableItems">
          <template #suffix>件</template>
        </n-statistic>
        <n-divider />
        <n-statistic label="今日新增" :value="stats.todayNewItems" class="text-primary">
          <template #suffix>件</template>
        </n-statistic>
      </n-card>

      <n-card title="💰 交易数据" :bordered="false" class="metric-card">
        <n-statistic label="总交易额" :value="stats.totalTransactionAmount">
          <template #prefix>¥</template>
        </n-statistic>
        <n-divider />
        <n-statistic label="今日成交" :value="stats.todayCompletedTransactions" class="text-success">
          <template #suffix>笔</template>
        </n-statistic>
      </n-card>

      <n-card title="⚡ 数据库性能" :bordered="false" class="metric-card">
        <n-statistic label="平均查询时间" :value="stats.avgQueryTime">
          <template #suffix>ms</template>
        </n-statistic>
        <n-divider />
        <n-statistic label="QPS" :value="stats.qps" class="text-warning">
          <template #suffix>次/秒</template>
        </n-statistic>
      </n-card>
    </div>

    <!-- 四库同步状态 -->
    <n-card title="🔄 四数据库同步状态" class="sync-status-card">
      <n-table :bordered="false" :single-line="false">
        <thead>
          <tr>
            <th>数据库</th>
            <th>连接状态</th>
            <th>延迟</th>
            <th>记录数</th>
            <th>同步版本</th>
            <th>最后同步</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="db in databases" :key="db.name">
            <td><strong>{{ db.name }}</strong></td>
            <td>
              <n-tag :type="db.status === 'online' ? 'success' : 'error'" size="small">
                {{ db.status === 'online' ? '✅ 在线' : '❌ 离线' }}
              </n-tag>
            </td>
            <td>{{ db.latency }}ms</td>
            <td>{{ db.recordCount.toLocaleString() }}</td>
            <td>v{{ db.syncVersion }}</td>
            <td>{{ db.lastSync }}</td>
            <td>
              <n-space>
                <n-button size="small" @click="syncDatabase(db.name)">同步</n-button>
                <n-button size="small" type="primary" @click="viewDbDetails(db.name)">详情</n-button>
              </n-space>
            </td>
          </tr>
        </tbody>
      </n-table>
    </n-card>

    <!-- 查询性能分析 -->
    <n-card title="📈 慢查询分析 (Top 10)" class="query-analysis-card">
      <n-table :bordered="false" :single-line="false">
        <thead>
          <tr>
            <th>查询ID</th>
            <th>SQL语句</th>
            <th>执行次数</th>
            <th>平均耗时</th>
            <th>最大耗时</th>
            <th>影响行数</th>
            <th>优化建议</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(query, idx) in slowQueries" :key="idx">
            <td>{{ query.id }}</td>
            <td class="sql-query">{{ query.sql }}</td>
            <td>{{ query.count }}</td>
            <td>
              <n-tag :type="query.avgTime > 100 ? 'error' : 'warning'" size="small">
                {{ query.avgTime }}ms
              </n-tag>
            </td>
            <td>{{ query.maxTime }}ms</td>
            <td>{{ query.rows }}</td>
            <td>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-button size="tiny" type="info">💡 查看</n-button>
                </template>
                {{ query.suggestion }}
              </n-tooltip>
            </td>
          </tr>
        </tbody>
      </n-table>
    </n-card>

    <!-- 数据库连接池状态 -->
    <div class="pool-grid">
      <n-card title="🏊 MySQL 连接池" size="small">
        <n-progress type="line" :percentage="mysqlPool.usage" :color="getPoolColor(mysqlPool.usage)" />
        <n-descriptions :column="2" size="small" style="margin-top: 10px;">
          <n-descriptions-item label="活跃连接">{{ mysqlPool.active }}/{{ mysqlPool.max }}</n-descriptions-item>
          <n-descriptions-item label="空闲连接">{{ mysqlPool.idle }}</n-descriptions-item>
          <n-descriptions-item label="等待队列">{{ mysqlPool.waiting }}</n-descriptions-item>
          <n-descriptions-item label="超时次数">{{ mysqlPool.timeouts }}</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card title="🏊 PostgreSQL 连接池" size="small">
        <n-progress type="line" :percentage="postgresPool.usage" :color="getPoolColor(postgresPool.usage)" />
        <n-descriptions :column="2" size="small" style="margin-top: 10px;">
          <n-descriptions-item label="活跃连接">{{ postgresPool.active }}/{{ postgresPool.max }}</n-descriptions-item>
          <n-descriptions-item label="空闲连接">{{ postgresPool.idle }}</n-descriptions-item>
          <n-descriptions-item label="等待队列">{{ postgresPool.waiting }}</n-descriptions-item>
          <n-descriptions-item label="超时次数">{{ postgresPool.timeouts }}</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card title="🏊 MariaDB 连接池" size="small">
        <n-progress type="line" :percentage="mariadbPool.usage" :color="getPoolColor(mariadbPool.usage)" />
        <n-descriptions :column="2" size="small" style="margin-top: 10px;">
          <n-descriptions-item label="活跃连接">{{ mariadbPool.active }}/{{ mariadbPool.max }}</n-descriptions-item>
          <n-descriptions-item label="空闲连接">{{ mariadbPool.idle }}</n-descriptions-item>
          <n-descriptions-item label="等待队列">{{ mariadbPool.waiting }}</n-descriptions-item>
          <n-descriptions-item label="超时次数">{{ mariadbPool.timeouts }}</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card title="🏊 SQLite 连接" size="small">
        <n-progress type="line" :percentage="sqlitePool.usage" :color="getPoolColor(sqlitePool.usage)" />
        <n-descriptions :column="2" size="small" style="margin-top: 10px;">
          <n-descriptions-item label="活跃连接">{{ sqlitePool.active }}/{{ sqlitePool.max }}</n-descriptions-item>
          <n-descriptions-item label="锁等待">{{ sqlitePool.waiting }}</n-descriptions-item>
          <n-descriptions-item label="写入队列">{{ sqlitePool.writeQueue }}</n-descriptions-item>
          <n-descriptions-item label="WAL大小">{{ sqlitePool.walSize }}MB</n-descriptions-item>
        </n-descriptions>
      </n-card>
    </div>

    <!-- 实时查询监控 -->
    <n-card title="🔍 实时查询监控" class="realtime-queries-card">
      <n-space vertical>
        <n-alert type="info" title="正在执行的查询" :bordered="false">
          当前有 <strong>{{ runningQueries.length }}</strong> 个查询正在执行
        </n-alert>
        <n-table :bordered="false" size="small" max-height="300px">
          <thead>
            <tr>
              <th>数据库</th>
              <th>查询</th>
              <th>状态</th>
              <th>耗时</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(q, idx) in runningQueries" :key="idx">
              <td><n-tag size="small">{{ q.database }}</n-tag></td>
              <td class="sql-query">{{ q.query }}</td>
              <td>
                <n-spin size="small" v-if="q.status === 'running'" />
                <span v-else>{{ q.status }}</span>
              </td>
              <td>{{ q.duration }}ms</td>
              <td>
                <n-button size="tiny" type="error" @click="killQuery(q.id)">终止</n-button>
              </td>
            </tr>
          </tbody>
        </n-table>
      </n-space>
    </n-card>

    <!-- 系统健康度仪表盘 -->
    <div class="health-dashboard">
      <n-card title="🏥 系统健康度评分">
        <div class="health-score">
          <n-progress
            type="dashboard"
            :percentage="systemHealth"
            :color="systemHealth > 80 ? '#18a058' : systemHealth > 60 ? '#f0a020' : '#d03050'"
            :rail-color="'rgba(128, 128, 128, 0.2)'"
          >
            <div class="health-label">
              <div class="score">{{ systemHealth }}</div>
              <div class="text">{{ getHealthLabel(systemHealth) }}</div>
            </div>
          </n-progress>
        </div>
        <n-divider />
        <n-space vertical>
          <div class="health-item">
            <span>数据库连接状态</span>
            <n-tag :type="healthMetrics.dbConnection > 90 ? 'success' : 'warning'">
              {{ healthMetrics.dbConnection }}%
            </n-tag>
          </div>
          <div class="health-item">
            <span>查询响应速度</span>
            <n-tag :type="healthMetrics.querySpeed > 90 ? 'success' : 'warning'">
              {{ healthMetrics.querySpeed }}%
            </n-tag>
          </div>
          <div class="health-item">
            <span>同步一致性</span>
            <n-tag :type="healthMetrics.syncConsistency > 95 ? 'success' : 'error'">
              {{ healthMetrics.syncConsistency }}%
            </n-tag>
          </div>
          <div class="health-item">
            <span>系统资源使用</span>
            <n-tag :type="healthMetrics.resourceUsage < 80 ? 'success' : 'warning'">
              {{ healthMetrics.resourceUsage }}%
            </n-tag>
          </div>
        </n-space>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NCard, NStatistic, NDivider, NTable, NTag, NButton, NSpace, NProgress, NDescriptions, NDescriptionsItem, NTooltip, NAlert, NSpin, useMessage } from 'naive-ui'

const message = useMessage()

// 统计数据
const stats = ref({
  totalUsers: 200,
  onlineUsers: 45,
  availableItems: 437,
  todayNewItems: 23,
  totalTransactionAmount: 156780.5,
  todayCompletedTransactions: 18,
  avgQueryTime: 12.5,
  qps: 342
})

// 数据库状态
const databases = ref([
  {
    name: 'MySQL',
    status: 'online',
    latency: 8,
    recordCount: 3247,
    syncVersion: 1523,
    lastSync: '2秒前'
  },
  {
    name: 'PostgreSQL',
    status: 'online',
    latency: 12,
    recordCount: 3245,
    syncVersion: 1522,
    lastSync: '5秒前'
  },
  {
    name: 'MariaDB',
    status: 'online',
    latency: 10,
    recordCount: 3247,
    syncVersion: 1523,
    lastSync: '3秒前'
  },
  {
    name: 'SQLite',
    status: 'online',
    latency: 3,
    recordCount: 3246,
    syncVersion: 1523,
    lastSync: '1秒前'
  }
])

// 慢查询
const slowQueries = ref([
  {
    id: 'Q1001',
    sql: 'SELECT * FROM items WHERE status = "available" ORDER BY created_at DESC LIMIT 1000',
    count: 1523,
    avgTime: 145,
    maxTime: 320,
    rows: 1000,
    suggestion: '建议: 添加 (status, created_at) 复合索引'
  },
  {
    id: 'Q1002',
    sql: 'SELECT u.*, COUNT(i.id) FROM users u LEFT JOIN items i ON u.id = i.seller_id GROUP BY u.id',
    count: 892,
    avgTime: 89,
    maxTime: 178,
    rows: 200,
    suggestion: '建议: 使用物化视图缓存聚合结果'
  },
  {
    id: 'Q1003',
    sql: 'UPDATE items SET view_count = view_count + 1 WHERE id = ?',
    count: 8943,
    avgTime: 5,
    maxTime: 45,
    rows: 1,
    suggestion: '建议: 使用 Redis 缓存浏览计数，批量写入数据库'
  },
  {
    id: 'Q1004',
    sql: 'SELECT * FROM transactions WHERE buyer_id = ? OR seller_id = ?',
    count: 2341,
    avgTime: 67,
    maxTime: 156,
    rows: 50,
    suggestion: '建议: 分别查询后合并，或使用 UNION'
  },
  {
    id: 'Q1005',
    sql: 'SELECT item_id, COUNT(*) FROM comments GROUP BY item_id HAVING COUNT(*) > 10',
    count: 456,
    avgTime: 123,
    maxTime: 289,
    rows: 87,
    suggestion: '建议: 添加 item_id 索引，考虑分区表'
  }
])

// 连接池状态
const mysqlPool = ref({
  active: 8,
  idle: 12,
  max: 20,
  waiting: 0,
  timeouts: 3,
  usage: 40
})

const postgresPool = ref({
  active: 6,
  idle: 14,
  max: 20,
  waiting: 0,
  timeouts: 1,
  usage: 30
})

const mariadbPool = ref({
  active: 7,
  idle: 13,
  max: 20,
  waiting: 0,
  timeouts: 2,
  usage: 35
})

const sqlitePool = ref({
  active: 1,
  idle: 0,
  max: 1,
  waiting: 0,
  writeQueue: 5,
  walSize: 12.3,
  usage: 100
})

// 实时查询
const runningQueries = ref([
  {
    id: 'RQ001',
    database: 'MySQL',
    query: 'SELECT * FROM items WHERE category_id = 2 AND price < 100',
    status: 'running',
    duration: 156
  },
  {
    id: 'RQ002',
    database: 'PostgreSQL',
    query: 'INSERT INTO audit_logs (user_id, table_name, operation) VALUES (...)',
    status: 'running',
    duration: 23
  }
])

// 健康度指标
const healthMetrics = ref({
  dbConnection: 98,
  querySpeed: 92,
  syncConsistency: 96,
  resourceUsage: 65
})

const systemHealth = computed(() => {
  const metrics = healthMetrics.value
  return Math.round(
    (metrics.dbConnection * 0.3 +
    metrics.querySpeed * 0.3 +
    metrics.syncConsistency * 0.3 +
    (100 - metrics.resourceUsage) * 0.1)
  )
})

// 自动刷新
const autoRefresh = ref(false)
let refreshInterval: number | null = null

const refreshAllData = () => {
  // 模拟数据刷新
  stats.value.onlineUsers = Math.floor(Math.random() * 20) + 35
  stats.value.todayNewItems = Math.floor(Math.random() * 10) + 15
  stats.value.todayCompletedTransactions = Math.floor(Math.random() * 10) + 10
  stats.value.avgQueryTime = (Math.random() * 10 + 8).toFixed(1) as any
  stats.value.qps = Math.floor(Math.random() * 100) + 300
  
  databases.value.forEach(db => {
    db.latency = Math.floor(Math.random() * 10) + 3
    db.recordCount += Math.floor(Math.random() * 5)
  })
  
  message.success('数据已刷新')
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    refreshInterval = window.setInterval(refreshAllData, 5000)
    message.info('已启动自动刷新（每5秒）')
  } else {
    if (refreshInterval) clearInterval(refreshInterval)
    message.info('已停止自动刷新')
  }
}

const getPoolColor = (usage: number) => {
  if (usage < 60) return '#18a058'
  if (usage < 80) return '#f0a020'
  return '#d03050'
}

const getHealthLabel = (score: number) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '一般'
  if (score >= 60) return '较差'
  return '危险'
}

const syncDatabase = (dbName: string) => {
  message.loading(`正在同步 ${dbName}...`)
  setTimeout(() => {
    message.success(`${dbName} 同步完成`)
  }, 1500)
}

const viewDbDetails = (dbName: string) => {
  message.info(`查看 ${dbName} 详细信息`)
}

const killQuery = (queryId: string) => {
  message.warning(`终止查询 ${queryId}`)
  runningQueries.value = runningQueries.value.filter(q => q.id !== queryId)
}

onMounted(() => {
  refreshAllData()
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.admin-performance-container {
  padding: 20px;
  background: #f5f5f5;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-bar h1 {
  margin: 0;
  font-size: 24px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.metric-card {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.text-success {
  color: #18a058;
}

.text-primary {
  color: #2080f0;
}

.text-warning {
  color: #f0a020;
}

.sync-status-card,
.query-analysis-card,
.realtime-queries-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.sql-query {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.health-dashboard {
  margin-top: 20px;
}

.health-score {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.health-label {
  text-align: center;
}

.health-label .score {
  font-size: 32px;
  font-weight: bold;
}

.health-label .text {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}
</style>
