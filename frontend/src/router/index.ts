import { createRouter, createWebHistory } from 'vue-router';

import AdminConsoleView from '@/views/AdminConsoleView.vue';
import DashboardView from '@/views/DashboardView.vue';
import MarketSearchView from '@/views/MarketSearchView.vue';
import ProfileCenterView from '@/views/ProfileCenterView.vue';

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
      component: DashboardView
    },
    {
      path: '/market',
      name: 'market-search',
      component: MarketSearchView
    },
    {
      path: '/admin',
      name: 'admin-console',
      component: AdminConsoleView
    },
    {
      path: '/profile',
      name: 'profile-center',
      component: ProfileCenterView
    }
  ]
});

router.beforeEach(async (to, from, next) => {
  console.info('[router] navigating', { from: from.fullPath, to: to.fullPath });
  next();
});

export default router;
