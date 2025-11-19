<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  NCard, 
  NCarousel, 
  NSpace, 
  NButton, 
  NTag, 
  NAvatar, 
  NDescriptions,
  NDescriptionsItem,
  NTabs,
  NTabPane,
  NInput,
  NRate,
  NGrid,
  NGridItem,
  NEmpty,
  useMessage,
  useDialog
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const itemId = computed(() => route.params.id as string)
const loading = ref(false)

// 商品详情
const item = ref({
  id: 1,
  title: '全新iPad Pro 2024款 11英寸',
  price: 4999,
  originalPrice: 6999,
  category: '数码产品',
  condition: '全新',
  status: '在售',
  views: 1258,
  likes: 89,
  images: [
    'https://picsum.photos/800/600?random=1',
    'https://picsum.photos/800/600?random=2',
    'https://picsum.photos/800/600?random=3',
    'https://picsum.photos/800/600?random=4'
  ],
  description: `
    全新未拆封的iPad Pro 2024款，11英寸版本。
    
    配置信息：
    - M4芯片
    - 256GB存储
    - Wi-Fi版
    - 深空灰色
    
    购买原因：朋友送的礼物，已经有一台了，所以出售。
    
    交易方式：
    - 支持当面交易（校内）
    - 接受验机
    - 全套配件齐全
    - 保修未激活
  `,
  seller: {
    id: 101,
    username: '张同学',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Zhang',
    rating: 4.8,
    totalSales: 23,
    campus: '北京大学',
    responseRate: 95
  },
  publishedAt: '2024-11-15 14:30',
  location: '北京大学 学生公寓1号楼'
})

// 评论列表
const comments = ref([
  {
    id: 1,
    user: {
      username: '李同学',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Li'
    },
    rating: 5,
    content: '卖家很靠谱，东西确实是全新的，价格也很实惠！',
    createdAt: '2024-11-16 10:20'
  },
  {
    id: 2,
    user: {
      username: '王同学',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Wang'
    },
    rating: 4,
    content: '东西不错，就是交易地点有点远',
    createdAt: '2024-11-17 15:45'
  }
])

// 相似推荐
const similarItems = ref([
  {
    id: 2,
    title: 'MacBook Air M2 13英寸',
    price: 6999,
    image: 'https://picsum.photos/200/200?random=5',
    seller: '刘同学'
  },
  {
    id: 3,
    title: 'Apple Watch Series 9',
    price: 2499,
    image: 'https://picsum.photos/200/200?random=6',
    seller: '陈同学'
  },
  {
    id: 4,
    title: 'AirPods Pro 2代',
    price: 1299,
    image: 'https://picsum.photos/200/200?random=7',
    seller: '周同学'
  },
  {
    id: 5,
    title: 'iPad Air 第五代',
    price: 3499,
    image: 'https://picsum.photos/200/200?random=8',
    seller: '赵同学'
  }
])

// 新评论
const newComment = reactive({
  rating: 5,
  content: ''
})

// 是否已收藏
const isFavorited = ref(false)

// 加入购物车
const handleAddToCart = () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  message.success('已加入购物车')
}

// 立即购买
const handleBuyNow = () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  dialog.success({
    title: '确认购买',
    content: `确定要购买 "${item.value.title}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      message.success('购买成功！')
      router.push('/orders')
    }
  })
}

// 联系卖家
const handleContactSeller = () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  router.push(`/messages?userId=${item.value.seller.id}`)
}

// 收藏/取消收藏
const handleToggleFavorite = () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  isFavorited.value = !isFavorited.value
  message.success(isFavorited.value ? '收藏成功' : '取消收藏')
}

// 提交评论
const handleSubmitComment = () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  if (!newComment.content.trim()) {
    message.warning('请输入评论内容')
    return
  }
  
  // TODO: 调用API提交评论
  comments.value.unshift({
    id: Date.now(),
    user: {
      username: authStore.displayName || '当前用户',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Current'
    },
    rating: newComment.rating,
    content: newComment.content,
    createdAt: new Date().toLocaleString('zh-CN')
  })
  
  newComment.content = ''
  newComment.rating = 5
  message.success('评论成功')
}

// 查看相似商品
const handleViewSimilarItem = (id: number) => {
  router.push(`/item/${id}`)
}

// 加载数据
onMounted(async () => {
  loading.value = true
  try {
    // TODO: 从API加载商品详情
    await new Promise(resolve => setTimeout(resolve, 500))
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="item-detail-view">
    <n-card>
      <n-grid :cols="2" :x-gap="24" responsive="screen">
        <!-- 左侧：图片轮播 -->
        <n-grid-item>
          <n-carousel autoplay show-arrow>
            <img
              v-for="(image, index) in item.images"
              :key="index"
              :src="image"
              class="carousel-img"
            />
          </n-carousel>
          
          <!-- 商品统计 -->
          <n-space justify="space-around" style="margin-top: 16px">
            <span>👁️ {{ item.views }} 次浏览</span>
            <span>❤️ {{ item.likes }} 人喜欢</span>
            <span>📅 {{ item.publishedAt }}</span>
          </n-space>
        </n-grid-item>

        <!-- 右侧：商品信息 -->
        <n-grid-item>
          <n-space vertical :size="16">
            <!-- 标题 -->
            <h1 style="font-size: 28px; margin: 0">{{ item.title }}</h1>

            <!-- 价格 -->
            <div class="price-section">
              <span class="current-price">¥{{ item.price }}</span>
              <span class="original-price">¥{{ item.originalPrice }}</span>
              <n-tag type="error" size="small">省{{ item.originalPrice - item.price }}元</n-tag>
            </div>

            <!-- 标签 -->
            <n-space>
              <n-tag type="success">{{ item.category }}</n-tag>
              <n-tag type="info">{{ item.condition }}</n-tag>
              <n-tag type="warning">{{ item.status }}</n-tag>
            </n-space>

            <!-- 卖家信息 -->
            <n-card size="small" title="卖家信息">
              <n-space align="center">
                <n-avatar :src="item.seller.avatar" size="large" />
                <div>
                  <div style="font-weight: bold; font-size: 16px">
                    {{ item.seller.username }}
                  </div>
                  <n-space :size="8">
                    <n-rate :value="item.seller.rating" readonly size="small" />
                    <span style="font-size: 12px; color: #999">
                      {{ item.seller.totalSales }} 笔交易
                    </span>
                  </n-space>
                  <div style="font-size: 12px; color: #666; margin-top: 4px">
                    📍 {{ item.seller.campus }} | 回复率 {{ item.seller.responseRate }}%
                  </div>
                </div>
              </n-space>
            </n-card>

            <!-- 交易地点 -->
            <n-descriptions :column="1" bordered size="small">
              <n-descriptions-item label="📍 交易地点">
                {{ item.location }}
              </n-descriptions-item>
            </n-descriptions>

            <!-- 操作按钮 -->
            <n-space>
              <n-button type="primary" size="large" @click="handleBuyNow">
                💰 立即购买
              </n-button>
              <n-button size="large" @click="handleAddToCart">
                🛒 加入购物车
              </n-button>
              <n-button size="large" @click="handleContactSeller">
                💬 联系卖家
              </n-button>
              <n-button
                :type="isFavorited ? 'error' : 'default'"
                size="large"
                @click="handleToggleFavorite"
              >
                {{ isFavorited ? '❤️ 已收藏' : '🤍 收藏' }}
              </n-button>
            </n-space>
          </n-space>
        </n-grid-item>
      </n-grid>
    </n-card>

    <!-- 详情和评论 -->
    <n-card style="margin-top: 24px">
      <n-tabs type="line" animated>
        <!-- 商品详情 -->
        <n-tab-pane name="details" tab="📝 商品详情">
          <div class="description" v-html="item.description.replace(/\n/g, '<br>')"></div>
        </n-tab-pane>

        <!-- 用户评价 -->
        <n-tab-pane name="comments" tab="💬 用户评价">
          <!-- 发表评论 -->
          <n-card size="small" title="发表评价" style="margin-bottom: 24px">
            <n-space vertical>
              <div>
                <span style="margin-right: 8px">评分：</span>
                <n-rate v-model:value="newComment.rating" />
              </div>
              <n-input
                v-model:value="newComment.content"
                type="textarea"
                placeholder="分享你的使用体验..."
                :rows="3"
              />
              <n-button type="primary" @click="handleSubmitComment">
                提交评价
              </n-button>
            </n-space>
          </n-card>

          <!-- 评论列表 -->
          <n-space vertical :size="16">
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <n-space align="start">
                <n-avatar :src="comment.user.avatar" />
                <div style="flex: 1">
                  <div style="font-weight: bold">{{ comment.user.username }}</div>
                  <n-rate :value="comment.rating" readonly size="small" />
                  <p style="margin: 8px 0">{{ comment.content }}</p>
                  <span style="font-size: 12px; color: #999">
                    {{ comment.createdAt }}
                  </span>
                </div>
              </n-space>
            </div>
            
            <n-empty v-if="comments.length === 0" description="暂无评价" />
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <!-- 相似推荐 -->
    <n-card title="🔍 相似推荐" style="margin-top: 24px">
      <n-grid :cols="4" :x-gap="16" :y-gap="16">
        <n-grid-item v-for="similarItem in similarItems" :key="similarItem.id">
          <n-card
            hoverable
            class="similar-item"
            @click="handleViewSimilarItem(similarItem.id)"
          >
            <img :src="similarItem.image" class="similar-item-img" />
            <div class="similar-item-title">{{ similarItem.title }}</div>
            <div class="similar-item-price">¥{{ similarItem.price }}</div>
            <div class="similar-item-seller">卖家: {{ similarItem.seller }}</div>
          </n-card>
        </n-grid-item>
      </n-grid>
    </n-card>
  </div>
</template>

<style scoped>
.item-detail-view {
  max-width: 1400px;
  margin: 0 auto;
}

.carousel-img {
  width: 100%;
  height: 500px;
  object-fit: cover;
  border-radius: 8px;
}

.price-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.current-price {
  font-size: 36px;
  font-weight: bold;
  color: #f56c6c;
}

.original-price {
  font-size: 18px;
  color: #999;
  text-decoration: line-through;
}

.description {
  line-height: 1.8;
  white-space: pre-wrap;
  color: #333;
}

.comment-item {
  padding: 16px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.similar-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.similar-item:hover {
  transform: translateY(-4px);
}

.similar-item-img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 8px;
}

.similar-item-title {
  font-weight: bold;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.similar-item-price {
  color: #f56c6c;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.similar-item-seller {
  font-size: 12px;
  color: #999;
}
</style>
