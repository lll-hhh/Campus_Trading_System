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
  NSpin,
  useMessage,
  useDialog
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { http } from '@/lib/http'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const itemId = computed(() => route.params.id as string)
const loading = ref(false)
const commentLoading = ref(false)

// 商品详情接口
interface ItemDetail {
  id: number
  title: string
  price: number
  originalPrice?: number
  category: string
  condition: string
  status: string
  view_count: number
  favorite_count: number
  images: string[]
  description: string
  seller_id: number
  seller_name: string
  seller?: {
    id: number
    username: string
    avatar?: string
    rating: number
    totalSales: number
    campus?: string
    responseRate: number
  }
  created_at: string
  location?: string
}

// 评论接口
interface Comment {
  id: number
  user: {
    id: number
    username: string
    avatar?: string
  }
  rating: number
  content: string
  created_at: string
}

// 商品详情
const item = ref<ItemDetail>({
  id: 0,
  title: '',
  price: 0,
  category: '',
  condition: '',
  status: '',
  view_count: 0,
  favorite_count: 0,
  images: [],
  description: '',
  seller_id: 0,
  seller_name: '',
  created_at: ''
})

// 评论列表
const comments = ref<Comment[]>([])

// 相似推荐
const similarItems = ref<ItemDetail[]>([])

// 商品详情弹窗状态
const showDetailDialog = ref(false)
const detailLoading = ref(false)
type DetailDialogItem = ItemDetail & { isFavorited?: boolean }
const currentItem = ref<DetailDialogItem>({
  id: 0,
  title: '',
  price: 0,
  category: '',
  condition: '',
  status: '',
  view_count: 0,
  favorite_count: 0,
  images: [],
  description: '',
  seller_id: 0,
  seller_name: '',
  created_at: ''
})

// 新评论
const newComment = reactive({
  rating: 5,
  content: ''
})

// 是否已收藏
const isFavorited = ref(false)

// 加载商品详情
const loadItemDetail = async () => {
  loading.value = true
  try {
    const response = await http.get(`/items/${itemId.value}`)
    const normalizedImages = normalizeImages(response.data.images)
    item.value = {
      ...response.data,
      images: normalizedImages
    }
    currentItem.value = { ...item.value, images: normalizedImages, isFavorited: isFavorited.value }
    
    // 如果没有原价，设置为当前价格的1.2倍（模拟）
    if (!item.value.originalPrice) {
      item.value.originalPrice = Math.round(item.value.price * 1.2)
    }
    
    // 构建卖家信息（如果后端没有返回完整信息）
    if (!item.value.seller) {
      item.value.seller = {
        id: item.value.seller_id,
        username: item.value.seller_name,
        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${item.value.seller_name}`,
        rating: 4.8,
        totalSales: 0,
        campus: '校园用户',
        responseRate: 95
      }
    }
    
    // 检查是否已收藏
    if (authStore.isAuthenticated) {
      await checkFavoriteStatus()
      currentItem.value.isFavorited = isFavorited.value
    }
    
    // 加载相似商品
    await loadSimilarItems()
    
  } catch (error: any) {
    console.error('加载商品详情失败:', error)
    message.error(error.response?.data?.detail || '加载商品详情失败')
  } finally {
    loading.value = false
  }
}

// 检查收藏状态
const checkFavoriteStatus = async () => {
  try {
    const response = await http.get(`/favorites/${itemId.value}/check`)
    isFavorited.value = response.data
  } catch (error) {
    console.error('检查收藏状态失败:', error)
  }
}

// 加载评论列表
const loadComments = async () => {
  commentLoading.value = true
  try {
    const response = await http.get(`/comments/items/${itemId.value}`)
    comments.value = response.data.map((c: any) => ({
      id: c.id,
      user: {
        id: c.user_id,
        username: c.username || '匿名用户',
        avatar: c.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${c.user_id}`
      },
      rating: c.rating || 5,
      content: c.content,
      created_at: c.created_at
    }))
  } catch (error: any) {
    console.error('加载评论失败:', error)
  } finally {
    commentLoading.value = false
  }
}

// 加载相似商品
const loadSimilarItems = async () => {
  try {
    const response = await http.get('/items', {
      params: {
        category: item.value.category,
        page_size: 4,
        status: 'available'
      }
    })
    // 过滤掉当前商品
    similarItems.value = response.data.items
      .filter((i: ItemDetail) => i.id !== item.value.id)
      .slice(0, 4)
      .map((i: ItemDetail) => {
        const normalized = normalizeImages(i.images)
        return {
          ...i,
          images: normalized
        }
      })
  } catch (error) {
    console.error('加载相似商品失败:', error)
  }
}

// ✅ 新增：加入购物车
const handleAddToCart = async (targetItem?: ItemDetail) => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    return
  }
  
  try {
    const data = targetItem ?? item.value
    await http.post('/cart', {
      item_id: data.id,
      quantity: 1
    })
    message.success(`"${data.title}" 已加入购物车`)
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (detail === '不能购买自己发布的商品') {
      message.warning('不能购买自己的商品哦~')
    } else if (detail === '商品已下架或已售出，无法添加到购物车') {
      message.warning('该商品已下架或已售出')
    } else {
      message.error(detail || '加入购物车失败')
    }
  }
}

// 立即购买
const handleBuyNow = () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  // 检查是否是自己的商品
  if (item.value.seller_id === authStore.user?.id) {
    message.warning('不能购买自己的商品')
    return
  }
  
  dialog.success({
    title: '确认购买',
    content: `确定要购买 "${item.value.title}" 吗？将创建订单并跳转到订单页面。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        // 创建订单
        const response = await http.post('/orders', {
          item_id: item.value.id,
          quantity: 1,
          note: ''
        })
        message.success('订单创建成功！')
        router.push(`/orders`)
      } catch (error: any) {
        message.error(error.response?.data?.detail || '创建订单失败')
      }
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
  
  router.push(`/messages?userId=${item.value.seller_id}&itemId=${item.value.id}`)
}

// ✅ 新增：收藏/取消收藏
const handleToggleFavorite = async (targetItem?: { id: number; isFavorited?: boolean }) => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    return
  }
  
  try {
    const itemId = targetItem?.id ?? item.value.id
    const currentlyFavorited = targetItem?.isFavorited ?? isFavorited.value
    if (currentlyFavorited) {
      await http.delete(`/favorites/${itemId}`)
      if (targetItem) {
        targetItem.isFavorited = false
      } else {
        isFavorited.value = false
        if (currentItem.value.id === item.value.id) {
          currentItem.value.isFavorited = false
        }
      }
      message.success('已取消收藏')
    } else {
      await http.post(`/favorites/${itemId}`)
      if (targetItem) {
        targetItem.isFavorited = true
      } else {
        isFavorited.value = true
        if (currentItem.value.id === item.value.id) {
          currentItem.value.isFavorited = true
        }
      }
      message.success('收藏成功')
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || '操作失败')
  }
}

const viewItemDetail = (targetItem: ItemDetail) => {
  currentItem.value = {
    ...targetItem,
    images: normalizeImages(targetItem.images)
  }
  showDetailDialog.value = true
}

const handleWantToBuy = () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  handleContactSeller()
}

// 提交评论
const handleSubmitComment = async () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  if (!newComment.content.trim()) {
    message.warning('请输入评论内容')
    return
  }
  
  try {
    const response = await http.post('/comments', {
      item_id: item.value.id,
      rating: newComment.rating,
      content: newComment.content
    })
    
    // 添加到评论列表顶部
    comments.value.unshift({
      id: response.data.id || Date.now(),
      user: {
        id: authStore.user?.id || 0,
        username: authStore.user?.displayName || authStore.user?.username || '当前用户',
        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${authStore.user?.id || 'current'}`
      },
      rating: newComment.rating,
      content: newComment.content,
      created_at: new Date().toISOString()
    })
    
    // 清空输入
    newComment.content = ''
    newComment.rating = 5
    message.success('评论成功')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '评论失败')
  }
}

// 查看相似商品
const handleViewSimilarItem = (id: number) => {
  router.push(`/item/${id}`)
}

// 本地占位图
const PLACEHOLDER_IMAGES = [
  '/demo-images/placeholder1.jpg',
  '/demo-images/placeholder2.jpg',
  '/demo-images/placeholder3.jpg',
  '/demo-images/placeholder4.jpg',
  '/demo-images/placeholder5.jpg',
  '/demo-images/placeholder6.jpg',
]

const getPlaceholderImage = (itemId: number) => {
  if (PLACEHOLDER_IMAGES.length === 0) return ''
  const index = Math.abs(itemId) % PLACEHOLDER_IMAGES.length
  return PLACEHOLDER_IMAGES[index]
}

const normalizeImages = (raw: unknown): string[] => {
  if (Array.isArray(raw)) {
    return raw.filter((path): path is string => typeof path === 'string')
  }
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        return parsed.filter((path): path is string => typeof path === 'string')
      }
    } catch (_err) {
      // ignore JSON parse errors
    }
    return raw ? [raw] : []
  }
  return []
}

const buildDisplayImages = (images: string[] | string | undefined | null, fallbackId: number) => {
  const normalized = normalizeImages(images)
  if (normalized.length > 0) {
    return normalized.map((img) => getFullImageUrl(img))
  }
  return [getPlaceholderImage(fallbackId)]
}

// 将相对图片URL转换为完整URL
const getFullImageUrl = (relativeUrl: string) => {
  if (!relativeUrl) return ''
  if (/^https?:/i.test(relativeUrl) || relativeUrl.startsWith('data:')) {
    return relativeUrl
  }
  const serverUrl = window.location.origin
  return `${serverUrl}${relativeUrl}`
}

// 获取商品图片URL，支持随机占位图
const getItemImageUrl = (images: string[] | string | undefined | null, itemId?: number) => {
  return buildDisplayImages(images, itemId || 0)[0]
}

const itemDisplayImages = computed(() => buildDisplayImages(item.value.images, item.value.id))
const dialogDisplayImages = computed(() => buildDisplayImages(currentItem.value.images, currentItem.value.id))

// 格式化时间
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载数据
onMounted(async () => {
  await loadItemDetail()
  await loadComments()
})
</script>

<template>
  <div class="item-detail-view">
    <n-spin :show="loading">
      <n-card>
        <n-grid :cols="2" :x-gap="24" responsive="screen">
          <!-- 左侧：图片轮播 -->
          <n-grid-item>
            <n-carousel autoplay show-arrow>
              <img
                v-for="(image, index) in itemDisplayImages"
                :key="index"
                :src="image"
                class="carousel-img"
              />
            </n-carousel>
            
            <!-- 商品统计 -->
            <n-space justify="space-around" style="margin-top: 16px">
              <span>👁️ {{ item.view_count }} 次浏览</span>
              <span>❤️ {{ item.favorite_count }} 人喜欢</span>
              <span>📅 {{ formatDate(item.created_at) }}</span>
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
                <span v-if="item.originalPrice && item.originalPrice > item.price" class="original-price">
                  ¥{{ item.originalPrice }}
                </span>
                <n-tag v-if="item.originalPrice && item.originalPrice > item.price" type="error" size="small">
                  省{{ item.originalPrice - item.price }}元
                </n-tag>
              </div>

              <!-- 标签 -->
              <n-space>
                <n-tag type="success">{{ item.category }}</n-tag>
                <n-tag type="info">{{ item.condition }}</n-tag>
                <n-tag :type="item.status === 'available' ? 'warning' : 'error'">
                  {{ item.status === 'available' ? '在售' : item.status === 'sold' ? '已售出' : item.status }}
                </n-tag>
              </n-space>

              <!-- 卖家信息 -->
              <n-card size="small" title="卖家信息">
                <n-space align="center">
                  <n-avatar :src="item.seller?.avatar" size="large" />
                  <div>
                    <div style="font-weight: bold; font-size: 16px">
                      {{ item.seller?.username || item.seller_name }}
                    </div>
                    <n-space :size="8">
                      <n-rate :value="item.seller?.rating || 5" readonly size="small" />
                      <span style="font-size: 12px; color: #999">
                        {{ item.seller?.totalSales || 0 }} 笔交易
                      </span>
                    </n-space>
                    <div style="font-size: 12px; color: #666; margin-top: 4px">
                      📍 {{ item.seller?.campus || '校园用户' }} | 回复率 {{ item.seller?.responseRate || 95 }}%
                    </div>
                  </div>
                </n-space>
              </n-card>

              <!-- 交易地点 -->
              <n-descriptions :column="1" bordered size="small">
                <n-descriptions-item label="📍 交易地点">
                  {{ item.location || '线下当面交易' }}
                </n-descriptions-item>
              </n-descriptions>

              <!-- 操作按钮 -->
              <n-space>
                <n-button 
                  type="primary" 
                  size="large" 
                  @click="handleBuyNow()"
                  :disabled="item.status !== 'available'"
                >
                  💰 立即购买
                </n-button>
                <n-button 
                  size="large" 
                  @click="handleAddToCart()"
                  :disabled="item.status !== 'available'"
                >
                  🛒 加入购物车
                </n-button>
                <n-button size="large" @click="handleContactSeller()">
                  💬 联系卖家
                </n-button>
                <n-button
                  :type="isFavorited ? 'error' : 'default'"
                  size="large"
                  @click="handleToggleFavorite()"
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
                <n-button type="primary" @click="handleSubmitComment()">
                  提交评价
                </n-button>
              </n-space>
            </n-card>

            <!-- 评论列表 -->
            <n-spin :show="commentLoading">
              <n-space vertical :size="16">
                <div v-for="comment in comments" :key="comment.id" class="comment-item">
                  <n-space align="start">
                    <n-avatar :src="comment.user.avatar" />
                    <div style="flex: 1">
                      <div style="font-weight: bold">{{ comment.user.username }}</div>
                      <n-rate :value="comment.rating" readonly size="small" />
                      <p style="margin: 8px 0">{{ comment.content }}</p>
                      <span style="font-size: 12px; color: #999">
                        {{ formatDate(comment.created_at) }}
                      </span>
                    </div>
                  </n-space>
                </div>
                
                <n-empty v-if="comments.length === 0" description="暂无评价" />
              </n-space>
            </n-spin>
          </n-tab-pane>
        </n-tabs>
      </n-card>

      <!-- 相似推荐 -->
      <n-card title="🔍 相似推荐" style="margin-top: 24px">
        <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen">
          <n-grid-item v-for="similarItem in similarItems" :key="similarItem.id">
            <n-card
              hoverable
              class="similar-item"
              @click="handleViewSimilarItem(similarItem.id)"
            >
              <img 
                :src="getItemImageUrl(similarItem.images, similarItem.id)" 
                class="similar-item-img" 
              />
              <div class="similar-item-title">{{ similarItem.title }}</div>
              <div class="similar-item-price">¥{{ similarItem.price }}</div>
              <div class="similar-item-seller">卖家: {{ similarItem.seller_name }}</div>

              <!-- 在商品卡片的底部操作区域添加 -->
              <div class="flex gap-2 mt-3">
                <n-button 
                  size="small" 
                  type="primary"
                  @click.stop="handleAddToCart(similarItem)"
                >
                  🛒 加购
                </n-button>
                <n-button 
                  size="small"
                  @click.stop="viewItemDetail(similarItem)"
                >
                  查看详情
                </n-button>
              </div>
            </n-card>
          </n-grid-item>
        </n-grid>
        <n-empty v-if="similarItems.length === 0" description="暂无相似商品" />
      </n-card>
    </n-spin>

    <!-- 商品详情弹窗（新加） -->
    <n-dialog v-model:show="showDetailDialog" width="80%" :mask-closable="false">
      <template #header>
        <div class="text-lg font-bold">{{ currentItem.title }}</div>
      </template>
      
      <template #default>
        <n-spin :show="detailLoading">
          <!-- 图片轮播 -->
          <n-carousel autoplay show-arrow>
            <img
              v-for="(image, index) in dialogDisplayImages"
              :key="index"
              :src="image"
              class="carousel-img"
            />
          </n-carousel>
          
          <!-- 商品信息 -->
          <div class="p-4">
            <!-- 价格 -->
            <div class="price-section">
              <span class="current-price">¥{{ currentItem.price }}</span>
              <span v-if="currentItem.originalPrice && currentItem.originalPrice > currentItem.price" class="original-price">
                ¥{{ currentItem.originalPrice }}
              </span>
              <n-tag v-if="currentItem.originalPrice && currentItem.originalPrice > currentItem.price" type="error" size="small">
                省{{ currentItem.originalPrice - currentItem.price }}元
              </n-tag>
            </div>

            <!-- 标签 -->
            <n-space>
              <n-tag type="success">{{ currentItem.category }}</n-tag>
              <n-tag type="info">{{ currentItem.condition }}</n-tag>
              <n-tag :type="currentItem.status === 'available' ? 'warning' : 'error'">
                {{ currentItem.status === 'available' ? '在售' : currentItem.status === 'sold' ? '已售出' : currentItem.status }}
              </n-tag>
            </n-space>

            <!-- 卖家信息 -->
            <n-card size="small" title="卖家信息" class="mt-4">
              <n-space align="center">
                <n-avatar :src="currentItem.seller?.avatar" size="large" />
                <div>
                  <div style="font-weight: bold; font-size: 16px">
                    {{ currentItem.seller?.username || currentItem.seller_name }}
                  </div>
                  <n-space :size="8">
                    <n-rate :value="currentItem.seller?.rating || 5" readonly size="small" />
                    <span style="font-size: 12px; color: #999">
                      {{ currentItem.seller?.totalSales || 0 }} 笔交易
                    </span>
                  </n-space>
                  <div style="font-size: 12px; color: #666; margin-top: 4px">
                    📍 {{ currentItem.seller?.campus || '校园用户' }} | 回复率 {{ currentItem.seller?.responseRate || 95 }}%
                  </div>
                </div>
              </n-space>
            </n-card>

            <!-- 操作按钮组 -->
            <div class="space-y-3 mt-4">
              <!-- 立即购买/联系卖家 -->
              <n-button 
                type="warning" 
                size="large" 
                block 
                @click="handleWantToBuy()"
                strong
              >
                💬 我想要 - 联系卖家
              </n-button>
              
              <!-- 加入购物车 -->
              <n-button 
                type="primary" 
                size="large" 
                block 
                @click="handleAddToCart(currentItem)"
                strong
              >
                🛒 加入购物车
              </n-button>
              
              <!-- 收藏 -->
              <n-button 
                size="large" 
                block 
                ghost
                :type="currentItem?.isFavorited ? 'error' : 'default'"
                @click="handleToggleFavorite(currentItem)"
              >
                {{ currentItem?.isFavorited ? '❤️ 已收藏' : '🤍 收藏' }}
              </n-button>
            </div>
            
            <!-- 交易提示 -->
            <n-alert type="warning" class="mt-4">
              <template #header>
                ⚠️ 交易流程说明
              </template>
              <ol class="list-decimal list-inside text-sm space-y-1">
                <li>点击"我想要"后，在评论区留言沟通</li>
                <li>双方达成一致后，平台提供联系方式</li>
                <li>线下当面交易，验货后付款</li>
                <li>交易完成后，商品自动下架</li>
              </ol>
              <p class="text-red-500 font-bold mt-2">❌ 禁止线上支付！违规将封号处理！</p>
            </n-alert>
          </div>
        </n-spin>
      </template>
    </n-dialog>
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

/* 新增：商品详情弹窗样式 */
.n-dialog {
  max-width: 900px;
}

.n-dialog .carousel-img {
  height: 400px;
}

.n-dialog .price-section {
  margin-top: 16px;
}

.n-dialog .current-price {
  font-size: 28px;
}

.n-dialog .original-price {
  font-size: 16px;
}

.n-dialog .description {
  font-size: 14px;
}

.n-dialog .comment-item {
  font-size: 14px;
}

.n-dialog .similar-item-img {
  height: 150px;
}
</style>
