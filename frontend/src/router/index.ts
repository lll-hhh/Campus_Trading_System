import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

// 布局组件
import UserLayout from '@/components/UserLayout.vue';
import AdminLayout from '@/components/AdminLayout.vue';

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
import LoginView from '@/views/LoginView.vue';
import ItemDetailView from '@/views/ItemDetailView.vue';
import PublishItemView from '@/views/PublishItemView.vue';
import SearchResultsView from '@/views/SearchResultsView.vue';
import NotFoundView from '@/views/NotFoundView.vue';
import ForbiddenView from '@/views/ForbiddenView.vue';
import ServerErrorView from '@/views/ServerErrorView.vue';

// 管理员页面
import AdminConsoleView from '@/views/AdminConsoleView.vue';
import AnalyticsView from '@/views/AnalyticsView.vue';
import DashboardView from '@/views/DashboardView.vue';
import SystemSettingsView from '@/views/SystemSettingsView.vue';
import UserManagementView from '@/views/UserManagementView.vue';
import AdminPerformanceView from '@/views/AdminPerformanceView.vue';
import AdminOperationsView from '@/views/AdminOperationsView.vue';
import AdminTablesView from '@/views/AdminTablesView.vue';
import SyncMonitorView from '@/views/SyncMonitorView.vue';

// 1. 引入注册组件
import RegisterView from '@/views/RegisterView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ✅ 修改根路径：根据角色重定向
    {
      path: '/',
      name: 'home',
      redirect: () => {
        const authStore = useAuthStore();
        if (authStore.isAdmin) {
          return '/admin/dashboard';  // 管理员进入后台
        }
        return '/marketplace';  // 普通用户进入市场
      }
    },
    
    // ========== 登录/注册页面（无布局） ==========
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: '登录', public: true }
    },
    // 2. 添加注册路由
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { title: '注册', public: true }
    },
    
    // ========== 普通用户路由（使用 UserLayout） ==========
    {
      path: '/',
      component: UserLayout,
      children: [
        {
          path: 'marketplace',
          name: 'marketplace',
          component: MarketplaceView,
          meta: { title: '商品市场', icon: '🏪', role: 'user' }
        },
        {
          path: 'item/:id',
          name: 'item-detail',
          component: ItemDetailView,
          meta: { title: '商品详情', icon: '📦', role: 'user' }
        },
        {
          path: 'publish',
          name: 'publish-item',
          component: PublishItemView,
          meta: { title: '发布商品', icon: '📝', role: 'user', requiresAuth: true }
        },
        {
          path: 'cart',
          name: 'cart',
          component: ShoppingCartView,
          meta: { title: '购物车', icon: '🛒', role: 'user', requiresAuth: true }
        },
        {
          path: 'messages',
          name: 'messages',
          component: MessagesView,
          meta: { title: '消息', icon: '💬', role: 'user', requiresAuth: true }
        },
        {
          path: 'my-items',
          name: 'my-items',
          component: MyItemsView,
          meta: { title: '我的商品', icon: '📦', role: 'user', requiresAuth: true }
        },
        {
          path: 'orders',
          name: 'orders',
          component: OrdersView,
          meta: { title: '交易记录', icon: '📝', role: 'user', requiresAuth: true }
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileCenterView,
          meta: { title: '个人中心', icon: '👤', role: 'user', requiresAuth: true }
        },
        {
          path: 'user/profile',
          name: 'user-profile',
          component: UserProfileView,
          meta: { title: '个人主页', icon: '👤', role: 'user', requiresAuth: true }
        },
        {
          path: 'user/settings',
          name: 'user-settings',
          component: UserSettingsView,
          meta: { title: '账号设置', icon: '⚙️', role: 'user', requiresAuth: true }
        },
        {
          path: 'user/favorites',
          name: 'user-favorites',
          component: ProfileCenterView,
          meta: { title: '我的收藏', icon: '❤️', role: 'user', requiresAuth: true }
        },
        {
          path: 'user/search-history',
          name: 'search-history',
          component: SearchHistoryView,
          meta: { title: '搜索历史', icon: '🔍', role: 'user', requiresAuth: true }
        },
        {
          path: 'search',
          name: 'search-results',
          component: SearchResultsView,
          meta: { title: '搜索结果', icon: '🔍', role: 'user' }
        }
      ]
    },
    
    // ========== 管理员路由（使用 AdminLayout） ==========
    {
      path: '/admin',
      component: AdminLayout,
      children: [
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: DashboardView,
          meta: { title: '数据仪表盘', icon: '📊', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'analytics',
          name: 'admin-analytics',
          component: AnalyticsView,
          meta: { title: '数据分析', icon: '📈', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'console',
          name: 'admin-console',
          component: AdminConsoleView,
          meta: { title: '四库同步', icon: '🔄', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'performance',
          name: 'admin-performance',
          component: AdminPerformanceView,
          meta: { title: '性能监控', icon: '⚡', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'operations',
          name: 'admin-operations',
          component: AdminOperationsView,
          meta: { title: '高级操作', icon: '⚙️', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'tables',
          name: 'admin-tables',
          component: AdminTablesView,
          meta: { title: '表格管理', icon: '📋', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'users',
          name: 'admin-users',
          component: UserManagementView,
          meta: { title: '用户管理', icon: '👥', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'settings',
          name: 'admin-settings',
          component: SystemSettingsView,
          meta: { title: '系统设置', icon: '🔧', role: 'admin', requiresAdmin: true }
        },
        {
          path: 'sync-monitor',
          name: 'sync-monitor',
          component: SyncMonitorView,
          meta: { title: '同步监控', icon: '🔄', role: 'admin', requiresAdmin: true }
        }
      ]
    },
    
    // ========== 错误页面 ==========
    {
      path: '/403',
      name: 'forbidden',
      component: ForbiddenView,
      meta: { title: '访问被拒绝', public: true }
    },
    {
      path: '/500',
      name: 'server-error',
      component: ServerErrorView,
      meta: { title: '服务器错误', public: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: { title: '页面不存在', public: true }
    }
  ]
});

// 🔥 修复后的路由守卫
router.beforeEach(async (to, from, next) => {
  // 👇 3. 更新白名单
  const whiteList = ['/login', '/register', '/403', '/500', '/not-found'];
  
  console.group(`🚦 [Router] ${from.path} → ${to.path}`);
  
  try {
    const authStore = useAuthStore();
    // 确保 authStore 已初始化
    if (!authStore.token && localStorage.getItem('token')) {
      authStore.init();
    }
    
    const isAuthenticated = authStore.isAuthenticated;
    const isAdmin = authStore.isAdmin;
    
    console.log('状态:', { 
      isAuthenticated, 
      isAdmin, 
      requiresAuth: to.meta.requiresAuth,
      public: to.meta.public 
    });

    // ============ 规则 1: 访问登录页 ============
    if (to.path === '/login' || to.name === 'login') {
      if (isAuthenticated) {
        console.log('✅ 已登录，重定向到市场');
        next('/marketplace');
      } else {
        console.log('✅ 访问登录页，放行');
        next();
      }
      console.groupEnd();
      return;
    }

    // ============ 规则 2: 白名单页面 ============
    if (whiteList.includes(to.path) || to.meta.public === true) {
      console.log('✅ 白名单/公开页面，放行');
      next();
      console.groupEnd();
      return;
    }

    // ============ 规则 3: 需要登录但未登录 ============
    // 注意：这里我们假设所有非白名单页面默认都需要登录，除非明确标记 public: true
    // 或者你也可以只检查 meta.requiresAuth
    const requiresAuth = to.meta.requiresAuth !== false; // 默认为 true，除非明确设为 false
    
    if (requiresAuth && !isAuthenticated) {
      console.warn('❌ 未登录，重定向到登录页');
      // 避免无限循环：如果已经在登录页，不要再推送到登录页
      if (from.path === '/login') {
        console.error('⚠️ 检测到重定向循环，强制停止');
        return; 
      }
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      });
      console.groupEnd();
      return;
    }

    // ============ 规则 4: 需要管理员权限 ============
    if (to.meta.requiresAdmin === true) {
      if (!isAdmin) {
        console.warn('❌ 权限不足，拒绝访问');
        next('/403');
        console.groupEnd();
        return;
      }
    }

    // ============ 规则 5: 放行所有其他情况 ============
    console.log('✅ 检查通过，放行');
    next();

  } catch (error) {
    console.error('❌ 路由守卫异常:', error);
    // 发生错误时，为了避免死循环，可以尝试跳转到错误页或放行到登录页
    if (to.path !== '/login') {
      next('/login');
    } else {
      next();
    }
  } finally {
    console.groupEnd();
  }
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
