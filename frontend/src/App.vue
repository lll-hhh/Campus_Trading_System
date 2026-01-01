<template>
  <!-- 1. 最外层：配置提供者 -->
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN" :theme-overrides="themeOverrides">
    
    <!-- 2. 第二层：消息提供者 (必须包裹在 router-view 外面) -->
    <n-message-provider>
      <n-dialog-provider>
        <n-loading-bar-provider>
          
          <!-- 3. 应用布局 -->
          <div class="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
            
            <!-- 顶部小条 -->
            <div class="bg-gray-100 py-1 border-b text-[10px] text-gray-500">
              <div class="max-w-7xl mx-auto px-4 flex justify-between items-center">
                <div class="flex items-center gap-4">
                  <span class="flex items-center gap-1"><span class="text-primary">🚚</span> 限时全球免运费</span>
                  <span class="flex items-center gap-1"><span class="text-primary">📞</span> 24/7 客户支持: 400-123-4567</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="cursor-pointer hover:text-primary">追踪订单</span>
                  <span class="cursor-pointer hover:text-primary">帮助中心</span>
                  <span class="cursor-pointer hover:text-primary">语言: 简体中文</span>
                </div>
              </div>
            </div>

            <!-- Logo & 搜索区域 -->
            <div class="bg-white py-6 border-b">
              <div class="max-w-7xl mx-auto px-4 flex items-center justify-between">
                <!-- Logo -->
                <RouterLink class="flex items-center gap-3 group" to="/">
                  <div class="w-12 h-12 bg-primary rounded-full flex items-center justify-center text-white text-2xl font-bold group-hover:rotate-12 transition-transform">
                    P
                  </div>
                  <div>
                    <h1 class="text-2xl font-black tracking-tighter text-dark leading-none">PHOENIX <span class="text-primary">MALL</span></h1>
                    <p class="text-[10px] text-gray-400 font-bold tracking-[0.2em] uppercase">For Auto Parts</p>
                  </div>
                </RouterLink>

                <!-- 搜索框 (简化版) -->
                <div class="hidden md:flex flex-1 max-w-xl mx-10">
                  <div class="relative w-full">
                    <input 
                      type="text" 
                      placeholder="搜索零件编号、名称或品牌..." 
                      class="w-full border-2 border-gray-100 rounded-full py-2 px-6 focus:border-primary outline-none transition-colors text-sm"
                    />
                    <button class="absolute right-2 top-1/2 -translate-y-1/2 bg-primary text-white p-1.5 rounded-full hover:bg-primary/90">
                      <span class="text-sm">🔍</span>
                    </button>
                  </div>
                </div>

                <!-- 右侧功能区 -->
                <div class="flex items-center gap-6">
                  <div class="relative cursor-pointer group">
                    <span class="text-2xl text-dark group-hover:text-primary transition-colors">🛒</span>
                    <span class="absolute -top-2 -right-2 bg-primary text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center border-2 border-white">2</span>
                  </div>
                  <div v-if="isAuthenticated" class="flex items-center gap-3 border-l pl-6">
                    <div class="text-right hidden sm:block">
                      <p class="text-xs font-bold text-dark">{{ currentUserName }}</p>
                      <p class="text-[10px] text-gray-400">{{ isAdmin ? '系统管理员' : '认证商户' }}</p>
                    </div>
                    <n-avatar round size="small" :src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUserName}`" />
                  </div>
                  <RouterLink v-else to="/login" class="bg-dark text-white px-6 py-2 rounded-full text-sm font-bold hover:bg-primary transition-colors">
                    登录 / 注册
                  </RouterLink>
                </div>
              </div>
            </div>

            <!-- 主导航栏 (深色) -->
            <nav v-if="!isLoginPage && !isAdminPage" class="bg-dark sticky top-0 z-50 shadow-lg">
              <div class="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
                <div class="flex items-center gap-1 h-full">
                  <RouterLink
                    v-for="item in visibleLinks"
                    :key="item.to"
                    :to="item.to"
                    class="px-5 h-full flex items-center text-xs font-bold uppercase tracking-wider transition-colors border-b-2 border-transparent"
                    :class="isActive(item.to) ? 'text-primary border-primary bg-white/5' : 'text-gray-300 hover:text-white hover:bg-white/5'"
                  >
                    {{ item.label }}
                  </RouterLink>
                </div>
                
                <div class="flex items-center gap-4">
                  <button v-if="isAuthenticated" @click="logout" class="text-gray-400 hover:text-white text-[10px] font-bold uppercase tracking-widest">
                    退出登录
                  </button>
                  <div class="bg-primary text-white px-4 py-1.5 rounded text-[10px] font-black uppercase tracking-widest cursor-pointer hover:bg-white hover:text-primary transition-colors">
                    促销零件
                  </div>
                </div>
              </div>
            </nav>

            <!-- 4. 核心：路由视图 (页面内容在这里显示) -->
            <main class="flex-1">
              <router-view />
            </main>

            <!-- AI 聊天助手 (悬浮按钮) -->
            <AIChatBox v-if="isAuthenticated && !isAdminPage" />

            <!-- 页脚 (多列) -->
            <footer v-if="!isLoginPage && !isAdminPage" class="bg-dark text-white pt-16 pb-8 border-t border-white/5">
              <div class="max-w-7xl mx-auto px-4">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-16">
                  <!-- 公司信息 -->
                  <div class="lg:col-span-2">
                    <div class="flex items-center gap-2 mb-6">
                      <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white font-bold">P</div>
                      <h2 class="text-xl font-black tracking-tighter">PHOENIX <span class="text-primary">MALL</span></h2>
                    </div>
                    <p class="text-gray-400 text-sm leading-relaxed mb-6 max-w-sm">
                      凤凰汽配商城是全球领先的专业汽车零件交易平台，致力于为全球车主和维修店提供高品质、原厂标准的汽车零部件。我们坚持客户至上，服务第一。
                    </p>
                    <div class="flex gap-4">
                      <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">f</div>
                      <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">t</div>
                      <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">in</div>
                      <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">g+</div>
                    </div>
                  </div>

                  <!-- 快速链接 -->
                  <div>
                    <h3 class="text-sm font-bold uppercase tracking-widest mb-6 border-l-4 border-primary pl-3">制动系统</h3>
                    <ul class="text-gray-400 text-sm space-y-3">
                      <li class="hover:text-primary cursor-pointer transition-colors">刹车片</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">刹车盘</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">制动液</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">制动软管</li>
                    </ul>
                  </div>

                  <div>
                    <h3 class="text-sm font-bold uppercase tracking-widest mb-6 border-l-4 border-primary pl-3">滤清器</h3>
                    <ul class="text-gray-400 text-sm space-y-3">
                      <li class="hover:text-primary cursor-pointer transition-colors">空气滤清器</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">燃油滤清器</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">机油滤清器</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">空调滤清器</li>
                    </ul>
                  </div>

                  <div>
                    <h3 class="text-sm font-bold uppercase tracking-widest mb-6 border-l-4 border-primary pl-3">发动机零件</h3>
                    <ul class="text-gray-400 text-sm space-y-3">
                      <li class="hover:text-primary cursor-pointer transition-colors">火花塞</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">正时皮带</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">气缸垫</li>
                      <li class="hover:text-primary cursor-pointer transition-colors">曲轴</li>
                    </ul>
                  </div>
                </div>

                <div class="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                  <p class="text-gray-500 text-[10px] font-bold uppercase tracking-widest">
                    Copyright © {{ currentYear }} Phoenix Auto Parts Co., Ltd. All rights reserved.
                  </p>
                  <div class="flex gap-6 text-[10px] font-bold uppercase tracking-widest text-gray-500">
                    <span class="hover:text-white cursor-pointer">服务条款</span>
                    <span class="hover:text-white cursor-pointer">隐私政策</span>
                    <span class="hover:text-white cursor-pointer">联系我们</span>
                  </div>
                </div>
              </div>
            </footer>
          </div>

        </n-loading-bar-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { zhCN, dateZhCN, type GlobalThemeOverrides } from 'naive-ui'
import { useAuthStore } from '@/stores/auth' // 🔥 初始化 Store
import { useMessageStore } from '@/stores/message'
import AIChatBox from '@/components/AIChatBox.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore() // 🔥 初始化 Store
const messageStore = useMessageStore()

const currentYear = new Date().getFullYear()

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#82b440',
    primaryColorHover: '#94c651',
    primaryColorPressed: '#719d35',
    primaryColorSuppl: '#82b440',
    borderRadius: '8px'
  },
  Button: {
    borderRadiusMedium: '20px'
  },
  Card: {
    borderRadius: '12px'
  }
}

// 🔥 从 Store 获取真实状态
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isAdmin = computed(() => authStore.isAdmin)
const currentUserName = computed(() => authStore.user?.username || '未登录用户')

// 判断是否在登录页 (登录页通常不显示复杂的 Header)
const isLoginPage = computed(() => route.path === '/login')
// 判断是否在管理员页面
const isAdminPage = computed(() => route.path.startsWith('/admin'))

// 普通用户导航
const userLinks = [
  { label: '汽配市场', to: '/marketplace', icon: '🏪' },
  { label: '零件列表', to: '/marketplace', icon: '📜' },
  { label: '门店网络', to: '/stores', icon: '📍' },
  { label: '采购车', to: '/cart', icon: '🛒' }, 
  { label: '消息', to: '/messages', icon: '💬' },
  { label: '我的库存', to: '/my-items', icon: '📦' },
  { label: '采购订单', to: '/orders', icon: '📝' },
  { label: '商户中心', to: '/user/profile', icon: '👤' }
]

// 管理员导航
const adminLinks = [
  { label: '数据仪表盘', to: '/admin/dashboard', icon: '📊' },
  { label: '数据分析', to: '/admin/analytics', icon: '📈' },
  { label: '商户管理', to: '/admin/users', icon: '👥' },
  { label: '零件审核', to: '/admin/operations', icon: '⚖️' },
  { label: '系统设置', to: '/admin/settings', icon: '🔧' }
]

const visibleLinks = computed(() => isAdmin.value ? adminLinks : userLinks)

// 监听登录状态，启动/停止消息轮询
watch(isAuthenticated, (val) => {
  if (val) {
    messageStore.startPolling()
  } else {
    messageStore.stopPolling()
  }
}, { immediate: true })

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  min-height: 100vh;
}
</style>