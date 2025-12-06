<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NSpace,
  NAvatar,
  NStatistic,
  NGrid,
  NGridItem,
  NButton,
  NTag,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NTabs,
  NTabPane,
  NList,
  NListItem,
  NThing,
  useMessage,
} from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { http as api } from '@/lib/http'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

const userInfo = ref<any>({
  id: 1,
  username: '张三',
  email: 'zhangsan@example.com',
  student_id: 'S10001',
  avatar: '',
  credit_score: 95,
  role: 'user',
  created_at: '2024-01-01',
  is_verified: true,
})

const stats = ref({
  items_count: 12,
  sold_count: 8,
  buying_count: 3,
  favorites_count: 25,
  messages_unread: 5,
  credit_score: 95,
})

const recentItems = ref<any[]>([])
const recentTransactions = ref<any[]>([])
const recentFavorites = ref<any[]>([])

const activeTab = ref('items')

const loadUserData = async () => {
  try {
    const response = await api.get('/auth/me')
    userInfo.value = {
      id: response.data.user_id,
      username: response.data.display_name || '用户',
      email: response.data.email || '已登录用户',
      student_id: response.data.student_id || '已认证',
      avatar: response.data.avatar || '',
      credit_score: response.data.credit_score || 95,
      role: response.data.roles?.[0] || 'user',
      created_at: response.data.created_at || new Date().toISOString(),
      is_verified: response.data.is_verified !== false
    }
  } catch (error: any) {
    message.error('加载用户数据失败')
  }
}

const loadStats = async () => {
  try {
    // 加载商品统计
    const itemsResponse = await api.get('/items/my', { params: { page_size: 1 } })
    stats.value.items_count = itemsResponse.data.total

    // 加载收藏统计
    const favoritesResponse = await api.get('/items/my/favorites', { params: { page_size: 1 } })
    stats.value.favorites_count = favoritesResponse.data.total

    // 加载订单统计
    const ordersResponse = await api.get('/orders', { params: { role: 'buyer', page_size: 100 } })
    const allOrders = ordersResponse.data.orders
    stats.value.buying_count = allOrders.filter((order: any) => order.status === 'pending').length

    // 计算已售出数量（作为卖家）
    const sellingResponse = await api.get('/orders', { params: { role: 'seller', page_size: 100 } })
    stats.value.sold_count = sellingResponse.data.orders.filter((order: any) => order.status === 'completed').length

    // 加载未读消息数量
    try {
      const messagesResponse = await api.get('/messages/unread/count')
      stats.value.messages_unread = messagesResponse.data.count || 0
    } catch {
      stats.value.messages_unread = 0
    }
  } catch (error: any) {
    console.error('加载统计数据失败:', error)
    message.error('加载统计数据失败')
  }
}

const loadRecentItems = async () => {
  try {
    const response = await api.get('/items/my', { params: { page_size: 3 } })
    recentItems.value = response.data.items
  } catch (error: any) {
    console.error('加载最近商品失败:', error)
  }
}

const loadRecentTransactions = async () => {
  try {
    const response = await api.get('/orders', { params: { page_size: 3 } })
    recentTransactions.value = response.data.orders
  } catch (error: any) {
    console.error('加载最近交易失败:', error)
  }
}

const loadRecentFavorites = async () => {
  try {
    const response = await api.get('/items/my/favorites', { params: { page_size: 3 } })
    recentFavorites.value = response.data.items
  } catch (error: any) {
    console.error('加载最近收藏失败:', error)
  }
}

const goToSettings = () => {
  router.push('/user/settings')
}

const goToMyItems = () => {
  router.push('/my-items')
}

const goToOrders = () => {
  router.push('/orders')
}

const goToFavorites = () => {
  activeTab.value = 'favorites'
}

onMounted(() => {
  loadUserData()
  loadStats()
  loadRecentItems()
  loadRecentTransactions()
  loadRecentFavorites()
})
</script>

<template>
  <div class="profile-page">
    <n-space vertical :size="24">
      <!-- 用户信息卡片 -->
      <n-card title="个人信息">
        <template #header-extra>
          <n-button @click="goToSettings">编辑资料</n-button>
        </template>

        <n-space align="center" :size="24">
          <n-avatar :size="100" round>
            {{ userInfo.username?.charAt(0) }}
          </n-avatar>

          <n-space vertical :size="8">
            <div style="font-size: 24px; font-weight: bold">
              {{ userInfo.username }}
              <n-tag v-if="userInfo.is_verified" type="success" size="small" style="margin-left: 8px">
                已认证
              </n-tag>
            </div>
            <div style="color: #666">学号: {{ userInfo.student_id }}</div>
            <div style="color: #666">邮箱: {{ userInfo.email }}</div>
            <div>
              <n-tag type="info">信用分: {{ userInfo.credit_score }}</n-tag>
            </div>
          </n-space>
        </n-space>

        <n-divider />

        <n-grid :cols="4" :x-gap="24">
          <n-grid-item>
            <n-statistic label="发布商品" :value="stats.items_count" />
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="已售出" :value="stats.sold_count" />
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="购买中" :value="stats.buying_count" />
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="收藏" :value="stats.favorites_count" />
          </n-grid-item>
        </n-grid>
      </n-card>

      <!-- 快捷操作 -->
      <n-card title="快捷操作">
        <n-space>
          <n-button type="primary" @click="router.push('/marketplace')">
            浏览商品
          </n-button>
          <n-button @click="goToMyItems">我的商品</n-button>
          <n-button @click="goToOrders">交易记录</n-button>
          <n-button @click="goToFavorites">我的收藏</n-button>
          <n-button @click="router.push('/messages')">
            消息 <n-tag v-if="stats.messages_unread > 0" type="error" size="small" round>
              {{ stats.messages_unread }}
            </n-tag>
          </n-button>
        </n-space>
      </n-card>

      <!-- 最近活动 -->
      <n-card title="最近活动">
        <n-tabs type="line" v-model:value="activeTab">
          <n-tab-pane name="items" tab="我的商品">
            <n-list hoverable clickable>
              <n-list-item v-for="item in recentItems" :key="item.id">
                <n-thing :title="item.title" :description="`发布于 ${new Date(item.created_at).toLocaleDateString()}`">
                  <template #avatar>
                    <n-avatar>{{ item.title?.charAt(0) }}</n-avatar>
                  </template>
                  <template #header-extra>
                    <n-tag :type="item.status === 'active' ? 'success' : 'default'">{{ item.status === 'active' ? '在售' : '下架' }}</n-tag>
                  </template>
                  <template #footer>
                    <span style="color: #f56c6c; font-weight: bold">¥{{ item.price }}</span>
                  </template>
                </n-thing>
              </n-list-item>
              <n-list-item v-if="recentItems.length === 0">
                <n-thing title="暂无商品" description="您还没有发布商品">
                  <template #footer>
                    <n-button @click="router.push('/marketplace')">去发布商品</n-button>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>

          <n-tab-pane name="transactions" tab="交易记录">
            <n-list hoverable clickable>
              <n-list-item v-for="transaction in recentTransactions" :key="transaction.id">
                <n-thing :title="`交易订单 #${transaction.id}`" :description="new Date(transaction.created_at).toLocaleString()">
                  <template #avatar>
                    <n-avatar>单</n-avatar>
                  </template>
                  <template #header-extra>
                    <n-tag :type="transaction.status === 'completed' ? 'success' : transaction.status === 'pending' ? 'warning' : 'default'">
                      {{ transaction.status === 'completed' ? '已完成' : transaction.status === 'pending' ? '进行中' : transaction.status }}
                    </n-tag>
                  </template>
                  <template #footer>
                    <span>交易金额: ¥{{ transaction.total_amount }}</span>
                  </template>
                </n-thing>
              </n-list-item>
              <n-list-item v-if="recentTransactions.length === 0">
                <n-thing title="暂无交易记录" description="您还没有交易记录">
                  <template #footer>
                    <n-button @click="router.push('/marketplace')">去浏览商品</n-button>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>

          <n-tab-pane name="favorites" tab="我的收藏">
            <n-list hoverable clickable>
              <n-list-item v-for="favorite in recentFavorites" :key="favorite.id">
                <n-thing :title="favorite.title" :description="`收藏于 ${new Date(favorite.favorited_at || favorite.created_at).toLocaleDateString()}`">
                  <template #avatar>
                    <n-avatar>{{ favorite.title?.charAt(0) }}</n-avatar>
                  </template>
                  <template #footer>
                    <span style="color: #f56c6c; font-weight: bold">¥{{ favorite.price }}</span>
                  </template>
                </n-thing>
              </n-list-item>
              <n-list-item v-if="recentFavorites.length === 0">
                <n-thing title="暂无收藏" description="您还没有收藏商品">
                  <template #footer>
                    <n-button @click="router.push('/marketplace')">去浏览商品</n-button>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
</style>
