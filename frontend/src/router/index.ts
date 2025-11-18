import { createRouter, createWebHistory } from 'vue-router';

import AdminConsoleView from '@/views/AdminConsoleView.vue';
import AnalyticsView from '@/views/AnalyticsView.vue';
import DashboardView from '@/views/DashboardView.vue';
import MarketSearchView from '@/views/MarketSearchView.vue';
import ProfileCenterView from '@/views/ProfileCenterView.vue';
import SystemSettingsView from '@/views/SystemSettingsView.vue';
import UserManagementView from '@/views/UserManagementView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { title: '数据仪表盘', icon: '📊' }
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: AnalyticsView,
      meta: { title: '数据分析', icon: '📈' }
    },
    {
      path: '/market',
      name: 'market-search',
      component: MarketSearchView,
      meta: { title: '市场搜索', icon: '🔍' }
    },
    {
      path: '/admin',
      name: 'admin-console',
      component: AdminConsoleView,
      meta: { title: '管理控制台', icon: '⚙️' }
    },
    {
      path: '/users',
      name: 'user-management',
      component: UserManagementView,
      meta: { title: '用户管理', icon: '👥', requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/settings',
      name: 'system-settings',
      component: SystemSettingsView,
      meta: { title: '系统设置', icon: '🔧', requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/profile',
      name: 'profile-center',
      component: ProfileCenterView,
      meta: { title: '个人中心', icon: '👤' }
    }
  ]
});

router.beforeEach(async (to, from, next) => {
  console.info('[router] navigating', { from: from.fullPath, to: to.fullPath });
  next();
});

export default router;
