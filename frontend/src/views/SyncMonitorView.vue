<template>
  <div class="sync-monitor-view">
    <n-space vertical size="large">
      <!-- 页面标题 -->
      <n-page-header title="数据库同步监控" subtitle="实时监控四数据库同步状态">
        <template #extra>
          <n-space>
            <n-button @click="refreshData" :loading="loading">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新
            </n-button>
            <n-button type="primary" @click="showSyncRepairModal = true">
              <template #icon>
                <n-icon><BuildOutline /></n-icon>
              </template>
              同步修复
            </n-button>
          </n-space>
        </template>
      </n-page-header>

      <!-- 统计卡片 -->
      <n-grid :x-gap="16" :y-gap="16" :cols="4" responsive="screen">
        <n-grid-item>
          <n-statistic label="同步成功" tabular-nums>
            <n-number-animation :from="0" :to="stats.success_count" />
            <template #suffix>次</template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="同步失败" tabular-nums>
            <n-number-animation :from="0" :to="stats.failure_count" />
            <template #suffix>次</template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="冲突记录" tabular-nums>
            <n-number-animation :from="0" :to="stats.conflict_count" />
            <template #suffix>条</template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="成功率" tabular-nums>
            <n-number-animation :from="0" :to="stats.success_rate * 100" :precision="2" />
            <template #suffix>%</template>
          </n-statistic>
        </n-grid-item>
      </n-grid>

      <!-- 数据库状态 -->
      <n-card title="数据库状态" :bordered="false">
        <n-space vertical size="large">
          <div
            v-for="db in databases"
            :key="db.name"
            class="database-status"
          >
            <n-space justify="space-between" align="center">
              <n-space>
                <n-icon size="24" :color="getStatusColor(db.status)">
                  <ServerOutline />
                </n-icon>
                <div>
                  <div class="db-name">{{ db.label }}</div>
                  <div class="db-info">{{ db.type }} - {{ db.host }}</div>
                </div>
              </n-space>

              <n-space>
                <n-tag :type="getStatusType(db.status)" :bordered="false">
                  {{ getStatusText(db.status) }}
                </n-tag>
                <n-progress
                  type="circle"
                  :percentage="db.sync_progress"
                  :width="60"
                  :show-indicator="true"
                />
                <div class="stats">
                  <div class="stat-item">
                    <span class="label">延迟:</span>
                    <span class="value">{{ db.latency }}ms</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">最后同步:</span>
                    <span class="value">{{ formatTime(db.last_sync) }}</span>
                  </div>
                </div>
              </n-space>
            </n-space>
          </div>
        </n-space>
      </n-card>

      <!-- 冲突记录 -->
      <n-card title="冲突记录" :bordered="false">
        <template #header-extra>
          <n-space>
            <n-select
              v-model:value="conflictFilter"
              :options="conflictFilterOptions"
              style="width: 150px"
              @update:value="loadConflicts"
            />
          </n-space>
        </template>

        <n-data-table
          :columns="conflictColumns"
          :data="conflicts"
          :loading="conflictLoading"
          :pagination="conflictPagination"
          :row-key="(row: any) => row.id"
        />
      </n-card>

      <!-- 同步日志 -->
      <n-card title="同步日志" :bordered="false">
        <n-data-table
          :columns="logColumns"
          :data="logs"
          :loading="logLoading"
          :pagination="logPagination"
          :row-key="(row: any) => row.id"
        />
      </n-card>
    </n-space>

    <!-- 同步修复对话框 -->
    <n-modal
      v-model:show="showSyncRepairModal"
      preset="card"
      title="同步修复"
      style="width: 600px"
    >
      <n-form ref="repairFormRef" :model="repairForm" label-placement="left" label-width="100">
        <n-form-item label="表名" path="table">
          <n-input v-model:value="repairForm.table" placeholder="输入表名" />
        </n-form-item>
        <n-form-item label="记录ID" path="record_id">
          <n-input-number
            v-model:value="repairForm.record_id"
            placeholder="输入记录ID"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="强制修复">
          <n-switch v-model:value="repairForm.force" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showSyncRepairModal = false">取消</n-button>
          <n-button type="primary" @click="handleSyncRepair" :loading="repairLoading">
            开始修复
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 冲突详情对话框 -->
    <n-modal
      v-model:show="showConflictDetailModal"
      preset="card"
      title="冲突详情"
      style="width: 800px"
    >
      <n-descriptions v-if="selectedConflict" bordered :column="2">
        <n-descriptions-item label="冲突ID">
          {{ selectedConflict.id }}
        </n-descriptions-item>
        <n-descriptions-item label="表名">
          {{ selectedConflict.table_name }}
        </n-descriptions-item>
        <n-descriptions-item label="记录ID">
          {{ selectedConflict.record_id }}
        </n-descriptions-item>
        <n-descriptions-item label="来源数据库">
          {{ selectedConflict.source }}
        </n-descriptions-item>
        <n-descriptions-item label="目标数据库">
          {{ selectedConflict.target }}
        </n-descriptions-item>
        <n-descriptions-item label="发生时间">
          {{ formatDateTime(selectedConflict.created_at) }}
        </n-descriptions-item>
        <n-descriptions-item label="冲突数据" :span="2">
          <n-code :code="JSON.stringify(selectedConflict.payload, null, 2)" language="json" />
        </n-descriptions-item>
      </n-descriptions>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showConflictDetailModal = false">关闭</n-button>
          <n-button
            type="warning"
            @click="resolveConflict(selectedConflict.id)"
            :loading="resolveLoading"
          >
            标记为已解决
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useMessage, NButton, NTag, NSpace } from 'naive-ui'
import {
  RefreshOutline,
  BuildOutline,
  ServerOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'
import type { DataTableColumns } from 'naive-ui'

const message = useMessage()

// 状态
const loading = ref(false)
const conflictLoading = ref(false)
const logLoading = ref(false)
const repairLoading = ref(false)
const resolveLoading = ref(false)

// 统计数据
const stats = ref({
  success_count: 12345,
  failure_count: 23,
  conflict_count: 5,
  success_rate: 0.998
})

// 数据库状态
const databases = ref([
  {
    name: 'mysql',
    label: 'MySQL (主库)',
    type: 'MySQL 8.0',
    host: 'localhost:3306',
    status: 'healthy',
    sync_progress: 100,
    latency: 5,
    last_sync: new Date()
  },
  {
    name: 'postgres',
    label: 'PostgreSQL',
    type: 'PostgreSQL 15',
    host: 'localhost:5432',
    status: 'healthy',
    sync_progress: 98,
    latency: 8,
    last_sync: new Date()
  },
  {
    name: 'mariadb',
    label: 'MariaDB',
    type: 'MariaDB 10.11',
    host: 'localhost:3307',
    status: 'warning',
    sync_progress: 95,
    latency: 12,
    last_sync: new Date(Date.now() - 60000)
  },
  {
    name: 'sqlite',
    label: 'SQLite',
    type: 'SQLite 3',
    host: 'campus_swap.db',
    status: 'healthy',
    sync_progress: 100,
    latency: 2,
    last_sync: new Date()
  }
])

// 冲突记录
const conflicts = ref<any[]>([])
const conflictFilter = ref('unresolved')
const conflictFilterOptions = [
  { label: '未解决', value: 'unresolved' },
  { label: '已解决', value: 'resolved' },
  { label: '全部', value: 'all' }
]

const conflictPagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 同步日志
const logs = ref<any[]>([])
const logPagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 对话框
const showSyncRepairModal = ref(false)
const showConflictDetailModal = ref(false)
const selectedConflict = ref<any>(null)

// 修复表单
const repairForm = ref({
  table: '',
  record_id: null as number | null,
  force: false
})

// 冲突表格列
const conflictColumns: DataTableColumns<any> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '表名',
    key: 'table_name',
    width: 150
  },
  {
    title: '记录ID',
    key: 'record_id',
    width: 120
  },
  {
    title: '来源',
    key: 'source',
    width: 100
  },
  {
    title: '目标',
    key: 'target',
    width: 100
  },
  {
    title: '状态',
    key: 'resolved',
    width: 100,
    render(row) {
      return h(
        NTag,
        {
          type: row.resolved ? 'success' : 'error',
          bordered: false
        },
        { default: () => row.resolved ? '已解决' : '未解决' }
      )
    }
  },
  {
    title: '发生时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDateTime(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row) {
      return h(
        NSpace,
        {},
        {
          default: () => [
            h(
              NButton,
              {
                size: 'small',
                onClick: () => viewConflictDetail(row)
              },
              { default: () => '详情' }
            ),
            !row.resolved && h(
              NButton,
              {
                size: 'small',
                type: 'warning',
                onClick: () => resolveConflict(row.id)
              },
              { default: () => '解决' }
            )
          ]
        }
      )
    }
  }
]

// 日志表格列
const logColumns: DataTableColumns<any> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(
        NTag,
        {
          type: row.status === 'completed' ? 'success' : 'error',
          bordered: false
        },
        { default: () => row.status }
      )
    }
  },
  {
    title: '表名',
    key: 'table',
    width: 150,
    render(row) {
      return row.stats?.table || '-'
    }
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    render(row) {
      return row.stats?.action || '-'
    }
  },
  {
    title: '成功数',
    key: 'success_count',
    width: 100,
    render(row) {
      return row.stats?.success_count || 0
    }
  },
  {
    title: '总数',
    key: 'total_count',
    width: 100,
    render(row) {
      return row.stats?.total_count || 0
    }
  },
  {
    title: '开始时间',
    key: 'started_at',
    width: 180,
    render(row) {
      return formatDateTime(row.started_at)
    }
  },
  {
    title: '完成时间',
    key: 'completed_at',
    width: 180,
    render(row) {
      return formatDateTime(row.completed_at)
    }
  }
]

// 方法
const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return '#18a058'
    case 'warning':
      return '#f0a020'
    case 'error':
      return '#d03050'
    default:
      return '#999'
  }
}

const getStatusType = (status: string): any => {
  switch (status) {
    case 'healthy':
      return 'success'
    case 'warning':
      return 'warning'
    case 'error':
      return 'error'
    default:
      return 'default'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'healthy':
      return '正常'
    case 'warning':
      return '警告'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
}

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString()
  }
}

const formatDateTime = (date: string | Date) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('zh-CN')
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadStats(),
      loadDatabaseStatus(),
      loadConflicts(),
      loadLogs()
    ])
    message.success('数据已刷新')
  } catch (error) {
    console.error('刷新失败:', error)
    message.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  // TODO: 调用API加载统计数据
}

const loadDatabaseStatus = async () => {
  // TODO: 调用API加载数据库状态
}

const loadConflicts = async () => {
  conflictLoading.value = true
  try {
    // TODO: 调用API加载冲突记录
    // 模拟数据
    conflicts.value = [
      {
        id: 1,
        table_name: 'items',
        record_id: '12345',
        source: 'mysql',
        target: 'postgres,mariadb',
        resolved: false,
        created_at: new Date(),
        payload: { type: 'version_conflict', version: 5 }
      }
    ]
  } finally {
    conflictLoading.value = false
  }
}

const loadLogs = async () => {
  logLoading.value = true
  try {
    // TODO: 调用API加载同步日志
    // 模拟数据
    logs.value = [
      {
        id: 1,
        status: 'completed',
        started_at: new Date(),
        completed_at: new Date(),
        stats: {
          table: 'items',
          action: 'update',
          success_count: 3,
          total_count: 4
        }
      }
    ]
  } finally {
    logLoading.value = false
  }
}

const handleSyncRepair = async () => {
  if (!repairForm.value.table || !repairForm.value.record_id) {
    message.warning('请填写完整信息')
    return
  }

  repairLoading.value = true
  try {
    // TODO: 调用同步修复API
    await new Promise(resolve => setTimeout(resolve, 1000))
    message.success('同步修复成功')
    showSyncRepairModal.value = false
    refreshData()
  } catch (error) {
    console.error('修复失败:', error)
    message.error('修复失败')
  } finally {
    repairLoading.value = false
  }
}

const viewConflictDetail = (conflict: any) => {
  selectedConflict.value = conflict
  showConflictDetailModal.value = true
}

const resolveConflict = async (conflictId: number) => {
  resolveLoading.value = true
  try {
    // TODO: 调用API标记冲突为已解决
    await new Promise(resolve => setTimeout(resolve, 500))
    message.success('已标记为已解决')
    showConflictDetailModal.value = false
    loadConflicts()
  } catch (error) {
    console.error('操作失败:', error)
    message.error('操作失败')
  } finally {
    resolveLoading.value = false
  }
}

// 初始化
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.sync-monitor-view {
  padding: 24px;
}

.database-status {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.db-name {
  font-weight: 500;
  font-size: 16px;
  margin-bottom: 4px;
}

.db-info {
  font-size: 12px;
  color: #999;
}

.stats {
  text-align: right;
}

.stat-item {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.stat-item .label {
  color: #999;
  margin-right: 4px;
}

.stat-item .value {
  color: #333;
  font-weight: 500;
}
</style>
