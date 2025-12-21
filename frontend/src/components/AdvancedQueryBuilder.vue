<template>
  <n-card title="🔍 高级查询构建器" class="query-builder">
    <n-space vertical size="large">
      <!-- 模板选择 -->
      <n-space align="center">
        <n-text strong>快速开始:</n-text>
        <n-select
          v-model:value="selectedTemplate"
          :options="templateOptions"
          placeholder="选择预定义查询模板"
          style="width: 300px"
          @update:value="loadTemplate"
        />
        <n-button @click="resetQuery" secondary>重置</n-button>
      </n-space>

      <n-divider />

      <!-- 查询配置 -->
      <n-grid :cols="2" :x-gap="20">
        <n-gi>
          <n-form-item label="主表">
            <n-select
              v-model:value="queryConfig.base_table"
              :options="tableOptions"
              placeholder="选择主表"
            />
          </n-form-item>
        </n-gi>
        <n-gi>
          <n-form-item label="排序">
            <n-input
              v-model:value="queryConfig.order_by"
              placeholder="例如: items.created_at DESC"
            />
          </n-form-item>
        </n-gi>
      </n-grid>

      <!-- 关联表配置 -->
      <n-form-item label="关联表 (JOIN)">
        <n-dynamic-input
          v-model:value="queryConfig.joins"
          :on-create="createJoin"
          :min="0"
        >
          <template #default="{ value }">
            <n-space style="width: 100%">
              <n-select
                v-model:value="value.table"
                :options="tableOptions"
                placeholder="表名"
                style="width: 150px"
              />
              <n-select
                v-model:value="value.type"
                :options="joinTypeOptions"
                style="width: 120px"
              />
              <n-input
                v-model:value="value.on"
                placeholder="关联条件: table1.id = table2.fk_id"
                style="flex: 1"
              />
            </n-space>
          </template>
        </n-dynamic-input>
      </n-form-item>

      <!-- 列选择 -->
      <n-form-item label="查询列">
        <n-dynamic-input
          v-model:value="queryConfig.columns"
          :on-create="createColumn"
          :min="1"
        >
          <template #default="{ value }">
            <n-space style="width: 100%">
              <n-input
                v-model:value="value.table"
                placeholder="表名（可选）"
                style="width: 120px"
              />
              <n-input
                v-model:value="value.name"
                placeholder="列名或表达式"
                style="width: 200px"
              />
              <n-input
                v-model:value="value.alias"
                placeholder="别名（可选）"
                style="width: 150px"
              />
            </n-space>
          </template>
        </n-dynamic-input>
      </n-form-item>

      <!-- WHERE条件 -->
      <n-form-item label="筛选条件 (WHERE)">
        <n-input
          v-model:value="queryConfig.where"
          type="textarea"
          :rows="2"
          placeholder="例如: items.status = 'available' AND items.price > 100"
        />
      </n-form-item>

      <!-- SQL预览 -->
      <n-collapse>
        <n-collapse-item title="📄 SQL预览" name="sql">
          <n-code :code="previewSQL" language="sql" :word-wrap="true" />
        </n-collapse-item>
      </n-collapse>

      <!-- 操作按钮 -->
      <n-space justify="end">
        <n-button @click="exportResults" :disabled="!resultData.length">
          导出CSV
        </n-button>
        <n-button type="primary" @click="executeQuery" :loading="loading">
          <template #icon>
            <n-icon><SearchOutline /></n-icon>
          </template>
          执行查询
        </n-button>
      </n-space>

      <!-- 查询结果 -->
      <template v-if="resultData.length > 0">
        <n-divider />
        <n-space vertical>
          <n-text strong>查询结果 (共 {{ totalRecords }} 条)</n-text>
          <n-data-table
            :columns="resultColumns"
            :data="resultData"
            :loading="loading"
            :pagination="paginationConfig"
            :scroll-x="1200"
          />
        </n-space>
      </template>

      <n-empty v-else-if="!loading && executed" description="查询无结果" />
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage, type DataTableColumns } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'
import { http as api } from '@/lib/http'

const message = useMessage()

interface JoinConfig {
  table: string
  type: string
  on: string
  alias?: string
}

interface ColumnConfig {
  table?: string
  name: string
  alias?: string
}

interface QueryConfig {
  base_table: string
  columns: ColumnConfig[]
  joins: JoinConfig[]
  where?: string
  group_by?: string
  order_by?: string
  page: number
  page_size: number
}

// 查询配置
const queryConfig = ref<QueryConfig>({
  base_table: '',
  columns: [{ name: '*' }],
  joins: [],
  where: '',
  order_by: '',
  page: 1,
  page_size: 20
})

// 模板
const selectedTemplate = ref<string | null>(null)
const templates = ref<any[]>([])
const templateOptions = computed(() =>
  templates.value.map(t => ({
    label: t.name,
    value: t.name
  }))
)

// 表选项
const availableTables = ref<string[]>([])
const tableOptions = computed(() =>
  availableTables.value.map(t => ({
    label: t,
    value: t
  }))
)

const joinTypeOptions = [
  { label: 'INNER JOIN', value: 'INNER' },
  { label: 'LEFT JOIN', value: 'LEFT' },
  { label: 'RIGHT JOIN', value: 'RIGHT' }
]

// 查询结果
const loading = ref(false)
const executed = ref(false)
const resultData = ref<any[]>([])
const resultColumns = ref<DataTableColumns<any>>([])
const totalRecords = ref(0)

const paginationConfig = computed(() => ({
  page: queryConfig.value.page,
  pageSize: queryConfig.value.page_size,
  itemCount: totalRecords.value,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (page: number) => {
    queryConfig.value.page = page
    executeQuery()
  },
  onUpdatePageSize: (pageSize: number) => {
    queryConfig.value.page_size = pageSize
    queryConfig.value.page = 1
    executeQuery()
  }
}))

// SQL预览
const previewSQL = computed(() => {
  if (!queryConfig.value.base_table) return '-- 请先选择主表'
  
  const cols = queryConfig.value.columns
    .map(c => {
      let expr = c.table ? `${c.table}.${c.name}` : c.name
      if (c.alias) expr += ` AS ${c.alias}`
      return expr
    })
    .join(', ')
  
  let sql = `SELECT ${cols || '*'}\nFROM ${queryConfig.value.base_table}`
  
  if (queryConfig.value.joins.length > 0) {
    queryConfig.value.joins.forEach(j => {
      sql += `\n${j.type} JOIN ${j.table} ON ${j.on}`
    })
  }
  
  if (queryConfig.value.where) {
    sql += `\nWHERE ${queryConfig.value.where}`
  }
  
  if (queryConfig.value.order_by) {
    sql += `\nORDER BY ${queryConfig.value.order_by}`
  }
  
  sql += `\nLIMIT ${queryConfig.value.page_size} OFFSET ${(queryConfig.value.page - 1) * queryConfig.value.page_size}`
  
  return sql
})

// 创建JOIN
const createJoin = (): JoinConfig => ({
  table: '',
  type: 'LEFT',
  on: ''
})

// 创建列
const createColumn = (): ColumnConfig => ({
  name: ''
})

// 加载模板
const loadTemplate = (templateName: string) => {
  const template = templates.value.find(t => t.name === templateName)
  if (template && template.request) {
    queryConfig.value = {
      ...template.request,
      page: 1,
      page_size: 20
    }
    message.success(`已加载模板: ${templateName}`)
  }
}

// 执行查询
const executeQuery = async () => {
  if (!queryConfig.value.base_table) {
    message.warning('请选择主表')
    return
  }

  loading.value = true
  executed.value = true
  try {
    const response = await api.post('/admin/query/execute', queryConfig.value)
    
    resultData.value = response.data.data || []
    totalRecords.value = response.data.total || 0
    
    // 动态生成列
    if (resultData.value.length > 0) {
      const firstRow = resultData.value[0]
      resultColumns.value = Object.keys(firstRow).map(key => ({
        key,
        title: key,
        width: 150,
        ellipsis: { tooltip: true }
      }))
    }
    
    message.success(`查询成功，共 ${totalRecords.value} 条记录`)
  } catch (error: any) {
    message.error(error.response?.data?.detail || '查询失败')
    resultData.value = []
    resultColumns.value = []
  } finally {
    loading.value = false
  }
}

// 重置查询
const resetQuery = () => {
  queryConfig.value = {
    base_table: '',
    columns: [{ name: '*' }],
    joins: [],
    where: '',
    order_by: '',
    page: 1,
    page_size: 20
  }
  selectedTemplate.value = null
  resultData.value = []
  resultColumns.value = []
  executed.value = false
  message.info('已重置查询')
}

// 导出结果
const exportResults = () => {
  if (!resultData.value.length) return
  
  const headers = Object.keys(resultData.value[0])
  const csv = [
    headers.join(','),
    ...resultData.value.map(row =>
      headers.map(h => JSON.stringify(row[h] ?? '')).join(',')
    )
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `query_result_${Date.now()}.csv`
  link.click()
  URL.revokeObjectURL(url)
  
  message.success('导出成功')
}

// 加载模板列表
const loadTemplates = async () => {
  try {
    const response = await api.get('/admin/query/templates')
    templates.value = response.data.templates || []
  } catch (error) {
    console.error('加载模板失败:', error)
  }
}

// 加载可用表列表
const loadTables = async () => {
  try {
    const response = await api.get('/admin/query/tables')
    availableTables.value = response.data.tables || []
  } catch (error) {
    console.error('加载表列表失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadTemplates()
  loadTables()
})
</script>

<style scoped>
.query-builder {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
