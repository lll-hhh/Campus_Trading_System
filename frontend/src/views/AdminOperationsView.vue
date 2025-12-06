<template>
  <div class="admin-operations-container">
    <h1>⚙️ 管理员高级操作中心</h1>

    <!-- 批量操作区 -->
    <n-card title="📦 批量数据操作" class="section-card">
      <n-space vertical size="large">
        <n-alert type="warning" title="⚠️ 危险操作警告" :bordered="false">
          批量操作将影响多条数据，请谨慎操作！建议先备份数据库。
        </n-alert>

        <n-tabs type="line" animated>
          <n-tab-pane name="batch-user" tab="用户批量管理">
            <n-space vertical>
              <n-form inline>
                <n-form-item label="选择条件">
                  <n-select v-model:value="batchUserCondition" :options="userConditionOptions" style="width: 200px" />
                </n-form-item>
                <n-form-item label="操作">
                  <n-select v-model:value="batchUserAction" :options="userActionOptions" style="width: 200px" />
                </n-form-item>
                <n-form-item>
                  <n-button type="primary" @click="executeBatchUserOperation">
                    执行批量操作
                  </n-button>
                </n-form-item>
              </n-form>
              <n-statistic label="预计影响用户数" :value="estimatedUserCount">
                <template #suffix>人</template>
              </n-statistic>
            </n-space>
          </n-tab-pane>

          <n-tab-pane name="batch-item" tab="商品批量管理">
            <n-space vertical>
              <n-form inline>
                <n-form-item label="商品状态">
                  <n-select v-model:value="batchItemStatus" :options="itemStatusOptions" style="width: 150px" />
                </n-form-item>
                <n-form-item label="天数阈值">
                  <n-input-number v-model:value="batchItemDays" :min="1" style="width: 120px" />
                </n-form-item>
                <n-form-item label="操作">
                  <n-select v-model:value="batchItemAction" :options="itemActionOptions" style="width: 150px" />
                </n-form-item>
                <n-form-item>
                  <n-button type="primary" @click="executeBatchItemOperation">
                    执行批量操作
                  </n-button>
                </n-form-item>
              </n-form>
              <n-statistic label="预计影响商品数" :value="estimatedItemCount">
                <template #suffix>件</template>
              </n-statistic>
            </n-space>
          </n-tab-pane>

          <n-tab-pane name="batch-transaction" tab="交易批量处理">
            <n-space vertical>
              <n-form inline>
                <n-form-item label="交易类型">
                  <n-checkbox-group v-model:value="selectedTransactionTypes">
                    <n-space>
                      <n-checkbox value="pending" label="待处理" />
                      <n-checkbox value="cancelled" label="已取消" />
                      <n-checkbox value="timeout" label="超时未完成" />
                    </n-space>
                  </n-checkbox-group>
                </n-form-item>
                <n-form-item label="保留最近(天)">
                  <n-input-number v-model:value="transactionDays" :min="1" :max="365" style="width: 140px" />
                </n-form-item>
                <n-form-item>
                  <n-button type="error" @click="cleanupTransactions">
                    清理选中类型的交易记录
                  </n-button>
                </n-form-item>
              </n-form>
            </n-space>
          </n-tab-pane>
        </n-tabs>
      </n-space>
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
                <n-checkbox value="items" label="商品数据" />
                <n-checkbox value="transactions" label="交易数据" />
                <n-checkbox value="comments" label="评论数据" />
                <n-checkbox value="messages" label="消息数据" />
                <n-checkbox value="audit_logs" label="审计日志" />
              </n-space>
            </n-checkbox-group>
            <n-select v-model:value="exportFormat" :options="exportFormatOptions" placeholder="选择导出格式" />
            <n-space>
              <n-button type="primary" @click="exportData">
                🔽 导出数据
              </n-button>
              <n-button @click="scheduleExport">
                📅 定时导出
              </n-button>
            </n-space>
          </n-space>
        </n-gi>

        <n-gi>
          <h3>📥 数据导入</h3>
          <n-space vertical>
            <n-select v-model:value="importTable" :options="importTableOptions" placeholder="选择目标表" />
            <n-upload
              :max="1"
              accept=".sql,.json,.csv"
              @before-upload="handleBeforeUpload"
            >
              <n-button>选择文件</n-button>
            </n-upload>
            <n-alert v-if="uploadedFile" type="info" :bordered="false">
              已选择: {{ uploadedFile.name }} ({{ uploadedFile.file ? (uploadedFile.file.size / 1024).toFixed(2) : '0' }} KB)
            </n-alert>
            <n-radio-group v-model:value="importMode">
              <n-space>
                <n-radio value="replace" label="替换模式" />
                <n-radio value="append" label="追加模式" />
                <n-radio value="update" label="更新模式" />
              </n-space>
            </n-radio-group>
            <n-button type="primary" :disabled="!uploadedFile" :loading="importLoading" @click="importData">
              🔼 开始导入
            </n-button>
          </n-space>
        </n-gi>
      </n-grid>
    </n-card>

    <!-- 同步冲突解决 -->
    <n-card title="🔄 同步冲突解决" class="section-card">
      <n-space vertical>
        <n-alert type="error" v-if="conflicts.length > 0" :bordered="false">
          检测到 <strong>{{ conflicts.length }}</strong> 个数据同步冲突，需要手动解决！
        </n-alert>
        <n-alert type="success" v-else :bordered="false">
          ✅ 当前无同步冲突
        </n-alert>

        <n-spin :show="conflictsLoading">
          <n-table :bordered="false" v-if="conflicts.length > 0">
            <thead>
              <tr>
                <th>冲突ID</th>
                <th>表名</th>
                <th>记录ID</th>
                <th>源数据库</th>
                <th>目标数据库</th>
                <th>冲突类型</th>
                <th>发生时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="conflict in conflicts" :key="conflict.id">
                <td>{{ conflict.id }}</td>
                <td><n-tag>{{ conflict.table }}</n-tag></td>
                <td>{{ conflict.recordId }}</td>
                <td>{{ conflict.sourceDb }}</td>
                <td>{{ conflict.targetDb }}</td>
                <td>
                  <n-tag :type="getConflictTypeColor(conflict.type)">
                    {{ conflict.type }}
                  </n-tag>
                </td>
                <td>{{ conflict.createdAt }}</td>
                <td>
                  <n-space>
                    <n-button size="small" type="primary" @click="viewConflictDetail(conflict)">
                      查看详情
                    </n-button>
                    <n-button size="small" type="success" @click="resolveConflict(conflict, 'source')">
                      使用源
                    </n-button>
                    <n-button size="small" type="warning" @click="resolveConflict(conflict, 'target')">
                      使用目标
                    </n-button>
                    <n-button size="small" type="error" @click="resolveConflict(conflict, 'manual')">
                      手动解决
                    </n-button>
                  </n-space>
                </td>
              </tr>
            </tbody>
          </n-table>
          <n-empty v-else description="当前没有未解决的冲突" />
        </n-spin>

        <n-space>
          <n-button @click="scanConflicts">🔍 扫描新冲突</n-button>
          <n-button type="error" @click="resolveAllConflicts">⚡ 批量解决（使用最新数据）</n-button>
        </n-space>
      </n-space>
    </n-card>

    <!-- SQL 执行器 -->
    <n-card title="💻 高级 SQL 执行器" class="section-card">
      <n-space vertical>
        <n-alert type="warning" title="⚠️ 高级功能" :bordered="false">
          仅限高级管理员使用，错误的 SQL 可能导致数据丢失！
        </n-alert>
        
        <n-select v-model:value="sqlTargetDb" :options="databaseOptions" placeholder="选择目标数据库" />
        
        <n-input
          v-model:value="sqlQuery"
          type="textarea"
          placeholder="输入 SQL 语句..."
          :rows="8"
          :autosize="{ minRows: 8, maxRows: 20 }"
        />
        
        <n-space>
          <n-button type="primary" :loading="sqlLoading" @click="executeSql">▶️ 执行 SQL</n-button>
          <n-button :loading="sqlLoading" @click="explainSql">📊 EXPLAIN 分析</n-button>
          <n-button @click="formatSql">🎨 格式化</n-button>
          <n-button type="error" @click="clearSql">🗑️ 清空</n-button>
        </n-space>

        <n-card v-if="sqlResult" title="执行结果" size="small">
          <n-code :code="JSON.stringify(sqlResult, null, 2)" language="json" />
        </n-card>
      </n-space>
    </n-card>

    <!-- 系统维护工具 -->
    <n-card title="🛠️ 系统维护工具" class="section-card">
      <n-grid :cols="3" :x-gap="15" :y-gap="15">
        <n-gi>
          <n-card title="🧹 数据清理" size="small">
            <n-space vertical>
              <n-button block @click="cleanupExpiredSessions">清理过期会话</n-button>
              <n-button block @click="cleanupDeletedRecords">清理已删除记录</n-button>
              <n-button block @click="cleanupTempFiles">清理临时文件</n-button>
              <n-button block type="warning" @click="vacuum">VACUUM 优化</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="📊 索引管理" size="small">
            <n-space vertical>
              <n-button block @click="analyzeIndexes">分析索引使用率</n-button>
              <n-button block @click="rebuildIndexes">重建索引</n-button>
              <n-button block @click="suggestIndexes">智能索引建议</n-button>
              <n-button block type="primary" @click="optimizeTables">优化表结构</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="🔐 安全审计" size="small">
            <n-space vertical>
              <n-button block @click="viewAuditLogs">查看审计日志</n-button>
              <n-button block @click="exportAuditLogs">导出审计日志</n-button>
              <n-button block type="warning" @click="detectAnomalies">检测异常行为</n-button>
              <n-button block type="error" @click="lockSuspiciousUsers">锁定可疑用户</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="📈 性能优化" size="small">
            <n-space vertical>
              <n-button block @click="analyzeSlowQueries">慢查询分析</n-button>
              <n-button block @click="cacheWarming">预热缓存</n-button>
              <n-button block @click="adjustConnPool">调整连接池</n-button>
              <n-button block type="primary" @click="autoOptimize">自动优化</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="💾 备份恢复" size="small">
            <n-space vertical>
              <n-button block type="primary" @click="createBackup">创建备份</n-button>
              <n-button block @click="viewBackups">查看备份列表</n-button>
              <n-button block type="warning" @click="restoreBackup">恢复备份</n-button>
              <n-button block @click="scheduleBackup">定时备份设置</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="🔄 同步管理" size="small">
            <n-space vertical>
              <n-button block @click="forceSyncAll">强制全量同步</n-button>
              <n-button block @click="pauseSync">暂停同步</n-button>
              <n-button block @click="resumeSync">恢复同步</n-button>
              <n-button block type="primary" @click="configureSyncRules">配置同步规则</n-button>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
    </n-card>

    <!-- 冲突详情弹窗 -->
    <n-modal v-model:show="showConflictModal" preset="card" title="冲突详情" style="width: 800px">
      <n-grid :cols="2" :x-gap="20" v-if="currentConflict">
        <n-gi>
          <h4>源数据 ({{ currentConflict.sourceDb }})</h4>
          <n-code :code="JSON.stringify(currentConflict.sourceData, null, 2)" language="json" />
        </n-gi>
        <n-gi>
          <h4>目标数据 ({{ currentConflict.targetDb }})</h4>
          <n-code :code="JSON.stringify(currentConflict.targetData, null, 2)" language="json" />
        </n-gi>
      </n-grid>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type { UploadFileInfo } from 'naive-ui'
import { useMessage } from 'naive-ui'

import { http as api } from '@/lib/http'

interface ConflictRow {
  id: number
  table: string
  recordId: string
  sourceDb: string
  targetDb: string
  type: string
  createdAt: string
  sourceData: Record<string, unknown>
  targetData: Record<string, unknown>
}

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

// 批量商品操作
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
  { label: '商品数据', value: 'items' },
  { label: '交易数据', value: 'transactions' },
  { label: '评论数据', value: 'comments' },
  { label: '消息数据', value: 'messages' },
  { label: '审计日志', value: 'audit_logs' }
]

// 同步冲突
const conflicts = ref<ConflictRow[]>([])
const conflictsLoading = ref(false)
const showConflictModal = ref(false)
const currentConflict = ref<ConflictRow | null>(null)

// SQL 执行器
const sqlTargetDb = ref<'MySQL' | 'PostgreSQL' | 'MariaDB' | 'SQLite'>('MySQL')
const sqlQuery = ref('')
const sqlResult = ref<any>(null)
const sqlLoading = ref(false)

const databaseOptions = [
  { label: 'MySQL', value: 'MySQL' },
  { label: 'PostgreSQL', value: 'PostgreSQL' },
  { label: 'MariaDB', value: 'MariaDB' },
  { label: 'SQLite', value: 'SQLite' }
]

const DB_VALUE_MAP: Record<string, 'mysql' | 'postgres' | 'mariadb' | 'sqlite'> = {
  MySQL: 'mysql',
  PostgreSQL: 'postgres',
  MariaDB: 'mariadb',
  SQLite: 'sqlite'
}

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
    handleError(error, '无法获取商品数量')
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
    message.success(`成功处理 ${data.affected} 件商品`)
    fetchItemEstimate()
  } catch (error) {
    handleError(error, '批量商品操作失败')
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

const fetchConflicts = async () => {
  conflictsLoading.value = true
  try {
    const { data } = await api.get<{ conflicts: any[] }>(
      '/sync/conflicts',
      {
      params: { resolved: false, page: 1, page_size: 50 }
      }
    )
    const rows = data.conflicts ?? []
    conflicts.value = rows.map((item: any) => ({
      id: item.id,
      table: item.table_name,
      recordId: item.record_id,
      sourceDb: item.source,
      targetDb: item.target,
      type: item.payload?.type || 'unknown',
      createdAt: item.created_at,
      sourceData: item.payload?.local || {},
      targetData: item.payload?.remote || {}
    }))
  } catch (error) {
    handleError(error, '获取冲突列表失败')
  } finally {
    conflictsLoading.value = false
  }
}

const scanConflicts = () => fetchConflicts()

const viewConflictDetail = (conflict: ConflictRow) => {
  currentConflict.value = conflict
  showConflictModal.value = true
}

const resolveConflict = async (conflict: ConflictRow, strategy: 'source' | 'target' | 'manual') => {
  try {
    await api.put(`/sync/conflicts/${conflict.id}/resolve`, { strategy })
    message.success(`冲突 ${conflict.id} 已解决`)
    await fetchConflicts()
  } catch (error) {
    handleError(error, '解决冲突失败')
  }
}

const resolveAllConflicts = async () => {
  if (!conflicts.value.length) {
    message.info('当前无待解决冲突')
    return
  }
  for (const conflict of conflicts.value) {
    try {
      await api.put(`/sync/conflicts/${conflict.id}/resolve`, { strategy: 'manual' })
    } catch (error) {
      handleError(error, `冲突 ${conflict.id} 处理失败`)
      return
    }
  }
  message.success('所有冲突已标记为解决')
  fetchConflicts()
}

const getConflictTypeColor = (type: string) => {
  if (type.includes('version') || type.includes('版本')) return 'warning'
  if (type.includes('inconsistent') || type.includes('不一致')) return 'error'
  return 'info'
}

const runSql = async (mode: 'run' | 'explain') => {
  if (!sqlQuery.value.trim()) {
    message.warning('请输入 SQL 语句')
    return
  }
  sqlLoading.value = true
  try {
    const { data } = await api.post('/admin/operations/sql', {
      database: DB_VALUE_MAP[sqlTargetDb.value],
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

type MaintenanceTaskKey =
  | 'cleanup_expired_sessions'
  | 'cleanup_deleted_records'
  | 'cleanup_temp_files'
  | 'vacuum_tables'
  | 'analyze_indexes'
  | 'rebuild_indexes'
  | 'suggest_indexes'
  | 'optimize_tables'
  | 'view_audit_logs'
  | 'export_audit_logs'
  | 'detect_anomalies'
  | 'lock_suspicious_users'
  | 'analyze_slow_queries'
  | 'cache_warming'
  | 'adjust_connection_pool'
  | 'auto_optimize'
  | 'create_backup'
  | 'view_backups'
  | 'restore_backup'
  | 'schedule_backup'

const runMaintenanceTask = async (task: MaintenanceTaskKey, successText: string) => {
  try {
    const { data } = await api.post('/admin/operations/maintenance', { task })
    const affected = data?.affected_rows ?? 0
    const messageText = data?.message || successText
    message.success(`${messageText}${affected ? `（影响 ${affected} 行）` : ''}`)
  } catch (error) {
    handleError(error, `${successText}失败`)
  }
}

// 系统维护工具（接入后台任务）
const cleanupExpiredSessions = () => runMaintenanceTask('cleanup_expired_sessions', '过期会话清理任务已提交')
const cleanupDeletedRecords = () => runMaintenanceTask('cleanup_deleted_records', '已提交删除记录清理任务')
const cleanupTempFiles = () => runMaintenanceTask('cleanup_temp_files', '临时文件清理完成')
const vacuum = () => runMaintenanceTask('vacuum_tables', 'VACUUM 优化任务已记录')
const analyzeIndexes = () => runMaintenanceTask('analyze_indexes', '索引分析任务已发起')
const rebuildIndexes = () => runMaintenanceTask('rebuild_indexes', '索引重建执行中')
const suggestIndexes = () => runMaintenanceTask('suggest_indexes', '索引建议报告已生成')
const optimizeTables = () => runMaintenanceTask('optimize_tables', '表结构优化已提交')
const viewAuditLogs = () => runMaintenanceTask('view_audit_logs', '已获取最新审计日志')
const exportAuditLogs = () => runMaintenanceTask('export_audit_logs', '审计日志导出任务已提交')
const detectAnomalies = () => runMaintenanceTask('detect_anomalies', '已触发异常检测')
const lockSuspiciousUsers = () => runMaintenanceTask('lock_suspicious_users', '可疑用户已锁定')
const analyzeSlowQueries = () => runMaintenanceTask('analyze_slow_queries', '慢查询分析任务已执行')
const cacheWarming = () => runMaintenanceTask('cache_warming', '缓存预热已启动')
const adjustConnPool = () => runMaintenanceTask('adjust_connection_pool', '连接池参数调整请求已发送')
const autoOptimize = () => runMaintenanceTask('auto_optimize', '自动优化策略已执行')
const createBackup = () => runMaintenanceTask('create_backup', '备份任务已加入队列')
const viewBackups = () => runMaintenanceTask('view_backups', '已拉取备份信息')
const restoreBackup = () => runMaintenanceTask('restore_backup', '恢复任务已启动，请关注进度')
const scheduleBackup = () => runMaintenanceTask('schedule_backup', '定时备份计划已更新')

const forceSyncAll = async () => {
  try {
    await api.post('/sync/run')
    message.success('已触发全量同步任务')
  } catch (error) {
    handleError(error, '触发全量同步失败')
  }
}

const pauseSync = () => message.info('同步暂停功能待实现')
const resumeSync = () => message.info('同步恢复功能待实现')
const configureSyncRules = () => message.info('请前往同步设置页面配置规则')

onMounted(() => {
  fetchConflicts()
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
