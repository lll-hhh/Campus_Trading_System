<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b bg-white/80 backdrop-blur sticky top-0 z-50">
      <div class="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex items-center gap-4">
          <RouterLink class="text-2xl font-semibold text-indigo-600" to="/">
            🎓 CampuSwap
          </RouterLink>
          <!-- 角色切换开关 -->
          <div class="flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1">
            <span :class="isAdmin ? 'text-gray-400' : 'text-indigo-600 font-bold'">用户</span>
            <button
              @click="toggleRole"
              class="relative w-12 h-6 bg-gray-300 rounded-full transition-colors"
              :class="isAdmin ? 'bg-indigo-600' : 'bg-gray-300'"
            >
              <span
                class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform"
                :class="isAdmin ? 'transform translate-x-6' : ''"
              ></span>
            </button>
            <span :class="isAdmin ? 'text-indigo-600 font-bold' : 'text-gray-400'">管理员</span>
          </div>
        </div>
        
        <nav class="flex flex-wrap items-center gap-2 text-sm text-slate-600">
          <RouterLink
            v-for="item in visibleLinks"
            :key="item.to"
            :to="item.to"
            class="rounded-full px-4 py-2 transition-all"
            :class="isActive(item.to) ? 'bg-indigo-600 text-white' : 'hover:bg-indigo-50 hover:text-indigo-600'"
          >
            {{ item.icon }} {{ item.label }}
          </RouterLink>
        </nav>
        
        <div class="flex items-center gap-3 text-sm">
          <span class="text-slate-500">{{ currentUserName }}</span>
          <button
            class="rounded-full bg-indigo-600 text-white px-4 py-2 hover:bg-indigo-700 transition-colors"
            type="button"
            @click="logout"
          >
            退出
          </button>
        </div>
      </div>
    </header>

    <main>
      <router-view />
    </main>

    <footer class="border-t bg-white mt-12">
      <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-xs text-slate-500">
        <p>© {{ currentYear }} CampuSwap · 校园二手交易平台 + 四库同步管理系统</p>
        <p>FastAPI · Vue 3 · MySQL/MariaDB/PostgreSQL/SQLite · Redis · AI Pricing</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const currentYear = new Date().getFullYear();
const isAdmin = ref(false);

// 普通用户导航
const userLinks = [
  { label: '商品市场', to: '/marketplace', icon: '🏪' },
  { label: '消息', to: '/messages', icon: '💬' },
  { label: '我的商品', to: '/my-items', icon: '📦' },
  { label: '我的订单', to: '/orders', icon: '📝' },
  { label: '个人中心', to: '/profile', icon: '👤' }
];

// 管理员导航
const adminLinks = [
  { label: '数据仪表盘', to: '/admin/dashboard', icon: '📊' },
  { label: '数据分析', to: '/admin/analytics', icon: '📈' },
  { label: '四库同步', to: '/admin/console', icon: '🔄' },
  { label: '用户管理', to: '/admin/users', icon: '👥' },
  { label: '系统设置', to: '/admin/settings', icon: '🔧' }
];

const visibleLinks = computed(() => isAdmin.value ? adminLinks : userLinks);

const currentUserName = computed(() => 
  isAdmin.value ? '管理员 Admin' : '普通用户 张三'
);

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/');
}

function toggleRole() {
  isAdmin.value = !isAdmin.value;
  // 切换角色时自动跳转到对应的首页
  if (isAdmin.value) {
    router.push('/admin/dashboard');
  } else {
    router.push('/marketplace');
  }
}

function logout() {
  alert('退出登录');
}

// 监听路由变化,自动切换角色
watch(() => route.path, (newPath) => {
  if (newPath.startsWith('/admin/')) {
    isAdmin.value = true;
  } else if (!newPath.startsWith('/admin/') && isAdmin.value) {
    // 如果当前是管理员模式,但访问的是用户页面,不自动切换
  }
});
</script>
