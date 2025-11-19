import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

// 普通用户页面
import MarketplaceView from '@/views/MarketplaceView.vue';
import MessagesView from '@/views/MessagesView.vue';
import MyItemsView from '@/views/MyItemsView.vue';
import OrdersView from '@/views/OrdersView.vue';
import ProfileCenterView from '@/views/ProfileCenterView.vue';
import UserProfileView from '@/views/UserProfileView.vue';
import ShoppingCartView from '@/views/ShoppingCartView.vue';
import SearchHistoryView from '@/views/SearchHistoryView.vue';
import UserSettingsView from '@/views/UserSettingsView.vue';

// 管理员页面
import AdminConsoleView from '@/views/AdminConsoleView.vue';
import AnalyticsView from '@/views/AnalyticsView.vue';
import DashboardView from '@/views/DashboardView.vue';
import SystemSettingsView from '@/views/SystemSettingsView.vue';
import UserManagementView from '@/views/UserManagementView.vue';
import AdminPerformanceView from '@/views/AdminPerformanceView.vue';
import AdminOperationsView from '@/views/AdminOperationsView.vue';
import AdminTablesView from '@/views/AdminTablesView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 根路径重定向
    {
      path: '/',
      redirect: '/marketplace'
    },
    
    // ========== 普通用户路由 ==========
    {
      path: '/marketplace',
      name: 'marketplace',
      component: MarketplaceView,
      meta: { title: '商品市场', icon: '🏪', role: 'user' }
    },
    {
      path: '/cart',
      name: 'cart',
      component: ShoppingCartView,
      meta: { title: '购物车', icon: '🛒', role: 'user', requiresAuth: true }
    },
    {
      path: '/messages',
      name: 'messages',
      component: MessagesView,
      meta: { title: '消息', icon: '💬', role: 'user', requiresAuth: true }
    },
    {
      path: '/my-items',
      name: 'my-items',
      component: MyItemsView,
      meta: { title: '我的商品', icon: '📦', role: 'user', requiresAuth: true }
    },
    {
      path: '/orders',
      name: 'orders',
      component: OrdersView,
      meta: { title: '交易记录', icon: '📝', role: 'user', requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileCenterView,
      meta: { title: '个人中心', icon: '👤', role: 'user', requiresAuth: true }
    },
    {
      path: '/user/profile',
      name: 'user-profile',
      component: UserProfileView,
      meta: { title: '个人主页', icon: '👤', role: 'user', requiresAuth: true }
    },
    {
      path: '/user/settings',
      name: 'user-settings',
      component: UserSettingsView,
      meta: { title: '账号设置', icon: '⚙️', role: 'user', requiresAuth: true }
    },
    {
      path: '/user/favorites',
      name: 'user-favorites',
      component: ProfileCenterView,
      meta: { title: '我的收藏', icon: '❤️', role: 'user', requiresAuth: true }
    },
    {
      path: '/user/search-history',
      name: 'search-history',
      component: SearchHistoryView,
      meta: { title: '搜索历史', icon: '🔍', role: 'user', requiresAuth: true }
    },
    
    // ========== 管理员路由 ==========
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: DashboardView,
      meta: { title: '数据仪表盘', icon: '📊', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/analytics',
      name: 'admin-analytics',
      component: AnalyticsView,
      meta: { title: '数据分析', icon: '📈', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/console',
      name: 'admin-console',
      component: AdminConsoleView,
      meta: { title: '四库同步', icon: '🔄', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/performance',
      name: 'admin-performance',
      component: AdminPerformanceView,
      meta: { title: '性能监控', icon: '⚡', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/operations',
      name: 'admin-operations',
      component: AdminOperationsView,
      meta: { title: '高级操作', icon: '⚙️', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/tables',
      name: 'admin-tables',
      component: AdminTablesView,
      meta: { title: '表格管理', icon: '📋', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: UserManagementView,
      meta: { title: '用户管理', icon: '👥', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/settings',
      name: 'admin-settings',
      component: SystemSettingsView,
      meta: { title: '系统设置', icon: '🔧', role: 'admin', requiresAdmin: true }
    }
  ]
});

// 路由守卫 - 权限控制
router.beforeEach(async (to, from, next) => {
  console.info('[router] navigating', { from: from.fullPath, to: to.fullPath });
  
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;
  const isAdmin = authStore.isAdmin;
  
  // 检查是否需要登录
  if (to.meta.requiresAuth && !isAuthenticated) {
    console.warn('[router] 需要登录');
    // TODO: 跳转到登录页
    // next('/login');
    next(); // 暂时允许通过
    return;
  }
  
  // 检查管理员权限
  if (to.meta.requiresAdmin && !isAdmin) {
    console.warn('[router] 需要管理员权限');
    // TODO: 显示无权限提示
    next('/marketplace');
    return;
  }
  
  next();
});

// 获取用户路由（用于导航菜单）
export function getUserRoutes() {
  return router.options.routes.filter(route => {
    return route.meta?.role === 'user' && route.path !== '/';
  });
}

// 获取管理员路由（用于导航菜单）
export function getAdminRoutes() {
  return router.options.routes.filter(route => {
    return route.meta?.role === 'admin';
  });
}

export default router;
