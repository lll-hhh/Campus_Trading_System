<script setup lang="ts">
import { ref, computed } from 'vue'
import { NLayout, NLayoutHeader, NLayoutContent, NSpace, NBreadcrumb, NBreadcrumbItem, NButton } from 'naive-ui'
import { useRouter } from 'vue-router'
import AdminSidebar from './AdminSidebar.vue'

const router = useRouter()

const breadcrumbs = computed(() => {
  const path = router.currentRoute.value.path
  const pathSegments = path.split('/').filter(Boolean)
  
  const items = [
    { label: '首页', path: '/admin/dashboard' }
  ]
  
  const routeNameMap: Record<string, string> = {
    'dashboard': '📊 数据仪表盘',
    'analytics': '📈 数据分析',
    'console': '🔄 四库同步',
    'performance': '⚡ 性能监控',
    'operations': '⚙️ 高级操作',
    'tables': '📋 表格管理',
    'users': '👥 用户管理',
    'settings': '🔧 系统设置'
  }
  
  if (pathSegments.length > 1) {
    const currentPage = pathSegments[pathSegments.length - 1]
    const label = routeNameMap[currentPage] || currentPage
    items.push({ label, path })
  }
  
  return items
})

const handleBreadcrumbClick = (path: string) => {
  router.push(path)
}
</script>

<template>
  <n-layout has-sider class="admin-layout">
    <!-- 左侧边栏 -->
    <AdminSidebar />

    <!-- 右侧主内容 -->
    <n-layout>
      <!-- 顶部面包屑 -->
      <n-layout-header bordered class="admin-header">
        <div class="header-content">
          <n-breadcrumb>
            <n-breadcrumb-item
              v-for="(item, index) in breadcrumbs"
              :key="index"
              @click="handleBreadcrumbClick(item.path)"
              class="breadcrumb-item"
            >
              {{ item.label }}
            </n-breadcrumb-item>
          </n-breadcrumb>

          <n-space>
            <n-button secondary circle>
              🔔
            </n-button>
            <n-button secondary circle>
              ⚙️
            </n-button>
            <n-button secondary circle>
              ❓
            </n-button>
          </n-space>
        </div>
      </n-layout-header>

      <!-- 内容区域 -->
      <n-layout-content class="admin-content">
        <div class="content-container">
          <router-view v-slot="{ Component }">
            <transition name="slide-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.admin-header {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  background-color: #fff;
  position: sticky;
  top: 0;
  z-index: 999;
  margin-left: 240px; /* AdminSidebar 宽度 */
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.breadcrumb-item {
  cursor: pointer;
  transition: color 0.2s;
}

.breadcrumb-item:hover {
  color: #f56c6c;
}

.admin-content {
  padding: 24px;
  margin-left: 240px; /* AdminSidebar 宽度 */
  min-height: calc(100vh - 60px);
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面切换动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from {
  transform: translateX(20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

/* 响应式适配侧边栏折叠 */
@media (max-width: 768px) {
  .admin-header,
  .admin-content {
    margin-left: 64px; /* 折叠后的宽度 */
  }
}
</style>
