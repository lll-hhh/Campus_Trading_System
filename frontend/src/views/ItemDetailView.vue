<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
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

// 辅助函数
const getStatusType = (status: string) => {
  switch (status) {
    case 'available': return 'success'
    case 'pending': return 'warning'
    case 'sold': return 'info'
    case 'offline': return 'error'
    default: return 'default'
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'available': return '在售'
    case 'pending': return '审核中'
    case 'sold': return '已售'
    case 'offline': return '已下架'
    default: return '未知'
  }
}

const getCategoryLabel = (category: string) => {
  const options = [
    { label: '发动机系统', value: 'engine' },
    { label: '制动系统', value: 'brakes' },
    { label: '滤清器', value: 'filters' },
    { label: '蓄电池', value: 'batteries' },
    { label: '轮胎轮毂', value: 'tires' },
    { label: '灯光照明', value: 'lighting' },
    { label: '悬挂系统', value: 'suspension' },
    { label: '传动系统', value: 'transmission' },
    { label: '车身外观', value: 'body' },
    { label: '内饰配件', value: 'interior' },
    { label: '其他配件', value: 'other' }
  ]
  return options.find(o => o.value === category)?.label || category
}

const getConditionLabel = (condition: string) => {
  const options = [
    { label: '原厂全新', value: 'new' },
    { label: '原厂拆车', value: 'like-new' },
    { label: '品牌件', value: 'excellent' },
    { label: '副厂件', value: 'good' },
    { label: '翻新件', value: 'used' }
  ]
  return options.find(o => o.value === condition)?.label || condition
}

// 零件详情接口
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
    region?: string
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
  parent_comment_id?: number
  replies?: Comment[]
}

// 零件详情
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

// 零件详情弹窗状态
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

// 加载零件详情
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
        region: '凤凰用户',
        responseRate: 95
      }
    }
    
    // 检查是否已收藏
    if (authStore.isAuthenticated) {
      await checkFavoriteStatus()
      currentItem.value.isFavorited = isFavorited.value
    }
    
    // 加载相似零件
    await loadSimilarItems()
    
  } catch (error: any) {
    console.error('加载零件详情失败:', error)
    message.error(error.response?.data?.detail || '加载零件详情失败')
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

// 加载相似零件
const loadSimilarItems = async () => {
  try {
    const response = await http.get('/items', {
      params: {
        category: item.value.category,
        page_size: 4,
        status: 'available'
      }
    })
    // 过滤掉当前零件
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
    console.error('加载相似零件失败:', error)
  }
}

// ✅ 新增：加入采购车
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
    message.success(`"${data.title}" 已加入采购车`)
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (detail === '不能购买自己发布的零件') {
      message.warning('不能购买自己的零件哦~')
    } else if (detail === '零件已下架或已售出，无法添加到采购车') {
      message.warning('该零件已下架或已售出')
    } else {
      message.error(detail || '加入采购车失败')
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
  
  // 检查是否是自己的零件
  if (item.value.seller_id === authStore.user?.id) {
    message.warning('不能购买自己的零件')
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

// 查看相似零件
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

// 获取零件图片URL，支持随机占位图
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

// 回复相关
const handleReply = (parentComment: Comment) => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录后再回复')
    router.push('/login')
    return
  }
  
  dialog.info({
    title: `回复 ${parentComment.user.username}`,
    content: () => h(NInput, {
      type: 'textarea',
      placeholder: '请输入回复内容...',
      onUpdateValue: (v) => { replyContent.value = v }
    }),
    positiveText: '提交',
    negativeText: '取消',
    onPositiveClick: async () => {
      if (!replyContent.value) {
        message.error('回复内容不能为空')
        return false
      }
      await submitReply(parentComment.id)
    }
  })
}

const replyContent = ref('')

const submitReply = async (parentId: number) => {
  try {
    await http.post('/api/v1/comments', {
      item_id: item.value.id,
      content: replyContent.value,
      parent_comment_id: parentId,
      rating: 5
    })
    message.success('回复成功')
    replyContent.value = ''
    loadComments() // 刷新评论列表
  } catch (error) {
    console.error('回复失败:', error)
    message.error('回复失败，请稍后再试')
  }
}
</script>

<template>
  <div class="item-detail-view max-w-7xl mx-auto py-12 px-4">
    <n-spin :show="loading">
      <div v-if="item.id" class="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <!-- 左侧：图片展示 -->
        <div class="lg:col-span-7">
          <div class="sticky top-24">
            <div class="bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-sm mb-6">
              <n-carousel show-arrow dot-type="line" class="h-[600px] bg-gray-50">
                <img
                  v-for="(img, index) in itemDisplayImages"
                  :key="index"
                  :src="img"
                  class="w-full h-full object-contain p-8"
                />
              </n-carousel>
            </div>
            <!-- 缩略图预览 (如果有多个图片) -->
            <div v-if="itemDisplayImages.length > 1" class="flex gap-4 overflow-x-auto pb-2">
              <div 
                v-for="(img, index) in itemDisplayImages" 
                :key="index"
                class="w-24 h-24 rounded-xl border-2 border-gray-100 overflow-hidden cursor-pointer hover:border-primary transition-colors flex-shrink-0"
              >
                <img :src="img" class="w-full h-full object-cover" />
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：零件信息 -->
        <div class="lg:col-span-5">
          <div class="flex flex-col h-full">
            <!-- 标题和状态 -->
            <div class="mb-8">
              <div class="flex items-center gap-3 mb-4">
                <span class="bg-primary text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full">
                  {{ getCategoryLabel(item.category) }}
                </span>
                <span :class="`bg-gray-100 text-gray-500 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full` ">
                  {{ getConditionLabel(item.condition) }}
                </span>
              </div>
              <h1 class="text-4xl font-black tracking-tighter text-dark leading-tight mb-4">
                {{ item.title }}
              </h1>
              <div class="flex items-center gap-6 text-gray-400 text-[10px] font-bold uppercase tracking-widest">
                <span>OEM: {{ item.id.toString().padStart(8, '0') }}</span>
                <span>👁️ {{ item.view_count }} 浏览</span>
                <span>❤️ {{ item.favorite_count }} 收藏</span>
              </div>
            </div>

            <!-- 价格区域 -->
            <div class="bg-gray-50 rounded-2xl p-8 mb-8 border border-gray-100">
              <div class="flex items-baseline gap-4 mb-2">
                <span class="text-gray-400 text-xs font-bold uppercase tracking-widest">现价 Price</span>
                <span class="text-4xl font-black text-dark tracking-tighter">¥{{ item.price }}</span>
                <span v-if="item.originalPrice" class="text-gray-400 line-through text-lg">¥{{ item.originalPrice }}</span>
              </div>
              <p class="text-primary text-[10px] font-black uppercase tracking-widest">
                <span class="mr-2">✓</span> 原厂品质保证 <span class="mx-2">|</span> <span class="mr-2">✓</span> 极速发货
              </p>
            </div>

            <!-- 卖家信息 -->
            <div class="flex items-center gap-4 p-6 rounded-2xl border border-gray-100 mb-8 hover:bg-gray-50 transition-colors cursor-pointer">
              <n-avatar round size="large" :src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${item.seller_id}`" />
              <div class="flex-1">
                <h4 class="text-dark font-black tracking-tighter uppercase">{{ item.seller_name }}</h4>
                <p class="text-gray-400 text-[10px] font-bold uppercase tracking-widest">认证商户 · 信用极好</p>
              </div>
              <n-button secondary round size="small" class="font-black text-[10px] tracking-widest uppercase">查看店铺</n-button>
            </div>

            <!-- 操作按钮 -->
            <div class="grid grid-cols-2 gap-4 mb-12">
              <n-button 
                type="primary" 
                size="large" 
                strong 
                round 
                class="h-14 uppercase font-black tracking-widest text-xs"
                @click="handleAddToCart(item)"
              >
                加入采购车
              </n-button>
              <n-button 
                secondary 
                size="large" 
                strong 
                round 
                class="h-14 uppercase font-black tracking-widest text-xs"
                @click="handleWantToBuy"
              >
                立即咨询
              </n-button>
            </div>

            <!-- 详情页签 -->
            <n-tabs type="line" animated>
              <n-tab-pane name="desc" tab="零件详情 DESCRIPTION">
                <div class="py-6 text-gray-600 leading-relaxed text-sm whitespace-pre-wrap">
                  {{ item.description || '暂无详细描述' }}
                </div>
                <div class="grid grid-cols-2 gap-y-4 py-6 border-t border-gray-100">
                  <div v-if="item.location" class="flex flex-col">
                    <span class="text-[10px] font-black uppercase tracking-widest text-gray-400">发货地 Location</span>
                    <span class="text-sm font-bold text-dark">{{ item.location }}</span>
                  </div>
                  <div class="flex flex-col">
                    <span class="text-[10px] font-black uppercase tracking-widest text-gray-400">发布时间 Posted</span>
                    <span class="text-sm font-bold text-dark">{{ formatDate(item.created_at) }}</span>
                  </div>
                </div>
              </n-tab-pane>
              <n-tab-pane name="comments" :tab="`评价 REVIEWS (${comments.length})` ">
                <!-- 评论列表 -->
                <div class="py-6 space-y-8">
                  <div v-for="comment in comments" :key="comment.id" class="flex gap-4">
                    <n-avatar round size="small" :src="comment.user.avatar" />
                    <div class="flex-1">
                      <div class="flex justify-between items-center mb-1">
                        <span class="text-xs font-black uppercase tracking-widest text-dark">{{ comment.user.username }}</span>
                        <span class="text-[10px] text-gray-400">{{ formatDate(comment.created_at) }}</span>
                      </div>
                      <n-rate readonly :default-value="comment.rating" size="small" class="mb-2" />
                      <p class="text-sm text-gray-600">{{ comment.content }}</p>
                    </div>
                  </div>
                  <n-empty v-if="comments.length === 0" description="暂无评价" />
                </div>
              </n-tab-pane>
            </n-tabs>
          </div>
        </div>
      </div>
    </n-spin>
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

/* 新增：零件详情弹窗样式 */
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

/* 专业汽车配件平台风格 */
.item-detail-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 16px;
}

.item-detail-view h1 {
  font-size: 28px;
  font-weight: 800;
  color: #111;
  margin-bottom: 16px;
}

.item-detail-view h2 {
  font-size: 22px;
  font-weight: 700;
  color: #333;
  margin-bottom: 12px;
}

.item-detail-view p {
  font-size: 16px;
  color: #555;
  line-height: 1.6;
  margin-bottom: 16px;
}

.item-detail-view .price-section {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.item-detail-view .current-price {
  font-size: 32px;
  font-weight: 700;
  color: #e63946;
}

.item-detail-view .original-price {
  font-size: 18px;
  color: #999;
  text-decoration: line-through;
}

.item-detail-view .description {
  line-height: 1.8;
  white-space: pre-wrap;
  color: #333;
}

.item-detail-view .comment-item {
  padding: 16px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.item-detail-view .similar-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.item-detail-view .similar-item:hover {
  transform: translateY(-4px);
}

.item-detail-view .similar-item-img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 8px;
}

.item-detail-view .similar-item-title {
  font-weight: bold;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-detail-view .similar-item-price {
  color: #e63946;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.item-detail-view .similar-item-seller {
  font-size: 12px;
  color: #999;
}
</style>
