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
            <n-button type="warning" @click="handleForceSyncAll" :loading="syncingAll">
              <template #icon>
                <n-icon><SyncOutline /></n-icon>
              </template>
              全库强制同步
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
                  <n-button size="tiny" quaternary type="primary" @click="handleManualSync(db.name)">
                    立即同步
                  </n-button>
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
              @update:value="handleConflictFilterChange"
            />
          </n-space>
        </template>

        <n-data-table
          :columns="conflictColumns"
          :data="conflicts"
          :loading="loadingConflicts"
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
      title="冲突解决 - 选择保留数据"
      style="width: 1000px"
    >
      <div v-if="selectedConflict">
        <!-- 基本信息 -->
        <n-descriptions bordered :column="3" size="small" style="margin-bottom: 20px">
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
            <n-tag type="info">{{ selectedConflict.source_db || selectedConflict.source }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="目标数据库">
            <n-tag type="warning">{{ selectedConflict.target_db || selectedConflict.target }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="发生时间">
            {{ formatDateTime(selectedConflict.created_at) }}
          </n-descriptions-item>
        </n-descriptions>

        <!-- 数据对比 -->
        <n-divider>数据对比 - 字段差异</n-divider>
        
        <n-space vertical>
          <!-- 选择策略 -->
          <n-alert type="info" title="请选择要保留的数据" style="margin-bottom: 16px">
            红色背景表示两个数据库的值不同，绿色边框表示当前选中的数据源
          </n-alert>

          <!-- 字段对比表格 -->
          <n-card title="字段详细对比" style="margin-bottom: 16px">
            <n-data-table
              :columns="conflictComparisonColumns"
              :data="conflictComparisonData"
              :pagination="false"
              :bordered="true"
              size="small"
              :max-height="400"
            />
          </n-card>

          <!-- 选择数据源 -->
          <n-radio-group v-model:value="conflictResolutionChoice" size="large">
            <n-space vertical :size="16">
              <!-- 来源数据库选项 -->
              <n-card 
                :class="{ 'selected-data-card': conflictResolutionChoice === 'source' }"
                hoverable
                @click="conflictResolutionChoice = 'source'"
                style="cursor: pointer"
              >
                <template #header>
                  <n-space align="center">
                    <n-radio :value="'source'" style="pointer-events: none" />
                    <span style="font-weight: 600">✅ 保留来源数据库 ({{ selectedConflict.source_db || selectedConflict.source }})</span>
                    <n-tag type="info" size="small">源数据</n-tag>
                  </n-space>
                </template>
                <div style="color: #666; font-size: 13px">
                  将此数据库的所有字段值同步到其他数据库
                </div>
              </n-card>

              <!-- 目标数据库选项 -->
              <n-card 
                :class="{ 'selected-data-card': conflictResolutionChoice === 'target' }"
                hoverable
                @click="conflictResolutionChoice = 'target'"
                style="cursor: pointer"
              >
                <template #header>
                  <n-space align="center">
                    <n-radio :value="'target'" style="pointer-events: none" />
                    <span style="font-weight: 600">✅ 保留目标数据库 ({{ selectedConflict.target_db || selectedConflict.target }})</span>
                    <n-tag type="warning" size="small">目标数据</n-tag>
                  </n-space>
                </template>
                <div style="color: #666; font-size: 13px">
                  将此数据库的所有字段值同步到其他数据库
                </div>
              </n-card>

              <!-- 仅标记已解决选项 -->
              <n-card 
                :class="{ 'selected-data-card': conflictResolutionChoice === 'manual' }"
                hoverable
                @click="conflictResolutionChoice = 'manual'"
                style="cursor: pointer"
              >
                <template #header>
                  <n-space align="center">
                    <n-radio :value="'manual'" style="pointer-events: none" />
                    <span style="font-weight: 600">⚠️ 仅标记为已解决</span>
                    <n-tag type="default" size="small">不同步数据</n-tag>
                  </n-space>
                </template>
                <n-alert type="warning" title="注意">
                  此选项只会将冲突标记为已解决，但不会同步数据到其他数据库。数据不一致性仍然存在。
                </n-alert>
              </n-card>
            </n-space>
          </n-radio-group>
        </n-space>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showConflictDetailModal = false">取消</n-button>
          <n-button
            type="primary"
            :loading="resolvingConflictId === selectedConflict?.id"
            :disabled="!conflictResolutionChoice"
            @click="handleResolveWithChoice"
          >
            {{ conflictResolutionChoice === 'manual' ? '标记已解决' : '解决冲突并同步数据' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useMessage, NButton, NTag, NSpace } from 'naive-ui'
import {
  RefreshOutline,
  BuildOutline,
  ServerOutline,
  SyncOutline
} from '@vicons/ionicons5'
import type { DataTableColumns } from 'naive-ui'
import { useSyncStore } from '@/stores/sync'
import { http as api } from '@/lib/http'

const message = useMessage()
const syncStore = useSyncStore()
const { conflicts, loadingConflicts, resolvingConflictId, conflictMeta } = storeToRefs(syncStore)

// 状态
const loading = ref(false)
const logLoading = ref(false)
const repairLoading = ref(false)
const syncingAll = ref(false)

const handleError = (error: any, fallback: string) => {
  console.error(error)
  const detail = error.response?.data?.detail
  message.error(typeof detail === 'string' ? detail : fallback)
}

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
    host: 'phoenix_parts.db',
    status: 'healthy',
    sync_progress: 100,
    latency: 2,
    last_sync: new Date()
  }
])

// 冲突记录
const conflictFilter = ref<'all' | 'resolved' | 'unresolved'>(conflictMeta.value.filter)
const conflictFilterOptions = [
  { label: '未解决', value: 'unresolved' },
  { label: '已解决', value: 'resolved' },
  { label: '全部', value: 'all' }
]

const conflictPagination = computed(() => ({
  page: conflictMeta.value.page,
  pageSize: conflictMeta.value.pageSize,
  itemCount: conflictMeta.value.total,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => loadConflicts({ page }),
  onUpdatePage: (page: number) => loadConflicts({ page }),
  onPageSizeChange: (pageSize: number) => loadConflicts({ pageSize, page: 1 }),
  onUpdatePageSize: (pageSize: number) => loadConflicts({ pageSize, page: 1 })
}))

// 同步日志
const logs = ref<any[]>([])
const logPagination = ref({
  page: 1,
  pageSize: 10,
  pageCount: 1,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 对话框
const showSyncRepairModal = ref(false)
const showConflictDetailModal = ref(false)
const selectedConflict = ref<any>(null)
const conflictResolutionChoice = ref<'source' | 'target' | 'manual'>('source')

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
                loading: resolvingConflictId.value === row.id,
                onClick: () => resolveConflictRecord(row.id, 'manual')
              },
              { default: () => resolvingConflictId.value === row.id ? '处理中…' : '解决' }
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
  const response = await fetch('/api/v1/sync/stats', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  })
  if (response.ok) {
    const data = await response.json()
    stats.value = data
  }
}

const loadDatabaseStatus = async () => {
  const response = await fetch('/api/v1/sync/databases/status', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  })
  if (response.ok) {
    const data = await response.json()
    databases.value = data.databases
  }
}

async function loadConflicts(options?: { page?: number; pageSize?: number }) {
  await syncStore.fetchConflicts({
    page: options?.page,
    pageSize: options?.pageSize,
    filter: conflictFilter.value
  })
}

function handleConflictFilterChange(value: 'all' | 'resolved' | 'unresolved') {
  conflictFilter.value = value
  loadConflicts({ page: 1 })
}

const loadLogs = async () => {
  logLoading.value = true
  try {
    const params = new URLSearchParams({
      page: logPagination.value.page.toString(),
      page_size: logPagination.value.pageSize.toString()
    })
    
    const response = await fetch(`/api/v1/sync/logs?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      logs.value = data.logs
      logPagination.value.pageCount = Math.ceil(data.total / data.page_size)
    }
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
    const response = await fetch('/api/v1/sync/repair', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(repairForm.value)
    })
    
    if (response.ok) {
      const data = await response.json()
      message.success('同步修复成功')
      showSyncRepairModal.value = false
      refreshData()
    } else {
      const error = await response.json()
      message.error(error.detail || '修复失败')
    }
  } catch (error) {
    console.error('修复失败:', error)
    message.error('修复失败')
  } finally {
    repairLoading.value = false
  }
}

const handleForceSyncAll = async () => {
  syncingAll.value = true
  try {
    await api.post('/sync/trigger-all')
    message.success('全库同步任务已触发')
    refreshData()
  } catch (error: any) {
    handleError(error, '触发全库同步失败')
  } finally {
    syncingAll.value = false
  }
}

const handleManualSync = async (dbName: string) => {
  try {
    await api.post(`/sync/trigger/${dbName}`)
    message.success(`${dbName} 同步任务已触发`)
    refreshData()
  } catch (error: any) {
    handleError(error, `触发 ${dbName} 同步失败`)
  }
}

const viewConflictDetail = (conflict: any) => {
  selectedConflict.value = conflict
  conflictResolutionChoice.value = 'source' // 默认选择源数据
  showConflictDetailModal.value = true
}

// 格式化冲突数据为美观的JSON
const formatConflictData = (data: any): string => {
  if (!data) return '{}'
  
  try {
    // 如果是字符串，先解析
    const parsed = typeof data === 'string' ? JSON.parse(data) : data
    return JSON.stringify(parsed, null, 2)
  } catch {
    return typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  }
}

// 解析冲突数据
const parseConflictData = (data: any): Record<string, any> => {
  if (!data) return {}
  
  try {
    return typeof data === 'string' ? JSON.parse(data) : data
  } catch {
    return {}
  }
}

// 冲突对比列定义
const conflictComparisonColumns = computed(() => [
  {
    title: '字段名',
    key: 'field',
    width: 150,
    fixed: 'left' as const,
    render(row: any) {
      return h('span', { style: { fontWeight: '500' } }, row.field)
    }
  },
  {
    title: `来源数据库 (${selectedConflict.value?.source_db || selectedConflict.value?.source || 'N/A'})`,
    key: 'sourceValue',
    minWidth: 250,
    render(row: any) {
      const isDiff = row.isDifferent
      return h(
        'div',
        {
          style: {
            padding: '4px 8px',
            borderRadius: '4px',
            backgroundColor: isDiff ? '#fff1f0' : 'transparent',
            border: conflictResolutionChoice.value === 'source' && isDiff ? '2px solid #52c41a' : 'none',
            fontFamily: 'monospace',
            fontSize: '12px',
            wordBreak: 'break-all'
          }
        },
        String(row.sourceValue)
      )
    }
  },
  {
    title: `目标数据库 (${selectedConflict.value?.target_db || selectedConflict.value?.target || 'N/A'})`,
    key: 'targetValue',
    minWidth: 250,
    render(row: any) {
      const isDiff = row.isDifferent
      return h(
        'div',
        {
          style: {
            padding: '4px 8px',
            borderRadius: '4px',
            backgroundColor: isDiff ? '#fff1f0' : 'transparent',
            border: conflictResolutionChoice.value === 'target' && isDiff ? '2px solid #52c41a' : 'none',
            fontFamily: 'monospace',
            fontSize: '12px',
            wordBreak: 'break-all'
          }
        },
        String(row.targetValue)
      )
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    align: 'center' as const,
    render(row: any) {
      return h(
        NTag,
        {
          type: row.isDifferent ? 'error' : 'success',
          size: 'small',
          bordered: false
        },
        { default: () => row.isDifferent ? '冲突' : '一致' }
      )
    }
  }
])

// 冲突对比数据
const conflictComparisonData = computed(() => {
  if (!selectedConflict.value) return []
  
  const localData = parseConflictData(selectedConflict.value.local_data)
  const remoteData = parseConflictData(selectedConflict.value.remote_data)
  
  // 获取所有字段
  const allFields = new Set([
    ...Object.keys(localData),
    ...Object.keys(remoteData)
  ])
  
  // 排除某些系统字段
  const excludeFields = ['created_at', 'updated_at', 'deleted_at']
  
  return Array.from(allFields)
    .filter(field => !excludeFields.includes(field))
    .map(field => {
      const sourceValue = localData[field] !== undefined ? localData[field] : '-'
      const targetValue = remoteData[field] !== undefined ? remoteData[field] : '-'
      
      // 判断是否不同
      const isDifferent = JSON.stringify(sourceValue) !== JSON.stringify(targetValue)
      
      return {
        field,
        sourceValue: formatFieldValue(sourceValue),
        targetValue: formatFieldValue(targetValue),
        isDifferent
      }
    })
    .sort((a, b) => {
      // 有冲突的字段排在前面
      if (a.isDifferent && !b.isDifferent) return -1
      if (!a.isDifferent && b.isDifferent) return 1
      return a.field.localeCompare(b.field)
    })
})

// 格式化字段值
const formatFieldValue = (value: any): string => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

// 处理选择后的冲突解决
const handleResolveWithChoice = async () => {
  if (!selectedConflict.value || !conflictResolutionChoice.value) {
    return
  }

  try {
    await syncStore.resolveConflict(selectedConflict.value.id, conflictResolutionChoice.value)
    
    const messages = {
      source: `冲突已解决！来源数据库 (${selectedConflict.value.source_db || selectedConflict.value.source}) 的数据已同步到所有数据库`,
      target: `冲突已解决！目标数据库 (${selectedConflict.value.target_db || selectedConflict.value.target}) 的数据已同步到所有数据库`,
      manual: '冲突已标记为已解决（未同步数据）'
    }
    
    message.success(messages[conflictResolutionChoice.value] || '冲突已解决')
    showConflictDetailModal.value = false
  } catch (error: any) {
    console.error('解决冲突失败:', error)
    message.error(error.message || '解决冲突失败')
  }
}

async function resolveConflictRecord(conflictId: number, strategy: 'source' | 'target' | 'manual') {
  try {
    await syncStore.resolveConflict(conflictId, strategy)
    message.success('冲突已解决')
    if (selectedConflict.value?.id === conflictId) {
      showConflictDetailModal.value = false
    }
  } catch (error) {
    console.error('操作失败:', error)
    message.error('操作失败')
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

/* 冲突解决数据卡片样式 */
.selected-data-card {
  border: 2px solid #18a058;
  box-shadow: 0 0 8px rgba(24, 160, 88, 0.3);
}
</style>
