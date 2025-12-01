<script setup lang="ts">
import { ref, computed, h } from 'vue'  // ✅ 添加 h
import { useRouter, RouterLink } from 'vue-router'  // ✅ 添加 RouterLink
import { NLayout, NLayoutHeader, NMenu, NButton, NSpace, NAvatar, NDropdown, NBadge } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import SearchAutocomplete from './SearchAutocomplete.vue'
import NotificationCenter from './NotificationCenter.vue'

const router = useRouter()
const authStore = useAuthStore()

const searchKeyword = ref('')
const unreadMessages = ref(5)

const isLoggedIn = computed(() => authStore.isAuthenticated)
const userName = computed(() => authStore.user?.displayName || authStore.user?.username || '用户')

// ✅ 修复：使用正确的 n-menu options 格式
const menuOptions = computed(() => [
  {
    label: () => h(RouterLink, { to: '/marketplace' }, { default: () => '🏪 商品市场' }),
    key: 'marketplace'
  },
  {
    label: () => h(RouterLink, { to: '/cart' }, { default: () => '🛒 购物车' }),
    key: 'cart'
  },
  {
    label: () => h(RouterLink, { to: '/my-items' }, { default: () => '📦 我的商品' }),
    key: 'my-items'
  },
  {
    label: () => h(RouterLink, { to: '/orders' }, { default: () => '📝 交易记录' }),
    key: 'orders'
  },
  {
    label: () => h(
      RouterLink, 
      { to: '/messages' }, 
      { 
        default: () => unreadMessages.value > 0 
          ? `💬 消息 (${unreadMessages.value})` 
          : '💬 消息' 
      }
    ),
    key: 'messages'
  }
])

const userDropdownOptions = [
  {
    label: '👤 个人主页',
    key: 'profile',
    props: {
      onClick: () => router.push('/user/profile')
    }
  },
  {
    label: '❤️ 我的收藏',
    key: 'favorites',
    props: {
      onClick: () => router.push('/user/favorites')
    }
  },
  {
    label: '🔍 搜索历史',
    key: 'search-history',
    props: {
      onClick: () => router.push('/user/search-history')
    }
  },
  {
    label: '⚙️ 账号设置',
    key: 'settings',
    props: {
      onClick: () => router.push('/user/settings')
    }
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: '🚪 退出登录',
    key: 'logout',
    props: {
      onClick: () => handleLogout()
    }
  }
]

const activeKey = computed(() => {
  const path = router.currentRoute.value.path
  if (path.startsWith('/marketplace') || path.startsWith('/item/')) return 'marketplace'
  if (path.startsWith('/cart')) return 'cart'
  if (path.startsWith('/my-items')) return 'my-items'
  if (path.startsWith('/orders')) return 'orders'
  if (path.startsWith('/messages')) return 'messages'
  return 'marketplace'
})

// ✅ 删除 handleMenuSelect，因为 RouterLink 会自动处理导航

const handleSearch = (query?: string) => {
  const searchTerm = query || searchKeyword.value
  if (searchTerm && searchTerm.trim()) {
    router.push({
      path: '/search',
      query: { q: searchTerm }
    })
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const handleLogin = () => {
  router.push('/login')
}

const handlePublish = () => {
  router.push('/publish')
}
</script>

<template>
  <n-layout-header bordered class="user-navbar">
    <div class="navbar-container">
      <!-- Logo -->
      <div class="logo" @click="router.push('/marketplace')">
        <span class="logo-icon">🎓</span>
        <span class="logo-text">校园交易</span>
      </div>

      <!-- 搜索框 -->
      <div class="search-bar">
        <SearchAutocomplete v-model="searchKeyword" @search="handleSearch" />
      </div>

      <!-- ✅ 修复：移除 @update:value，RouterLink 会自动处理 -->
      <n-menu
        :value="activeKey"
        mode="horizontal"
        :options="menuOptions"
        class="nav-menu"
      />

      <!-- 右侧操作 -->
      <n-space align="center" :size="16">
        <!-- 通知中心 -->
        <NotificationCenter v-if="isLoggedIn" />
        
        <n-button
          v-if="isLoggedIn"
          type="primary"
          @click="handlePublish"
        >
          + 发布商品
        </n-button>

        <div v-if="isLoggedIn" class="user-info">
          <n-dropdown :options="userDropdownOptions" placement="bottom-end">
            <div class="user-avatar-container">
              <n-badge :value="unreadMessages" :max="99" v-if="unreadMessages > 0">
                <n-avatar round size="medium">
                  {{ userName.charAt(0) }}
                </n-avatar>
              </n-badge>
              <n-avatar v-else round size="medium">
                {{ userName.charAt(0) }}
              </n-avatar>
            </div>
          </n-dropdown>
        </div>

        <n-space v-else :size="8">
          <n-button @click="handleLogin">登录</n-button>
          <n-button type="primary" @click="router.push('/register')">注册</n-button>
        </n-space>
      </n-space>
    </div>
  </n-layout-header>
</template>

<style scoped>
.user-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.navbar-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  transition: transform 0.2s;
}

.logo:hover {
  transform: scale(1.05);
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.search-bar {
  flex: 1;
  max-width: 500px;
}

.nav-menu {
  flex: 1;
}

.user-avatar-container {
  cursor: pointer;
  transition: opacity 0.2s;
}

.user-avatar-container:hover {
  opacity: 0.8;
}

.user-info {
  display: flex;
  align-items: center;
}
</style>
