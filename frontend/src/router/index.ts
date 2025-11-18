import { createRouter, createWebHistory } from 'vue-router';

// 普通用户页面
import MarketplaceView from '@/views/MarketplaceView.vue';
import MessagesView from '@/views/MessagesView.vue';
import MyItemsView from '@/views/MyItemsView.vue';
import OrdersView from '@/views/OrdersView.vue';
import ProfileCenterView from '@/views/ProfileCenterView.vue';

// 管理员页面
import AdminConsoleView from '@/views/AdminConsoleView.vue';
import AnalyticsView from '@/views/AnalyticsView.vue';
import DashboardView from '@/views/DashboardView.vue';
import SystemSettingsView from '@/views/SystemSettingsView.vue';
import UserManagementView from '@/views/UserManagementView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 普通用户路由
    {
      path: '/',
      redirect: '/marketplace'
    },
    {
      path: '/marketplace',
      name: 'marketplace',
      component: MarketplaceView,
      meta: { title: '商品市场', icon: '🏪', role: 'user' }
    },
    {
      path: '/messages',
      name: 'messages',
      component: MessagesView,
      meta: { title: '消息', icon: '💬', role: 'user' }
    },
    {
      path: '/my-items',
      name: 'my-items',
      component: MyItemsView,
      meta: { title: '我的商品', icon: '�', role: 'user' }
    },
    {
      path: '/orders',
      name: 'orders',
      component: OrdersView,
      meta: { title: '我的订单', icon: '📝', role: 'user' }
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileCenterView,
      meta: { title: '个人中心', icon: '�', role: 'user' }
    },
    
    // 管理员路由
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
      meta: { title: '数据分析', icon: '�', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/console',
      name: 'admin-console',
      component: AdminConsoleView,
      meta: { title: '四库同步', icon: '🔄', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: UserManagementView,
      meta: { title: '用户管理', icon: '�', role: 'admin', requiresAdmin: true }
    },
    {
      path: '/admin/settings',
      name: 'admin-settings',
      component: SystemSettingsView,
      meta: { title: '系统设置', icon: '�', role: 'admin', requiresAdmin: true }
    }
  ]
});

router.beforeEach(async (to, from, next) => {
  console.info('[router] navigating', { from: from.fullPath, to: to.fullPath });
  next();
});

export default router;
