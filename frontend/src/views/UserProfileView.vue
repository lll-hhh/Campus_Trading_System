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
import api from '../lib/http'

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

const loadUserData = async () => {
  try {
    // TODO: 从API加载用户数据
    // const response = await api.get('/api/users/me')
    // userInfo.value = response.data
  } catch (error: any) {
    message.error('加载用户数据失败')
  }
}

const loadStats = async () => {
  try {
    // TODO: 从API加载统计数据
  } catch (error: any) {
    message.error('加载统计数据失败')
  }
}

const goToSettings = () => {
  router.push('/user/settings')
}

const goToMyItems = () => {
  router.push('/user/my-items')
}

const goToOrders = () => {
  router.push('/user/orders')
}

onMounted(() => {
  loadUserData()
  loadStats()
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
          <n-button @click="router.push('/user/favorites')">我的收藏</n-button>
          <n-button @click="router.push('/messages')">
            消息 <n-tag v-if="stats.messages_unread > 0" type="error" size="small" round>
              {{ stats.messages_unread }}
            </n-tag>
          </n-button>
        </n-space>
      </n-card>

      <!-- 最近活动 -->
      <n-card title="最近活动">
        <n-tabs type="line">
          <n-tab-pane name="items" tab="我的商品">
            <n-list hoverable clickable>
              <n-list-item v-for="i in 3" :key="i">
                <n-thing title="商品标题" description="发布于 2天前">
                  <template #avatar>
                    <n-avatar>商</n-avatar>
                  </template>
                  <template #header-extra>
                    <n-tag type="success">在售</n-tag>
                  </template>
                  <template #footer>
                    <span style="color: #f56c6c; font-weight: bold">¥199</span>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>

          <n-tab-pane name="transactions" tab="交易记录">
            <n-list hoverable clickable>
              <n-list-item v-for="i in 3" :key="i">
                <n-thing title="交易订单 #12345" description="2024-11-19 10:30">
                  <template #avatar>
                    <n-avatar>单</n-avatar>
                  </template>
                  <template #header-extra>
                    <n-tag type="warning">进行中</n-tag>
                  </template>
                  <template #footer>
                    <span>交易金额: ¥299</span>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>

          <n-tab-pane name="favorites" tab="我的收藏">
            <n-list hoverable clickable>
              <n-list-item v-for="i in 3" :key="i">
                <n-thing title="收藏的商品" description="收藏于 1天前">
                  <template #avatar>
                    <n-avatar>藏</n-avatar>
                  </template>
                  <template #footer>
                    <span style="color: #f56c6c; font-weight: bold">¥399</span>
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
