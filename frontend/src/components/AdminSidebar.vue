<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { NLayoutSider, NMenu, NSpace, NAvatar, NButton } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const collapsed = ref(false)

const userName = computed(() => authStore.displayName || '管理员')

const menuOptions = [
  {
    label: '📊 数据仪表盘',
    key: 'admin-dashboard',
    path: '/admin/dashboard'
  },
  {
    label: '📈 数据分析',
    key: 'admin-analytics',
    path: '/admin/analytics'
  },
  {
    label: '🔄 四库同步',
    key: 'admin-console',
    path: '/admin/console'
  },
  {
    label: '🔍 同步监控',
    key: 'sync-monitor',
    path: '/admin/sync-monitor'
  },
  {
    label: '⚡ 性能监控',
    key: 'admin-performance',
    path: '/admin/performance'
  },
  {
    label: '⚙️ 高级操作',
    key: 'admin-operations',
    path: '/admin/operations'
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: '📋 表格管理',
    key: 'admin-tables',
    path: '/admin/tables'
  },
  {
    label: '👥 用户管理',
    key: 'admin-users',
    path: '/admin/users'
  },
  {
    label: '🔧 系统设置',
    key: 'admin-settings',
    path: '/admin/settings'
  },
  {
    type: 'divider',
    key: 'd2'
  },
  {
    label: '👤 个人中心',
    key: 'profile',
    path: '/user/profile'
  },
  {
    label: '🏪 返回市场',
    key: 'marketplace',
    path: '/marketplace'
  }
]

const activeKey = computed(() => {
  const path = router.currentRoute.value.path
  const item = menuOptions.find(option => option.path && path.startsWith(option.path))
  return item?.key || 'admin-dashboard'
})

const handleMenuSelect = (key: string) => {
  const item = menuOptions.find(option => option.key === key)
  if (item && item.path) {
    router.push(item.path)
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <n-layout-sider
    bordered
    collapse-mode="width"
    :collapsed-width="64"
    :width="240"
    :collapsed="collapsed"
    show-trigger
    @collapse="collapsed = true"
    @expand="collapsed = false"
    class="admin-sider"
  >
    <div class="sider-content">
      <!-- Logo -->
      <div class="admin-logo">
        <span class="logo-icon">🎓</span>
        <span v-show="!collapsed" class="logo-text">管理后台</span>
      </div>

      <!-- 用户信息 -->
      <div class="admin-user-info">
        <n-space vertical align="center" :size="8">
          <n-avatar round size="large">
            {{ userName.charAt(0) }}
          </n-avatar>
          <div v-show="!collapsed" style="text-align: center">
            <div style="font-weight: 500">{{ userName }}</div>
            <div style="font-size: 12px; color: #999">超级管理员</div>
          </div>
        </n-space>
      </div>

      <!-- 导航菜单 -->
      <n-menu
        v-model:value="activeKey"
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        @update:value="handleMenuSelect"
      />

      <!-- 退出按钮 -->
      <div class="logout-btn">
        <n-button
          type="error"
          secondary
          block
          @click="handleLogout"
        >
          <span v-show="!collapsed">🚪 退出登录</span>
          <span v-show="collapsed">🚪</span>
        </n-button>
      </div>
    </div>
  </n-layout-sider>
</template>

<style scoped>
.admin-sider {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 1000;
}

.sider-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.admin-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
  background: linear-gradient(135deg, #f56c6c 0%, #ff8787 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.admin-user-info {
  padding: 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.logout-btn {
  margin-top: auto;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
