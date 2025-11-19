<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NCard,
  NDataTable,
  NButton,
  NSpace,
  NInput,
  NSelect,
  NPagination,
  NSwitch,
  NPopconfirm,
  NTag,
  NDrawer,
  NDrawerContent,
  NDescriptions,
  NDescriptionsItem,
  useMessage,
  DataTableColumns,
} from 'naive-ui'
import AdvancedTableFilterPanel, { FilterCondition, TableColumn } from '../components/AdvancedTableFilterPanel.vue'
import api from '../lib/http'

const props = defineProps<{
  tableName: string
  apiEndpoint: string
}>()

const message = useMessage()

// 表格数据
const data = ref<any[]>([])
const loading = ref(false)
const totalRecords = ref(0)
const checkedRowKeys = ref<string[]>([])

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100, 200],
  onChange: (page: number) => {
    pagination.value.page = page
    loadData()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
    loadData()
  },
})

// 排序
const sortState = ref<{ field: string; order: 'asc' | 'desc' } | null>(null)

// 筛选
const filterConditions = ref<FilterCondition[]>([])
const showFilterPanel = ref(false)

// 表格列配置
const columns = ref<TableColumn[]>([])
const dataTableColumns = ref<DataTableColumns<any>>([])

// 详情抽屉
const showDetailDrawer = ref(false)
const selectedRecord = ref<any>(null)

// 表格元数据配置
const tableMetadata = {
  users: {
    title: '用户管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'username', title: '用户名', type: 'string' as const },
      { key: 'email', title: '邮箱', type: 'string' as const },
      { key: 'student_id', title: '学号', type: 'string' as const },
      {
        key: 'role',
        title: '角色',
        type: 'enum' as const,
        enumOptions: [
          { label: '普通用户', value: 'user' },
          { label: '管理员', value: 'admin' },
        ],
      },
      { key: 'credit_score', title: '信用分', type: 'number' as const },
      {
        key: 'is_verified',
        title: '已验证',
        type: 'boolean' as const,
      },
      {
        key: 'is_active',
        title: '激活状态',
        type: 'boolean' as const,
      },
      { key: 'created_at', title: '创建时间', type: 'date' as const },
      { key: 'last_login', title: '最后登录', type: 'date' as const },
    ],
  },
  items: {
    title: '商品管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'title', title: '商品名称', type: 'string' as const },
      { key: 'seller_id', title: '卖家ID', type: 'number' as const },
      { key: 'category_id', title: '分类ID', type: 'number' as const },
      { key: 'price', title: '价格', type: 'number' as const },
      { key: 'original_price', title: '原价', type: 'number' as const },
      {
        key: 'condition_type',
        title: '成色',
        type: 'enum' as const,
        enumOptions: [
          { label: '全新', value: 'brand_new' },
          { label: '99新', value: 'like_new' },
          { label: '95新', value: 'very_good' },
          { label: '9成新', value: 'good' },
          { label: '二手', value: 'used' },
        ],
      },
      {
        key: 'status',
        title: '状态',
        type: 'enum' as const,
        enumOptions: [
          { label: '在售', value: 'available' },
          { label: '预定中', value: 'reserved' },
          { label: '已售出', value: 'sold' },
          { label: '已下架', value: 'removed' },
        ],
      },
      { key: 'views', title: '浏览量', type: 'number' as const },
      { key: 'favorites_count', title: '收藏数', type: 'number' as const },
      { key: 'created_at', title: '发布时间', type: 'date' as const },
      { key: 'updated_at', title: '更新时间', type: 'date' as const },
    ],
  },
  transactions: {
    title: '交易管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'buyer_id', title: '买家ID', type: 'number' as const },
      { key: 'seller_id', title: '卖家ID', type: 'number' as const },
      { key: 'item_id', title: '商品ID', type: 'number' as const },
      { key: 'amount', title: '交易金额', type: 'number' as const },
      {
        key: 'status',
        title: '状态',
        type: 'enum' as const,
        enumOptions: [
          { label: '待确认', value: 'pending' },
          { label: '进行中', value: 'in_progress' },
          { label: '已完成', value: 'completed' },
          { label: '已取消', value: 'cancelled' },
          { label: '退款中', value: 'refunding' },
          { label: '已退款', value: 'refunded' },
        ],
      },
      { key: 'meet_location', title: '交易地点', type: 'string' as const },
      { key: 'meet_time', title: '交易时间', type: 'date' as const },
      { key: 'created_at', title: '创建时间', type: 'date' as const },
      { key: 'completed_at', title: '完成时间', type: 'date' as const },
    ],
  },
  comments: {
    title: '评论管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'item_id', title: '商品ID', type: 'number' as const },
      { key: 'user_id', title: '用户ID', type: 'number' as const },
      { key: 'parent_id', title: '父评论ID', type: 'number' as const },
      { key: 'content', title: '内容', type: 'string' as const },
      {
        key: 'is_seller',
        title: '是否卖家',
        type: 'boolean' as const,
      },
      { key: 'likes_count', title: '点赞数', type: 'number' as const },
      { key: 'created_at', title: '创建时间', type: 'date' as const },
    ],
  },
  messages: {
    title: '消息管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'sender_id', title: '发送者ID', type: 'number' as const },
      { key: 'receiver_id', title: '接收者ID', type: 'number' as const },
      { key: 'content', title: '内容', type: 'string' as const },
      {
        key: 'is_read',
        title: '已读',
        type: 'boolean' as const,
      },
      { key: 'sent_at', title: '发送时间', type: 'date' as const },
      { key: 'read_at', title: '阅读时间', type: 'date' as const },
    ],
  },
  categories: {
    title: '分类管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'name', title: '分类名称', type: 'string' as const },
      { key: 'slug', title: '别名', type: 'string' as const },
      { key: 'icon', title: '图标', type: 'string' as const },
      { key: 'description', title: '描述', type: 'string' as const },
      { key: 'items_count', title: '商品数', type: 'number' as const },
      { key: 'display_order', title: '排序', type: 'number' as const },
    ],
  },
  reports: {
    title: '举报管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'reporter_id', title: '举报人ID', type: 'number' as const },
      { key: 'reported_user_id', title: '被举报人ID', type: 'number' as const },
      { key: 'item_id', title: '商品ID', type: 'number' as const },
      {
        key: 'report_type',
        title: '举报类型',
        type: 'enum' as const,
        enumOptions: [
          { label: '虚假商品', value: 'fake_item' },
          { label: '欺诈行为', value: 'fraud' },
          { label: '违禁物品', value: 'prohibited' },
          { label: '不当内容', value: 'inappropriate' },
          { label: '其他', value: 'other' },
        ],
      },
      {
        key: 'status',
        title: '状态',
        type: 'enum' as const,
        enumOptions: [
          { label: '待处理', value: 'pending' },
          { label: '处理中', value: 'in_progress' },
          { label: '已解决', value: 'resolved' },
          { label: '已驳回', value: 'rejected' },
        ],
      },
      { key: 'reason', title: '举报原因', type: 'string' as const },
      { key: 'created_at', title: '举报时间', type: 'date' as const },
      { key: 'resolved_at', title: '处理时间', type: 'date' as const },
    ],
  },
  favorites: {
    title: '收藏管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'user_id', title: '用户ID', type: 'number' as const },
      { key: 'item_id', title: '商品ID', type: 'number' as const },
      { key: 'created_at', title: '收藏时间', type: 'date' as const },
    ],
  },
  audit_logs: {
    title: '审计日志',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'user_id', title: '用户ID', type: 'number' as const },
      {
        key: 'action',
        title: '操作',
        type: 'enum' as const,
        enumOptions: [
          { label: '创建', value: 'create' },
          { label: '更新', value: 'update' },
          { label: '删除', value: 'delete' },
          { label: '登录', value: 'login' },
          { label: '登出', value: 'logout' },
        ],
      },
      { key: 'table_name', title: '表名', type: 'string' as const },
      { key: 'record_id', title: '记录ID', type: 'number' as const },
      { key: 'ip_address', title: 'IP地址', type: 'string' as const },
      { key: 'user_agent', title: '用户代理', type: 'string' as const },
      { key: 'created_at', title: '时间', type: 'date' as const },
    ],
  },
  conflict_records: {
    title: '冲突记录',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'table_name', title: '表名', type: 'string' as const },
      { key: 'record_id', title: '记录ID', type: 'string' as const },
      { key: 'source_db', title: '源数据库', type: 'string' as const },
      { key: 'target_db', title: '目标数据库', type: 'string' as const },
      {
        key: 'conflict_type',
        title: '冲突类型',
        type: 'enum' as const,
        enumOptions: [
          { label: '版本不匹配', value: 'version_mismatch' },
          { label: '数据不一致', value: 'data_inconsistency' },
          { label: '删除冲突', value: 'delete_conflict' },
        ],
      },
      {
        key: 'status',
        title: '状态',
        type: 'enum' as const,
        enumOptions: [
          { label: '未解决', value: 'unresolved' },
          { label: '已解决', value: 'resolved' },
          { label: '忽略', value: 'ignored' },
        ],
      },
      { key: 'resolved_by', title: '处理人ID', type: 'number' as const },
      { key: 'detected_at', title: '检测时间', type: 'date' as const },
      { key: 'resolved_at', title: '解决时间', type: 'date' as const },
    ],
  },
  notifications: {
    title: '通知管理',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'user_id', title: '用户ID', type: 'number' as const },
      {
        key: 'type',
        title: '类型',
        type: 'enum' as const,
        enumOptions: [
          { label: '系统通知', value: 'system' },
          { label: '交易通知', value: 'transaction' },
          { label: '评论通知', value: 'comment' },
          { label: '消息通知', value: 'message' },
        ],
      },
      { key: 'title', title: '标题', type: 'string' as const },
      { key: 'content', title: '内容', type: 'string' as const },
      {
        key: 'is_read',
        title: '已读',
        type: 'boolean' as const,
      },
      { key: 'created_at', title: '创建时间', type: 'date' as const },
      { key: 'read_at', title: '阅读时间', type: 'date' as const },
    ],
  },
  search_history: {
    title: '搜索历史',
    columns: [
      { key: 'id', title: 'ID', type: 'number' as const },
      { key: 'user_id', title: '用户ID', type: 'number' as const },
      { key: 'keyword', title: '关键词', type: 'string' as const },
      { key: 'results_count', title: '结果数', type: 'number' as const },
      { key: 'created_at', title: '搜索时间', type: 'date' as const },
    ],
  },
}

// 获取表格配置
const getTableConfig = () => {
  return tableMetadata[props.tableName as keyof typeof tableMetadata] || {
    title: props.tableName,
    columns: [],
  }
}

// 初始化列配置
const initColumns = () => {
  const config = getTableConfig()
  columns.value = config.columns

  // 构建DataTable列配置
  dataTableColumns.value = [
    {
      type: 'selection',
    },
    ...config.columns.map((col) => ({
      key: col.key,
      title: col.title,
      sorter: col.type === 'number' || col.type === 'date',
      render: (row: any) => {
        const value = row[col.key]
        if (value === null || value === undefined) return '-'

        if (col.type === 'boolean') {
          return value ? '✓' : '✗'
        } else if (col.type === 'enum' && col.enumOptions) {
          const option = col.enumOptions.find((opt) => opt.value === value)
          return option ? option.label : value
        } else if (col.type === 'date') {
          return new Date(value).toLocaleString('zh-CN')
        }
        return value
      },
    })),
    {
      key: 'actions',
      title: '操作',
      width: 200,
      render: (row: any) => {
        return h(NSpace, null, {
          default: () => [
            h(NButton, { size: 'small', onClick: () => viewDetail(row) }, { default: () => '查看' }),
            h(NButton, { size: 'small', type: 'primary', onClick: () => editRecord(row) }, { default: () => '编辑' }),
            h(NButton, { size: 'small', type: 'error', onClick: () => deleteRecord(row) }, { default: () => '删除' }),
          ],
        })
      },
    },
  ]
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
    }

    // 添加排序参数
    if (sortState.value) {
      params.sort_by = sortState.value.field
      params.sort_order = sortState.value.order
    }

    // 添加筛选参数
    if (filterConditions.value.length > 0) {
      params.filters = JSON.stringify(filterConditions.value)
    }

    const response = await api.get(props.apiEndpoint, { params })
    data.value = response.data.items || []
    totalRecords.value = response.data.total || 0
  } catch (error: any) {
    message.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 应用筛选
const applyFilter = (conditions: FilterCondition[]) => {
  filterConditions.value = conditions
  pagination.value.page = 1
  loadData()
}

// 重置筛选
const resetFilter = () => {
  filterConditions.value = []
  pagination.value.page = 1
  loadData()
}

// 查看详情
const viewDetail = (row: any) => {
  selectedRecord.value = row
  showDetailDrawer.value = true
}

// 编辑记录
const editRecord = (row: any) => {
  message.info(`编辑记录 ID: ${row.id}`)
  // TODO: 实现编辑功能
}

// 删除记录
const deleteRecord = async (row: any) => {
  try {
    await api.delete(`${props.apiEndpoint}/${row.id}`)
    message.success('删除成功')
    loadData()
  } catch (error: any) {
    message.error(error.message || '删除失败')
  }
}

// 批量删除
const batchDelete = async () => {
  if (checkedRowKeys.value.length === 0) {
    message.warning('请先选择要删除的记录')
    return
  }

  try {
    await api.post(`${props.apiEndpoint}/batch-delete`, {
      ids: checkedRowKeys.value,
    })
    message.success(`成功删除 ${checkedRowKeys.value.length} 条记录`)
    checkedRowKeys.value = []
    loadData()
  } catch (error: any) {
    message.error(error.message || '批量删除失败')
  }
}

// 导出数据
const exportData = async () => {
  try {
    const params: any = {}
    if (filterConditions.value.length > 0) {
      params.filters = JSON.stringify(filterConditions.value)
    }

    const response = await api.get(`${props.apiEndpoint}/export`, {
      params,
      responseType: 'blob',
    })

    const url = URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.tableName}_${Date.now()}.csv`
    link.click()
    URL.revokeObjectURL(url)

    message.success('导出成功')
  } catch (error: any) {
    message.error(error.message || '导出失败')
  }
}

// 初始化
onMounted(() => {
  initColumns()
  loadData()
})
</script>

<template>
  <div class="table-manager">
    <n-card :title="getTableConfig().title">
      <template #header-extra>
        <n-space>
          <n-button @click="showFilterPanel = !showFilterPanel">
            {{ showFilterPanel ? '隐藏筛选' : '显示筛选' }}
          </n-button>
          <n-button type="primary" @click="loadData">刷新</n-button>
          <n-button @click="exportData">导出</n-button>
        </n-space>
      </template>

      <!-- 筛选面板 -->
      <div v-if="showFilterPanel" style="margin-bottom: 16px">
        <AdvancedTableFilterPanel
          v-model="filterConditions"
          :columns="columns"
          @apply="applyFilter"
          @reset="resetFilter"
        />
      </div>

      <!-- 批量操作 -->
      <div v-if="checkedRowKeys.length > 0" style="margin-bottom: 16px; padding: 12px; background: #f0f9ff; border: 1px solid #18a058; border-radius: 4px;">
        <n-space align="center" justify="space-between">
          <span>已选择 {{ checkedRowKeys.length }} 条记录</span>
          <n-space>
            <n-popconfirm @positive-click="batchDelete">
              <template #trigger>
                <n-button type="error" size="small">批量删除</n-button>
              </template>
              确定删除选中的 {{ checkedRowKeys.length }} 条记录吗？
            </n-popconfirm>
          </n-space>
        </n-space>
      </div>

      <!-- 数据表格 -->
      <n-data-table
        :columns="dataTableColumns"
        :data="data"
        :loading="loading"
        :row-key="(row: any) => row.id"
        :checked-row-keys="checkedRowKeys"
        @update:checked-row-keys="(keys) => (checkedRowKeys = keys as string[])"
        :pagination="false"
        striped
        :scroll-x="1200"
      />

      <!-- 分页 -->
      <div style="margin-top: 16px; display: flex; justify-content: flex-end">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-count="Math.ceil(totalRecords / pagination.pageSize)"
          :page-sizes="pagination.pageSizes"
          show-size-picker
          :item-count="totalRecords"
          show-quick-jumper
        >
          <template #prefix="{ itemCount }">共 {{ itemCount }} 条</template>
        </n-pagination>
      </div>
    </n-card>

    <!-- 详情抽屉 -->
    <n-drawer v-model:show="showDetailDrawer" :width="600">
      <n-drawer-content title="记录详情">
        <n-descriptions v-if="selectedRecord" :column="1" bordered>
          <n-descriptions-item
            v-for="col in columns"
            :key="col.key"
            :label="col.title"
          >
            {{ selectedRecord[col.key] || '-' }}
          </n-descriptions-item>
        </n-descriptions>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<style scoped>
.table-manager {
  height: 100%;
}
</style>
