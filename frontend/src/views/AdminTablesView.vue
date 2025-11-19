<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NTabs, NTabPane, NSelect, useMessage } from 'naive-ui'
import AdminTableManager from '../components/AdminTableManager.vue'

const message = useMessage()

const activeTab = ref('users')

// 25张表的配置
const tables = [
  // 核心业务表
  { key: 'users', label: '用户管理', endpoint: '/api/admin/tables/users' },
  { key: 'categories', label: '分类管理', endpoint: '/api/admin/tables/categories' },
  { key: 'items', label: '商品管理', endpoint: '/api/admin/tables/items' },
  { key: 'item_images', label: '商品图片', endpoint: '/api/admin/tables/item_images' },
  { key: 'comments', label: '评论管理', endpoint: '/api/admin/tables/comments' },
  { key: 'transactions', label: '交易管理', endpoint: '/api/admin/tables/transactions' },
  { key: 'messages', label: '消息管理', endpoint: '/api/admin/tables/messages' },
  { key: 'favorites', label: '收藏管理', endpoint: '/api/admin/tables/favorites' },
  { key: 'reports', label: '举报管理', endpoint: '/api/admin/tables/reports' },
  
  // 系统管理表
  { key: 'audit_logs', label: '审计日志', endpoint: '/api/admin/tables/audit_logs' },
  { key: 'conflict_records', label: '冲突记录', endpoint: '/api/admin/tables/conflict_records' },
  { key: 'system_configs', label: '系统配置', endpoint: '/api/admin/tables/system_configs' },
  
  // 扩展关联表
  { key: 'user_follows', label: '用户关注', endpoint: '/api/admin/tables/user_follows' },
  { key: 'item_view_history', label: '浏览历史', endpoint: '/api/admin/tables/item_view_history' },
  { key: 'user_addresses', label: '用户地址', endpoint: '/api/admin/tables/user_addresses' },
  { key: 'item_price_history', label: '价格历史', endpoint: '/api/admin/tables/item_price_history' },
  { key: 'comment_likes', label: '评论点赞', endpoint: '/api/admin/tables/comment_likes' },
  { key: 'message_attachments', label: '消息附件', endpoint: '/api/admin/tables/message_attachments' },
  { key: 'report_actions', label: '举报处理', endpoint: '/api/admin/tables/report_actions' },
  { key: 'transaction_review_images', label: '评价图片', endpoint: '/api/admin/tables/transaction_review_images' },
  { key: 'notifications', label: '通知管理', endpoint: '/api/admin/tables/notifications' },
  { key: 'search_history', label: '搜索历史', endpoint: '/api/admin/tables/search_history' },
  { key: 'credit_score_history', label: '信用分历史', endpoint: '/api/admin/tables/credit_score_history' },
  { key: 'sync_tasks', label: '同步任务', endpoint: '/api/admin/tables/sync_tasks' },
  { key: 'performance_metrics', label: '性能指标', endpoint: '/api/admin/tables/performance_metrics' },
]

const tableOptions = tables.map(t => ({ label: t.label, value: t.key }))

const getCurrentTable = () => {
  return tables.find(t => t.key === activeTab.value)
}
</script>

<template>
  <div class="admin-tables-page">
    <n-card title="数据表管理">
      <template #header-extra>
        <n-select
          v-model:value="activeTab"
          :options="tableOptions"
          style="width: 200px"
          placeholder="选择数据表"
        />
      </template>

      <AdminTableManager
        v-if="getCurrentTable()"
        :key="activeTab"
        :table-name="activeTab"
        :api-endpoint="getCurrentTable()!.endpoint"
      />
    </n-card>
  </div>
</template>

<style scoped>
.admin-tables-page {
  padding: 24px;
  height: 100%;
}
</style>
