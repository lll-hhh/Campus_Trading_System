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
        <div class="mb-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div 
              class="flex h-12 w-12 items-center justify-center rounded-full text-2xl"
              :class="db.connected ? 'bg-green-100' : 'bg-red-100'"
            >
              {{ db.icon }}
            </div>
            <div>
              <h3 class="text-lg font-semibold">{{ db.name }}</h3>
              <p class="text-sm text-slate-500">{{ db.host }}:{{ db.port }}</p>
            </div>
          </div>
          <span 
            class="rounded-full px-3 py-1 text-sm font-semibold"
            :class="db.connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
          >
            {{ db.connected ? '已连接' : '未连接' }}
          </span>
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
              v-model="db.port"
              type="number" 
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
            <label class="text-sm font-medium text-slate-700">连接池大小</label>
            <input 
              v-model="db.poolSize"
              type="number" 
              class="mt-1 w-full rounded-lg border-2 border-slate-300 px-3 py-2 text-sm"
            >
          </div>
        </div>

        <div class="mt-4 flex gap-2">
          <button class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
            测试连接
          </button>
          <button class="rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700">
            保存配置
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
              v-model="emailConfig.smtp_port"
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
        <button class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
          保存并测试
        </button>
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
import { ref } from 'vue'

const activeTab = ref('database')

const tabs = [
  { key: 'database', label: '数据库', icon: '💾' },
  { key: 'sync', label: '同步策略', icon: '🔄' },
  { key: 'notification', label: '通知', icon: '📧' },
  { key: 'performance', label: '性能', icon: '⚡' }
]

const databases = ref([
  { name: 'MySQL', icon: '🐬', host: 'localhost', port: 3306, username: 'root', poolSize: 10, connected: true },
  { name: 'MariaDB', icon: '🦭', host: 'localhost', port: 3307, username: 'root', poolSize: 10, connected: true },
  { name: 'PostgreSQL', icon: '🐘', host: 'localhost', port: 5432, username: 'postgres', poolSize: 10, connected: true },
  { name: 'SQLite', icon: '🪶', host: 'local', port: 0, username: 'N/A', poolSize: 1, connected: true }
])

const syncMode = ref('hybrid')
const syncInterval = ref(15)
const maxRetries = ref(3)
const enableAutoSync = ref(true)

const emailConfig = ref({
  smtp_server: 'smtp.csu.edu.cn',
  smtp_port: 587,
  from_email: 'noreply@csu.edu.cn',
  admin_emails: 'admin@csu.edu.cn',
  notify_conflicts: true,
  notify_failures: true,
  notify_daily_report: true
})
</script>
