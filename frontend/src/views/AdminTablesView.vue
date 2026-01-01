<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NTabs, NTabPane, NSelect, useMessage } from 'naive-ui'
import AdminTableManager from '../components/AdminTableManager.vue'

const message = useMessage()
const route = useRoute()
const router = useRouter()

const activeTab = ref('users')

// 25张表的配置
const tables = [
  // 核心业务表
  { key: 'users', label: '用户管理', endpoint: '/admin/tables/users' },
  { key: 'user_profiles', label: '用户档案', endpoint: '/admin/tables/user_profiles' },
  { key: 'categories', label: '分类管理', endpoint: '/admin/tables/categories' },
  { key: 'items', label: '零件管理', endpoint: '/admin/tables/items' },
  { key: 'item_images', label: '零件图片', endpoint: '/admin/tables/item_images' },
  { key: 'comments', label: '评论管理', endpoint: '/admin/tables/comments' },
  { key: 'transactions', label: '交易管理', endpoint: '/admin/tables/transactions' },
  { key: 'messages', label: '消息管理', endpoint: '/admin/tables/messages' },
  { key: 'favorites', label: '收藏管理', endpoint: '/admin/tables/favorites' },
  { key: 'reports', label: '举报管理', endpoint: '/admin/tables/reports' },
  
  // 系统管理表
  { key: 'audit_logs', label: '审计日志', endpoint: '/admin/tables/audit_logs' },
  { key: 'system_configs', label: '系统配置', endpoint: '/admin/tables/system_configs' },
  { key: 'system_settings', label: '系统设置', endpoint: '/admin/tables/system_settings' },
  { key: 'roles', label: '角色管理', endpoint: '/admin/tables/roles' },
  { key: 'permissions', label: '权限管理', endpoint: '/admin/tables/permissions' },
  { key: 'role_permissions', label: '角色权限关联', endpoint: '/admin/tables/role_permissions' },
  
  // 扩展关联表
  { key: 'user_follows', label: '用户关注', endpoint: '/admin/tables/user_follows' },
  { key: 'item_view_history', label: '浏览历史', endpoint: '/admin/tables/item_view_history' },
  { key: 'user_addresses', label: '用户地址', endpoint: '/admin/tables/user_addresses' },
  { key: 'item_price_history', label: '价格历史', endpoint: '/admin/tables/item_price_history' },
  { key: 'comment_likes', label: '评论点赞', endpoint: '/admin/tables/comment_likes' },
  { key: 'message_attachments', label: '消息附件', endpoint: '/admin/tables/message_attachments' },
  { key: 'report_actions', label: '举报处理', endpoint: '/admin/tables/report_actions' },
  { key: 'transaction_review_images', label: '评价图片', endpoint: '/admin/tables/transaction_review_images' },
  { key: 'notifications', label: '通知管理', endpoint: '/admin/tables/notifications' },
  { key: 'search_history', label: '搜索历史', endpoint: '/admin/tables/search_history' },
  { key: 'credit_score_history', label: '信用分历史', endpoint: '/admin/tables/credit_score_history' },
  { key: 'performance_metrics', label: '性能指标', endpoint: '/admin/tables/performance_metrics' },
]

const tableOptions = tables.map(t => ({ label: t.label, value: t.key }))

const getCurrentTable = () => {
  return tables.find(t => t.key === activeTab.value)
}

const syncQueryToTab = (value: string | undefined) => {
  if (!value) return
  const exists = tables.find(t => t.key === value)
  if (exists && activeTab.value !== value) {
    activeTab.value = value
  }
}

onMounted(() => {
  syncQueryToTab(route.query.table as string | undefined)
})

watch(() => route.query.table, (val) => {
  syncQueryToTab(val as string | undefined)
})

watch(activeTab, (value) => {
  if (route.query.table === value) return
  router.replace({ query: { ...route.query, table: value } })
})
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
