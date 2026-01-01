<template>
  <div class="admin-operations-container">
    <n-h1 class="mb-6">🛠️ 凤凰汽配 · 系统运维与审核中心</n-h1>

    <!-- 零件审核 -->
    <n-card title="⚖️ 零件审核" class="section-card mb-6">
      <template #header-extra>
        <n-space>
          <n-tag type="warning" round>待审核: {{ pendingItems.length }}</n-tag>
        </n-space>
      </template>
      
      <n-data-table
        :columns="auditColumns"
        :data="pendingItems"
        :loading="pendingLoading"
        :pagination="{ pageSize: 10 }"
      />
    </n-card>

    <!-- 数据导入导出 -->
    <n-card title="💾 数据导入/导出" class="section-card">
      <n-grid :cols="2" :x-gap="20">
        <n-gi>
          <h3>📤 数据导出</h3>
          <n-space vertical>
            <n-checkbox-group v-model:value="exportTables">
              <n-space vertical>
                <n-checkbox value="users" label="用户数据" />
                <n-checkbox value="items" label="零件数据" />
                <n-checkbox value="transactions" label="交易数据" />
                <n-checkbox value="comments" label="评论数据" />
                <n-checkbox value="messages" label="消息数据" />
                <n-checkbox value="audit_logs" label="审计日志" />
              </n-space>
            </n-checkbox-group>
            <n-select v-model:value="exportFormat" :options="exportFormatOptions" placeholder="选择导出格式" />
            <n-button type="primary" @click="exportData">🔽 导出数据</n-button>
          </n-space>
        </n-gi>

        <n-gi>
          <h3>📥 数据导入</h3>
          <n-space vertical>
            <n-select v-model:value="importTable" :options="importTableOptions" placeholder="选择目标表" />
            <n-upload :max="1" accept=".sql,.json,.csv" @before-upload="handleBeforeUpload">
              <n-button>选择文件</n-button>
            </n-upload>
            <n-radio-group v-model:value="importMode">
              <n-space>
                <n-radio value="replace" label="替换模式" />
                <n-radio value="append" label="追加模式" />
                <n-radio value="update" label="更新模式" />
              </n-space>
            </n-radio-group>
            <n-button type="primary" :disabled="!uploadedFile" :loading="importLoading" @click="importData">🔼 开始导入</n-button>
          </n-space>
        </n-gi>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, h } from 'vue'
import {
  NCard,
  NSpace,
  NButton,
  NTabs,
  NTabPane,
  NForm,
  NFormItem,
  NSelect,
  NInput,
  NInputNumber,
  NStatistic,
  NAlert,
  NCheckbox,
  NCheckboxGroup,
  NGrid,
  NGi,
  NUpload,
  NDataTable,
  useMessage,
  type UploadFileInfo
} from 'naive-ui'
import { http as api } from '@/lib/http'
import { ServerOutline } from '@vicons/ionicons5'

const message = useMessage()

const handleError = (error: unknown, fallback: string) => {
  console.error(error)
  const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
  message.error(detail || fallback)
}

// 批量用户操作
const batchUserCondition = ref('inactive_30days')
const batchUserAction = ref('delete')
const estimatedUserCount = ref(0)
const userEstimateLoading = ref(false)

const userConditionOptions = [
  { label: '30天未登录', value: 'inactive_30days' },
  { label: '未实名认证', value: 'not_verified' },
  { label: '信用分<60', value: 'low_credit' },
  { label: '被封禁', value: 'banned' }
]

const userActionOptions = [
  { label: '删除账号', value: 'delete' },
  { label: '发送提醒', value: 'remind' },
  { label: '降低权限', value: 'demote' },
  { label: '重置信用分', value: 'reset_credit' }
]

// 批量零件操作
const batchItemStatus = ref('available')
const batchItemDays = ref(90)
const batchItemAction = ref('archive')
const estimatedItemCount = ref(0)
const itemEstimateLoading = ref(false)

const itemStatusOptions = [
  { label: '在售', value: 'available' },
  { label: '已售出', value: 'sold' },
  { label: '已下架', value: 'deleted' },
  { label: '全部', value: 'all' }
]

const itemActionOptions = [
  { label: '归档', value: 'archive' },
  { label: '删除', value: 'delete' },
  { label: '提醒卖家', value: 'remind_seller' }
]

// 批量交易处理
const selectedTransactionTypes = ref<string[]>(['pending'])
const transactionDays = ref(30)

// 数据导入导出
const exportTables = ref<string[]>(['users', 'items'])
const exportFormat = ref<'json' | 'csv'>('json')
const uploadedFile = ref<UploadFileInfo | null>(null)
const importMode = ref<'replace' | 'append' | 'update'>('append')
const importTable = ref('users')
const importLoading = ref(false)

const exportFormatOptions = [
  { label: 'JSON', value: 'json' },
  { label: 'CSV', value: 'csv' }
]

const importTableOptions = [
  { label: '用户数据', value: 'users' },
  { label: '零件数据', value: 'items' },
  { label: '交易数据', value: 'transactions' },
  { label: '评论数据', value: 'comments' },
  { label: '消息数据', value: 'messages' },
  { label: '审计日志', value: 'audit_logs' }
]

// SQL 执行器
const sqlQuery = ref('')
const sqlResult = ref<any>(null)
const sqlLoading = ref(false)

const fetchUserEstimate = async () => {
  userEstimateLoading.value = true
  try {
    const { data } = await api.get<{ count: number }>(
      '/admin/operations/users/estimate',
      { params: { condition: batchUserCondition.value } }
    )
    estimatedUserCount.value = data.count
  } catch (error) {
    handleError(error, '无法获取用户数量')
  } finally {
    userEstimateLoading.value = false
  }
}

const fetchItemEstimate = async () => {
  itemEstimateLoading.value = true
  try {
    const { data } = await api.get<{ count: number }>(
      '/admin/operations/items/estimate',
      { params: { status: batchItemStatus.value, days: batchItemDays.value } }
    )
    estimatedItemCount.value = data.count
  } catch (error) {
    handleError(error, '无法获取零件数量')
  } finally {
    itemEstimateLoading.value = false
  }
}

watch(batchUserCondition, () => {
  fetchUserEstimate()
}, { immediate: true })
watch([batchItemStatus, batchItemDays], () => {
  fetchItemEstimate()
}, { immediate: true })

const executeBatchUserOperation = async () => {
  try {
    const { data } = await api.post<{ affected: number }>(
      '/admin/operations/users/batch',
      {
        condition: batchUserCondition.value,
        action: batchUserAction.value,
        dry_run: false
      }
    )
    message.success(`成功处理 ${data.affected} 个用户`)
    fetchUserEstimate()
  } catch (error) {
    handleError(error, '批量用户操作失败')
  }
}

const executeBatchItemOperation = async () => {
  try {
    const { data } = await api.post<{ affected: number }>(
      '/admin/operations/items/batch',
      {
        status: batchItemStatus.value,
        days: batchItemDays.value,
        action: batchItemAction.value,
        dry_run: false
      }
    )
    message.success(`成功处理 ${data.affected} 件零件`)
    fetchItemEstimate()
  } catch (error) {
    handleError(error, '批量零件操作失败')
  }
}

const cleanupTransactions = async () => {
  if (!selectedTransactionTypes.value.length) {
    message.warning('请至少选择一种交易类型')
    return
  }
  try {
    const { data } = await api.post<{ affected: number }>(
      '/admin/operations/transactions/cleanup',
      {
        statuses: selectedTransactionTypes.value,
        older_than_days: transactionDays.value
      }
    )
    message.success(`标记 ${data.affected} 条交易为已清理`)
  } catch (error) {
    handleError(error, '清理交易记录失败')
  }
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

const exportData = async () => {
  if (!exportTables.value.length) {
    message.warning('请至少选择一个要导出的数据表')
    return
  }
  try {
    const response = await api.post<Blob>(
      '/admin/operations/export',
      {
        tables: exportTables.value,
        format: exportFormat.value,
        schedule_only: false
      },
      { responseType: 'blob' }
    )
    const disposition = response.headers['content-disposition'] || ''
    const match = disposition.match(/filename="?([^";]+)"?/)
    const filename = match ? decodeURIComponent(match[1]) : `export-${Date.now()}.zip`
    downloadBlob(response.data, filename)
    message.success('数据导出任务完成')
  } catch (error) {
    handleError(error, '导出失败')
  }
}

const scheduleExport = async () => {
  try {
    await api.post('/admin/operations/export', {
      tables: exportTables.value,
      format: exportFormat.value,
      schedule_only: true
    })
    message.success('已提交定时导出请求')
  } catch (error) {
    handleError(error, '定时导出失败')
  }
}

const handleBeforeUpload = (options: { file: UploadFileInfo }) => {
  uploadedFile.value = options.file
  return false
}

const importData = async () => {
  if (!uploadedFile.value?.file) {
    message.warning('请先选择需要导入的文件')
    return
  }
  const rawFile = uploadedFile.value.file as File
  const form = new FormData()
  form.append('table', importTable.value)
  form.append('mode', importMode.value)
  form.append('file', rawFile)

  importLoading.value = true
  try {
    const { data } = await api.post<{ imported?: number; table?: string; message?: string }>(
      '/admin/operations/import',
      form,
      {
      headers: { 'Content-Type': 'multipart/form-data' }
      }
    )
    if ('imported' in data) {
      message.success(`导入 ${data.imported} 行 ${data.table} 数据成功`)
    } else {
      message.info(data.message || '文件已上传，请稍后处理')
    }
    uploadedFile.value = null
  } catch (error) {
    handleError(error, '导入失败')
  } finally {
    importLoading.value = false
  }
}

// SQL 执行器函数

const runSql = async (mode: 'run' | 'explain') => {
  if (!sqlQuery.value.trim()) {
    message.warning('请输入 SQL 语句')
    return
  }
  sqlLoading.value = true
  try {
    const { data } = await api.post('/admin/operations/sql', {
      database: 'mysql',
      query: sqlQuery.value.trim(),
      mode
    })
    sqlResult.value = data
    message.success(mode === 'run' ? 'SQL 执行成功' : 'EXPLAIN 完成')
  } catch (error) {
    handleError(error, 'SQL 执行失败')
  } finally {
    sqlLoading.value = false
  }
}

const executeSql = () => runSql('run')
const explainSql = () => runSql('explain')

const formatSql = () => {
  sqlQuery.value = sqlQuery.value.trim().replace(/\s+/g, ' ')
  message.success('SQL 已整理')
}

const clearSql = () => {
  sqlQuery.value = ''
  sqlResult.value = null
}

const pendingItems = ref<any[]>([])
const pendingLoading = ref(false)

const loadPendingItems = async () => {
  pendingLoading.value = true
  try {
    const response = await api.get('/admin/operations/items/pending')
    pendingItems.value = response.data
  } catch (error) {
    message.error('加载待审核零件失败')
  } finally {
    pendingLoading.value = false
  }
}

const auditItem = async (itemId: number, status: 'available' | 'banned', reason: string = '') => {
  try {
    // 映射前端状态到后端 action
    const action = status === 'available' ? 'approve' : 'reject'
    
    await api.post('/admin/operations/items/audit', {
      item_id: itemId,
      action: action,
      reason: reason
    })
    message.success(status === 'available' ? '审核通过' : '已驳回')
    loadPendingItems()
  } catch (error) {
    message.error('操作失败')
  }
}

const auditColumns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '标题', key: 'title' },
  { title: '价格', key: 'price', render: (row: any) => `¥${row.price}` },
  { title: '卖家', key: 'seller_name' },
  { title: '发布时间', key: 'created_at', render: (row: any) => new Date(row.created_at).toLocaleString() },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => h(NSpace, {}, {
      default: () => [
        h(NButton, { size: 'small', type: 'success', onClick: () => auditItem(row.id, 'available') }, { default: () => '通过' }),
        h(NButton, { size: 'small', type: 'error', onClick: () => auditItem(row.id, 'banned') }, { default: () => '驳回' })
      ]
    })
  }
]

onMounted(() => {
  loadPendingItems()
})
</script>

<style scoped>
.admin-operations-container {
  padding: 20px;
  background: #f5f5f5;
}

.admin-operations-container h1 {
  margin-bottom: 20px;
  font-size: 24px;
}

.section-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section-card h3 {
  margin-top: 0;
}
</style>
