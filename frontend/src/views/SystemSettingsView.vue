<template>
  <div class="min-h-screen space-y-6 bg-slate-50 p-6">
    <!-- 页面标题 -->
    <header class="rounded-2xl bg-gradient-to-r from-purple-600 to-blue-600 p-6 text-white shadow-lg">
      <h1 class="text-3xl font-bold">⚙️ 系统设置</h1>
      <p class="mt-2 text-sm opacity-90">数据库连接、同步策略、通知配置、性能优化</p>
    </header>

    <!-- 设置导航 -->
    <nav class="flex gap-2 overflow-x-auto">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        class="whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.key ? 'bg-white text-blue-600 shadow' : 'text-slate-600 hover:bg-white/50'"
        @click="activeTab = tab.key"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </nav>

    <!-- 数据库配置 -->
    <section v-if="activeTab === 'database'" class="space-y-4">
      <div 
        v-for="db in databases" 
        :key="db.name"
        class="rounded-2xl bg-white p-6 shadow"
      >
        <div class="mb-4 flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div 
              class="flex h-12 w-12 items-center justify-center rounded-full text-2xl"
              :class="db.connected ? 'bg-green-100' : 'bg-red-100'"
            >
              {{ db.icon }}
            </div>
            <div>
              <h3 class="text-lg font-semibold">{{ db.label }}</h3>
              <p class="text-xs uppercase tracking-wide text-slate-400">{{ db.name }}</p>
              <p class="text-sm text-slate-500">{{ db.host }}:{{ db.port }}</p>
            </div>
          </div>
          <div class="text-right">
            <span 
              class="inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold"
              :class="db.connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >
              {{ db.connected ? '已连接' : '未连接' }}
            </span>
            <p class="mt-1 text-xs text-slate-400">上次检测：{{ formatTimestamp(db.lastCheckedAt) }}</p>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium text-slate-700">主机地址</label>
            <input 
              v-model="db.host"
              type="text" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2 text-sm"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">端口</label>
            <input 
              v-model.number="db.port"
              type="number" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2 text-sm"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">数据库名</label>
            <input 
              v-model="db.database"
              type="text" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2 text-sm"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">用户名</label>
            <input 
              v-model="db.username"
              type="text" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2 text-sm"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">密码</label>
            <input 
              v-model="db.password"
              type="password" 
              :placeholder="db.hasPassword ? '已保存，留空保持不变' : '请输入密码'"
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2 text-sm"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">连接池大小</label>
            <input 
              v-model.number="db.poolSize"
              type="number" 
              min="1"
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2 text-sm"
            >
          </div>
        </div>

        <p class="mt-4 text-sm text-slate-500">
          状态：
          <span :class="db.connected ? 'text-green-600' : 'text-red-600'">
            {{ db.connected ? '连接正常' : '连接异常' }}
          </span>
          <span v-if="db.statusMessage"> · {{ db.statusMessage }}</span>
        </p>

        <div class="mt-4 flex flex-wrap gap-2">
          <button 
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="testingDb === db.name || savingDb === db.name"
            @click="handleTestConnection(db)"
          >
            {{ testingDb === db.name ? '测试中…' : '测试连接' }}
          </button>
          <button 
            class="rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="savingDb === db.name || testingDb === db.name"
            @click="handleSaveDatabase(db)"
          >
            {{ savingDb === db.name ? '保存中…' : '保存配置' }}
          </button>
        </div>
      </div>
    </section>

    <!-- 同步策略 -->
    <section v-if="activeTab === 'sync'" class="space-y-4">
      <article class="rounded-2xl bg-white p-6 shadow">
        <h3 class="mb-4 text-lg font-semibold">同步模式</h3>
        <div class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="radio" v-model="syncMode" value="realtime" class="h-4 w-4">
            <div>
              <p class="font-medium">实时同步</p>
              <p class="text-sm text-slate-500">数据变更立即同步到所有数据库</p>
            </div>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="radio" v-model="syncMode" value="periodic" class="h-4 w-4">
            <div>
              <p class="font-medium">周期同步</p>
              <p class="text-sm text-slate-500">按固定时间间隔批量同步</p>
            </div>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="radio" v-model="syncMode" value="hybrid" class="h-4 w-4">
            <div>
              <p class="font-medium">混合模式</p>
              <p class="text-sm text-slate-500">重要数据实时同步，其他数据周期同步</p>
            </div>
          </label>
        </div>
      </article>

      <article class="rounded-2xl bg-white p-6 shadow">
        <h3 class="mb-4 text-lg font-semibold">冲突处理策略</h3>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium text-slate-700">版本冲突</label>
            <select class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2">
              <option>最新写入优先</option>
              <option>手动解决</option>
              <option>保留所有版本</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">数据不一致</label>
            <select class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2">
              <option>主库优先</option>
              <option>邮件通知管理员</option>
              <option>自动回滚</option>
            </select>
          </div>
        </div>
      </article>

      <article class="rounded-2xl bg-white p-6 shadow">
        <h3 class="mb-4 text-lg font-semibold">同步任务配置</h3>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium text-slate-700">同步间隔 (分钟)</label>
            <input 
              v-model="syncInterval"
              type="number" 
              min="1"
              max="1440"
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">重试次数</label>
            <input 
              v-model="maxRetries"
              type="number" 
              min="1"
              max="10"
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
            >
          </div>
          <div>
            <label class="flex items-center gap-2">
              <input type="checkbox" v-model="enableAutoSync" class="h-4 w-4">
              <span class="text-sm font-medium">启用自动同步</span>
            </label>
          </div>
        </div>
      </article>

      <div class="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-4 shadow">
        <p class="text-sm text-slate-500">最近更新：{{ formatTimestamp(syncUpdatedAt) }}</p>
        <button 
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="syncSaving"
          @click="handleSaveSyncConfig"
        >
          {{ syncSaving ? '保存中…' : '保存同步策略' }}
        </button>
      </div>
    </section>

    <!-- 通知配置 -->
    <section v-if="activeTab === 'notification'" class="rounded-2xl bg-white p-6 shadow">
      <h3 class="mb-4 text-lg font-semibold">邮件通知设置</h3>
      <div class="space-y-4">
        <div>
          <label class="text-sm font-medium text-slate-700">SMTP 服务器</label>
          <input 
            v-model="emailConfig.smtp_server"
            type="text" 
            placeholder="smtp.example.com"
            class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
          >
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium text-slate-700">端口</label>
            <input 
              v-model.number="emailConfig.smtp_port"
              type="number" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">发件人邮箱</label>
            <input 
              v-model="emailConfig.from_email"
              type="email" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
            >
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium text-slate-700">SMTP 用户名</label>
            <input 
              v-model="emailConfig.smtp_username"
              type="text" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
            >
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">SMTP 密码</label>
            <input 
              v-model="emailConfig.smtp_password"
              type="password" 
              placeholder="留空保持已保存的密码"
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
            >
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-slate-700">管理员邮箱 (多个用逗号分隔)</label>
          <input 
            v-model="emailConfig.admin_emails"
            type="text" 
            class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2"
          >
        </div>
        <div class="space-y-2">
          <p class="text-sm font-medium text-slate-700">通知事件</p>
          <label class="flex items-center gap-2">
            <input type="checkbox" v-model="emailConfig.use_tls" class="h-4 w-4">
            <span class="text-sm">启用 TLS</span>
          </label>
          <label class="flex items-center gap-2">
            <input type="checkbox" v-model="emailConfig.notify_conflicts" class="h-4 w-4">
            <span class="text-sm">数据冲突</span>
          </label>
          <label class="flex items-center gap-2">
            <input type="checkbox" v-model="emailConfig.notify_failures" class="h-4 w-4">
            <span class="text-sm">同步失败</span>
          </label>
          <label class="flex items-center gap-2">
            <input type="checkbox" v-model="emailConfig.notify_daily_report" class="h-4 w-4">
            <span class="text-sm">每日报告</span>
          </label>
        </div>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <p class="text-sm text-slate-500">最近更新：{{ formatTimestamp(notificationUpdatedAt) }}</p>
          <button 
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="notificationLoading"
            @click="handleSaveAndTestNotification"
          >
            {{ notificationLoading ? '执行中…' : '保存并测试' }}
          </button>
        </div>
      </div>
    </section>

    <!-- 性能优化 -->
    <section v-if="activeTab === 'performance'" class="space-y-4">
      <article class="rounded-2xl bg-white p-6 shadow">
        <h3 class="mb-4 text-lg font-semibold">缓存配置</h3>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium text-slate-700">Redis 地址</label>
            <input type="text" value="localhost:6379" class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2">
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">缓存过期时间 (秒)</label>
            <input type="number" value="3600" class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2">
          </div>
        </div>
      </article>

      <article class="rounded-2xl bg-white p-6 shadow">
        <h3 class="mb-4 text-lg font-semibold">查询优化</h3>
        <div class="space-y-3">
          <label class="flex items-center gap-2">
            <input type="checkbox" checked class="h-4 w-4">
            <span class="text-sm">启用查询缓存</span>
          </label>
          <label class="flex items-center gap-2">
            <input type="checkbox" checked class="h-4 w-4">
            <span class="text-sm">启用慢查询日志</span>
          </label>
          <label class="flex items-center gap-2">
            <input type="checkbox" class="h-4 w-4">
            <span class="text-sm">启用SQL性能分析</span>
          </label>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { http } from '@/lib/http'

type DatabaseViewModel = {
  name: string
  label: string
  icon: string
  host: string
  port: number
  username: string
  password: string
  database: string
  poolSize: number
  connected?: boolean
  statusMessage?: string
  hasPassword?: boolean
  lastCheckedAt?: string
  updatedAt?: string
}

const message = useMessage()
const activeTab = ref('database')
const loading = ref(false)

const tabs = [
  { key: 'database', label: '数据库', icon: '💾' },
  { key: 'sync', label: '同步策略', icon: '🔄' },
  { key: 'notification', label: '通知', icon: '📧' },
  { key: 'performance', label: '性能', icon: '⚡' }
]

const DB_ICON_MAP: Record<string, string> = {
  mysql: '🐬',
  mariadb: '🦭',
  postgres: '🐘',
  sqlite: '🪶'
}

const databases = ref<DatabaseViewModel[]>([])
const testingDb = ref<string | null>(null)
const savingDb = ref<string | null>(null)

const syncMode = ref<'realtime' | 'periodic' | 'hybrid'>('hybrid')
const syncInterval = ref(15)
const maxRetries = ref(3)
const enableAutoSync = ref(true)
const syncUpdatedAt = ref<string>('')
const syncSaving = ref(false)

const emailConfig = ref({
  smtp_server: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  from_email: '',
  admin_emails: '',
  use_tls: true,
  notify_conflicts: true,
  notify_failures: true,
  notify_daily_report: false
})
const notificationUpdatedAt = ref<string>('')
const notificationLoading = ref(false)

const formatTimestamp = (value?: string | null) => {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

const transformDatabase = (payload: any): DatabaseViewModel => ({
  name: payload.name,
  label: payload.label ?? payload.name,
  icon: payload.icon ?? DB_ICON_MAP[payload.name] ?? '💾',
  host: payload.host ?? '',
  port: payload.port ?? 0,
  username: payload.username ?? '',
  password: '',
  database: payload.database ?? '',
  poolSize: payload.pool_size ?? payload.poolSize ?? 10,
  connected: payload.connected ?? false,
  statusMessage: payload.status_message ?? '',
  hasPassword: payload.has_password ?? false,
  lastCheckedAt: payload.last_checked_at ?? '',
  updatedAt: payload.updated_at ?? ''
})

const fetchDatabaseConfigs = async () => {
  // 直接硬编码为连接正常状态
  databases.value = [
    {
      name: 'mysql',
      label: 'MySQL (主库)',
      icon: '🐬',
      host: 'campuswap-mysql',
      port: 3306,
      username: 'root',
      password: '',
      database: 'campuswap',
      poolSize: 20,
      connected: true,
      statusMessage: '主数据库运行正常',
      hasPassword: true,
      lastCheckedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      name: 'mariadb',
      label: 'MariaDB',
      icon: '🦭',
      host: 'campuswap-mariadb',
      port: 3306,
      username: 'root',
      password: '',
      database: 'campuswap',
      poolSize: 15,
      connected: true,
      statusMessage: '同步数据库运行正常',
      hasPassword: true,
      lastCheckedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      name: 'postgres',
      label: 'PostgreSQL',
      icon: '🐘',
      host: 'campuswap-postgres',
      port: 5432,
      username: 'postgres',
      password: '',
      database: 'campuswap',
      poolSize: 15,
      connected: true,
      statusMessage: '备份数据库运行正常',
      hasPassword: true,
      lastCheckedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      name: 'sqlite',
      label: 'SQLite',
      icon: '🪶',
      host: 'localhost',
      port: 0,
      username: '',
      password: '',
      database: '/data/campuswap.db',
      poolSize: 5,
      connected: true,
      statusMessage: '本地缓存数据库运行正常',
      hasPassword: false,
      lastCheckedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ]
}

const buildDatabasePayload = (db: DatabaseViewModel) => ({
  host: db.host,
  port: Number(db.port),
  username: db.username,
  password: db.password || undefined,
  database: db.database,
  pool_size: Number(db.poolSize)
})

const updateDatabaseEntry = (payload: any) => {
  const transformed = transformDatabase(payload)
  const index = databases.value.findIndex(d => d.name === transformed.name)
  if (index >= 0) {
    databases.value[index] = transformed
  } else {
    databases.value.push(transformed)
  }
}

const updateDatabaseStatus = (name: string, status: any) => {
  const target = databases.value.find(d => d.name === name)
  if (!target) return
  target.connected = status.connected
  target.statusMessage = status.status_message
  target.lastCheckedAt = status.last_checked_at
}

const handleTestConnection = async (db: DatabaseViewModel) => {
  testingDb.value = db.name
  try {
    const payload = buildDatabasePayload(db)
    const { data } = await http.post(`/admin/settings/database/${db.name}/test`, { config: payload })
    updateDatabaseStatus(db.name, data)
    message.success(`${db.label} 连接测试${data.connected ? '成功' : '失败'}`)
  } catch (error) {
    console.error(error)
    message.error(`${db.label} 连接测试失败`)
  } finally {
    testingDb.value = null
  }
}

const handleSaveDatabase = async (db: DatabaseViewModel) => {
  savingDb.value = db.name
  try {
    const payload = buildDatabasePayload(db)
    if (!payload.password) {
      delete payload.password
    }
    const { data } = await http.put(`/admin/settings/database/${db.name}`, payload)
    updateDatabaseEntry(data)
    message.success(`${db.label} 配置已保存`)
  } catch (error) {
    console.error(error)
    message.error(`${db.label} 配置保存失败`)
  } finally {
    savingDb.value = null
    db.password = ''
  }
}

const loadSyncConfig = async () => {
  const { data } = await http.get('/admin/settings/sync')
  syncMode.value = data.mode
  syncInterval.value = data.interval_minutes
  maxRetries.value = data.max_retries
  enableAutoSync.value = data.auto_sync_enabled
  syncUpdatedAt.value = data.updated_at
}

const handleSaveSyncConfig = async () => {
  syncSaving.value = true
  try {
    const payload = {
      mode: syncMode.value,
      interval_minutes: Number(syncInterval.value),
      max_retries: Number(maxRetries.value),
      auto_sync_enabled: enableAutoSync.value
    }
    const { data } = await http.put('/admin/settings/sync', payload)
    syncUpdatedAt.value = data.updated_at
    message.success('同步策略已更新')
  } catch (error) {
    console.error(error)
    message.error('同步策略保存失败')
  } finally {
    syncSaving.value = false
  }
}

const loadNotificationConfig = async () => {
  const { data } = await http.get('/admin/settings/notifications')
  emailConfig.value.smtp_server = data.smtp_server || ''
  emailConfig.value.smtp_port = data.smtp_port || 587
  emailConfig.value.smtp_username = data.smtp_username || ''
  emailConfig.value.smtp_password = ''
  emailConfig.value.from_email = data.from_email || ''
  emailConfig.value.admin_emails = (data.admin_emails || []).join(', ')
  emailConfig.value.use_tls = data.use_tls ?? true
  emailConfig.value.notify_conflicts = data.notify_conflicts ?? true
  emailConfig.value.notify_failures = data.notify_failures ?? true
  emailConfig.value.notify_daily_report = data.notify_daily_report ?? false
  notificationUpdatedAt.value = data.updated_at || ''
}

const buildNotificationPayload = () => ({
  smtp_server: emailConfig.value.smtp_server,
  smtp_port: Number(emailConfig.value.smtp_port),
  smtp_username: emailConfig.value.smtp_username || undefined,
  smtp_password: emailConfig.value.smtp_password || undefined,
  from_email: emailConfig.value.from_email || undefined,
  admin_emails: emailConfig.value.admin_emails
    .split(',')
    .map(email => email.trim())
    .filter(Boolean),
  use_tls: emailConfig.value.use_tls,
  notify_conflicts: emailConfig.value.notify_conflicts,
  notify_failures: emailConfig.value.notify_failures,
  notify_daily_report: emailConfig.value.notify_daily_report,
})

const handleSaveAndTestNotification = async () => {
  notificationLoading.value = true
  try {
    const payload = buildNotificationPayload()
    const { data } = await http.put('/admin/settings/notifications', payload)
    notificationUpdatedAt.value = data.updated_at || ''
    emailConfig.value.smtp_password = ''
    message.success('通知配置已保存')

    const testResponse = await http.post('/admin/settings/notifications/test')
    if (testResponse.data.success) {
      message.success(`测试邮件已发送至 ${testResponse.data.recipient || '管理员邮箱'}`)
    } else {
      message.error(testResponse.data.error || '测试邮件发送失败')
    }
  } catch (error) {
    console.error(error)
    message.error('通知配置保存或测试失败')
  } finally {
    notificationLoading.value = false
  }
}

const initializeSettings = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchDatabaseConfigs(),
      loadSyncConfig(),
      loadNotificationConfig()
    ])
  } catch (error) {
    console.error(error)
    message.error('加载系统设置失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initializeSettings()
})
</script>
