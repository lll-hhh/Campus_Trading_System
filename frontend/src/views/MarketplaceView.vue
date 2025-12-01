<template>
  <div class="marketplace-view">
    <!-- 搜索栏 -->
    <div class="search-bar bg-gradient-to-r from-orange-400 to-orange-500 p-4 rounded-lg mb-4">
      <div class="flex items-center gap-4 max-w-4xl mx-auto">
        <div class="flex-1">
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索宝贝、店铺..."
            size="large"
            round
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <span>🔍</span>
            </template>
          </n-input>
        </div>
        <n-button type="warning" size="large" @click="handleSearch">
          搜索
        </n-button>
        <n-button 
          v-if="authStore.isAuthenticated"
          type="primary" 
          size="large" 
          @click="showPublishModal = true"
        >
          ✏️ 我要卖
        </n-button>
      </div>
      
      <!-- 热门搜索 -->
      <div class="flex items-center gap-2 mt-2 max-w-4xl mx-auto text-white text-sm">
        <span>热门:</span>
        <span 
          v-for="keyword in ['iPhone', '自行车', '教材', '显示器', '二手书']" 
          :key="keyword"
          class="cursor-pointer hover:underline"
          @click="searchKeyword = keyword; handleSearch()"
        >
          {{ keyword }}
        </span>
      </div>
    </div>

    <!-- 分类导航 -->
    <div class="categories-bar bg-white p-4 rounded-lg mb-4 shadow-sm">
      <div class="flex flex-wrap gap-2">
        <n-button
          v-for="cat in categories"
          :key="cat.id ?? 'all'"
          :type="selectedCategory === cat.id ? 'warning' : 'default'"
          :tertiary="selectedCategory !== cat.id"
          round
          @click="selectCategory(cat.id)"
        >
          {{ cat.icon }} {{ cat.name }}
          <n-tag v-if="cat.count > 0" size="small" round class="ml-1">
            {{ cat.count }}
          </n-tag>
        </n-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar bg-white p-4 rounded-lg mb-4 shadow-sm">
      <div class="flex flex-wrap items-center gap-4">
        <!-- 成色筛选 -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500">成色:</span>
          <n-button
            v-for="opt in conditionOptions"
            :key="opt.value ?? 'all'"
            :type="selectedCondition === opt.value ? 'primary' : 'default'"
            :tertiary="selectedCondition !== opt.value"
            size="small"
            @click="handleConditionChange(opt.value)"
          >
            {{ opt.label }}
          </n-button>
        </div>
        
        <!-- 价格区间 -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500">价格:</span>
          <n-input-number
            v-model:value="priceRange.min"
            placeholder="最低价"
            size="small"
            :min="0"
            style="width: 100px"
            @blur="handleSearch"
          />
          <span>-</span>
          <n-input-number
            v-model:value="priceRange.max"
            placeholder="最高价"
            size="small"
            :min="0"
            style="width: 100px"
            @blur="handleSearch"
          />
        </div>
        
        <!-- 排序 -->
        <div class="flex items-center gap-2 ml-auto">
          <span class="text-gray-500">排序:</span>
          <n-select
            v-model:value="sortBy"
            :options="sortOptions"
            size="small"
            style="width: 140px"
            @update:value="handleSortChange"
          />
        </div>
      </div>
    </div>

    <!-- 商品列表 -->
    <n-spin :show="loading">
      <div v-if="items.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <n-card
          v-for="item in items"
          :key="item.id"
          hoverable
          class="item-card cursor-pointer"
          @click="goToItemDetail(item.id)"
        >
          <!-- 商品图片 -->
          <div class="relative">
            <img
              :src="item.images[0]"
              :alt="item.title"
              class="w-full h-48 object-cover rounded-t-lg"
            />
            <!-- 标签 -->
            <div class="absolute top-2 left-2 flex gap-1">
              <n-tag v-if="item.condition_type === '全新'" type="success" size="small">全新</n-tag>
              <n-tag v-if="item.is_shipped" type="info" size="small">包邮</n-tag>
            </div>
            <!-- 图片数量 -->
            <div v-if="item.images.length > 1" class="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
              📷 {{ item.images.length }}
            </div>
          </div>

          <!-- 商品信息 -->
          <div class="p-3">
            <!-- 价格 -->
            <div class="flex items-baseline gap-2 mb-2">
              <span class="text-red-500 text-xl font-bold">¥{{ item.price }}</span>
              <span v-if="item.original_price && item.original_price > item.price" class="text-gray-400 text-sm line-through">
                ¥{{ item.original_price }}
              </span>
            </div>

            <!-- 标题 -->
            <h3 class="text-sm font-medium mb-2 line-clamp-2">
              {{ item.emoji }} {{ item.title }}
            </h3>

            <!-- 标签 -->
            <div class="flex flex-wrap gap-1 mb-2">
              <n-tag v-for="tag in item.tags?.slice(0, 3)" :key="tag" size="small" round>
                {{ tag }}
              </n-tag>
            </div>

            <!-- 卖家和统计 -->
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>👤 {{ item.seller_name }}</span>
              <span>👁️ {{ item.view_count }}</span>
            </div>
            
            <!-- 位置和时间 -->
            <div class="flex items-center justify-between text-xs text-gray-400 mt-1">
              <span v-if="item.location">📍 {{ item.location }}</span>
              <span>{{ formatTime(item.created_at) }}</span>
            </div>
          </div>

          <!-- 快捷操作 -->
          <div class="px-3 pb-3 flex gap-2">
            <n-button 
              size="small" 
              type="primary"
              @click.stop="handleAddToCart(item)"
            >
              🛒 加购
            </n-button>
            <n-button 
              size="small"
              :type="item.isFavorited ? 'error' : 'default'"
              @click.stop="handleToggleFavorite(item)"
            >
              {{ item.isFavorited ? '❤️' : '🤍' }}
            </n-button>
          </div>
        </n-card>
      </div>

      <!-- 空状态 -->
      <n-empty v-else-if="!loading" description="暂无商品，快来发布第一件吧~">
        <template #extra>
          <n-button type="primary" @click="showPublishModal = true">
            ✏️ 立即发布
          </n-button>
        </template>
      </n-empty>
    </n-spin>

    <!-- 分页 -->
    <div v-if="totalCount > 0" class="flex justify-center mt-8">
      <n-pagination
        v-model:page="currentPage"
        :page-count="totalPages"
        :page-size="pageSize"
        show-size-picker
        :page-sizes="[20, 40, 60, 100]"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>

    <!-- 发布商品对话框 -->
    <n-modal 
      v-model:show="showPublishModal" 
      preset="card" 
      title="📤 发布商品" 
      style="width: 600px"
    >
      <n-form :model="newItem" label-placement="left" label-width="80">
        <n-form-item label="商品名称">
          <n-input v-model:value="newItem.name" placeholder="例如：二手iPhone 13 Pro" />
        </n-form-item>
        
        <n-form-item label="分类">
          <n-select v-model:value="newItem.category_id" :options="categoryOptions" placeholder="请选择分类" />
        </n-form-item>
        
        <n-form-item label="价格">
          <n-input-number v-model:value="newItem.price" :min="0" placeholder="输入价格" style="width: 100%">
            <template #prefix>¥</template>
          </n-input-number>
        </n-form-item>
        
        <n-form-item label="成色">
          <n-select
            v-model:value="newItem.condition"
            :options="[
              { label: '全新', value: '全新' },
              { label: '99新', value: '99新' },
              { label: '95新', value: '95新' },
              { label: '9成新', value: '9成新' },
              { label: '二手', value: '二手' }
            ]"
          />
        </n-form-item>
        
        <n-form-item label="描述">
          <n-input
            v-model:value="newItem.description"
            type="textarea"
            placeholder="详细描述商品情况..."
            :rows="4"
          />
        </n-form-item>
        
        <n-form-item label="交易地点">
          <n-input v-model:value="newItem.location" placeholder="例如：东区2号楼" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showPublishModal = false">取消</n-button>
          <n-button type="primary" @click="handlePublish">发布商品</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 商品详情对话框 -->
    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      :title="currentItem?.title"
      style="width: 900px; max-height: 90vh"
    >
      <div v-if="currentItem" class="flex gap-6">
        <!-- 左侧图片 -->
        <div class="w-1/2">
          <n-carousel show-arrow>
            <img
              v-for="(img, idx) in currentItem.images"
              :key="idx"
              :src="img"
              class="w-full h-80 object-cover rounded"
            />
          </n-carousel>
        </div>

        <!-- 右侧信息 -->
        <div class="w-1/2 space-y-4">
          <!-- 价格 -->
          <div class="flex items-baseline gap-2">
            <span class="text-red-500 text-3xl font-bold">¥{{ currentItem.price }}</span>
            <span v-if="currentItem.original_price" class="text-gray-400 line-through">
              ¥{{ currentItem.original_price }}
            </span>
          </div>

          <!-- 标签 -->
          <div class="flex flex-wrap gap-2">
            <n-tag v-for="tag in currentItem.tags" :key="tag" type="info">
              {{ tag }}
            </n-tag>
          </div>

          <!-- 描述 -->
          <p class="text-gray-600">{{ currentItem.description }}</p>

          <!-- 卖家信息 -->
          <div class="bg-gray-50 p-4 rounded">
            <div class="flex items-center gap-3">
              <n-avatar :size="48">{{ currentItem.seller_name?.[0] }}</n-avatar>
              <div>
                <div class="font-bold">{{ currentItem.seller_name }}</div>
                <n-rate :value="4.5" readonly size="small" />
              </div>
            </div>
          </div>

          <!-- 统计 -->
          <div class="flex gap-4 text-sm text-gray-500">
            <span>👁️ {{ currentItem.view_count }} 浏览</span>
            <span>❤️ {{ currentItem.favorite_count }} 收藏</span>
            <span v-if="currentItem.location">📍 {{ currentItem.location }}</span>
          </div>

          <n-divider />

          <!-- 操作按钮 -->
          <div class="space-y-2">
            <n-button type="warning" size="large" block @click="handleContactSeller(currentItem!)">
              💬 联系卖家
            </n-button>
            <n-button type="primary" size="large" block @click="handleAddToCart(currentItem!)">
              🛒 加入购物车
            </n-button>
            <n-button 
              size="large" 
              block 
              :type="currentItem.isFavorited ? 'error' : 'default'"
              @click="handleToggleFavorite(currentItem!)"
            >
              {{ currentItem.isFavorited ? '❤️ 已收藏' : '🤍 收藏' }}
            </n-button>
          </div>

          <n-alert type="warning" class="mt-4">
            <template #header>⚠️ 交易提示</template>
            <p class="text-sm">请线下当面交易，验货后付款。禁止线上转账！</p>
          </n-alert>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NSpace,
  NButton,
  NInput,
  NSelect,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NInputNumber,
  NCarousel,
  NTabs,
  NTabPane,
  NAvatar,
  NPagination,
  NEmpty,
  NSpin,
  NRate,
  NDivider,
  NAlert,
  useMessage
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { http } from '@/lib/http'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

// ========== 状态定义 ==========
const loading = ref(false)
const searchKeyword = ref('')
const selectedCategory = ref<number | null>(null)
const selectedCondition = ref<string | null>(null)
const priceRange = ref({ min: null as number | null, max: null as number | null })
const sortBy = ref('default')
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

// 商品列表 - 改为响应式数据
const items = ref<any[]>([])
const totalItems = ref(0)

// 分类数据
const categories = ref([
  { id: null, name: '全部分类', icon: '🏪', count: 0 },
  { id: 1, name: '数码产品', icon: '📱', count: 0 },
  { id: 2, name: '图书教材', icon: '📚', count: 0 },
  { id: 3, name: '生活用品', icon: '🛋️', count: 0 },
  { id: 4, name: '运动器材', icon: '⚽', count: 0 },
  { id: 5, name: '服装鞋包', icon: '👔', count: 0 },
  { id: 6, name: '美妆护肤', icon: '💄', count: 0 },
  { id: 7, name: '其他闲置', icon: '📦', count: 0 }
])

// 成色选项
const conditionOptions = [
  { label: '全部', value: null },
  { label: '全新', value: '全新' },
  { label: '99新', value: '99新' },
  { label: '95新', value: '95新' },
  { label: '9成新', value: '9成新' },
  { label: '二手', value: '二手' }
]

// 排序选项
const sortOptions = [
  { label: '综合排序', value: 'default' },
  { label: '最新发布', value: 'newest' },
  { label: '价格从低到高', value: 'price_asc' },
  { label: '价格从高到低', value: 'price_desc' },
  { label: '浏览最多', value: 'views' }
]

// 分类 slug 映射
const categorySlugMap: Record<number, string> = {
  1: 'electronics',
  2: 'books',
  3: 'daily',
  4: 'sports',
  5: 'fashion',
  6: 'beauty',
  7: 'other'
}

// 分类 emoji 映射
const categoryEmojiMap: Record<string, string> = {
  'electronics': '📱',
  'books': '📚',
  'daily': '🛋️',
  'sports': '⚽',
  'fashion': '👔',
  'beauty': '💄',
  'other': '📦'
}

// ========== API 调用 ==========

// 加载商品列表
const loadItems = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
      status: 'available'
    }
    
    // 分类筛选
    if (selectedCategory.value) {
      params.category = categorySlugMap[selectedCategory.value] || ''
    }
    
    // 关键词搜索
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value.trim()
    }
    
    // 价格区间
    if (priceRange.value.min !== null) {
      params.min_price = priceRange.value.min
    }
    if (priceRange.value.max !== null) {
      params.max_price = priceRange.value.max
    }
    
    const response = await http.get('/items', { params })
    
    // 处理返回数据
    items.value = response.data.items.map((item: any) => ({
      ...item,
      original_price: item.original_price || Math.round(item.price * 1.3),
      emoji: categoryEmojiMap[item.category] || '📦',
      images: item.images?.length > 0 ? item.images : [`https://picsum.photos/400/400?random=${item.id}`],
      tags: parseTags(item),
      isFavorited: false
    }))
    
    totalCount.value = response.data.total
    
    // 如果用户已登录，检查收藏状态
    if (authStore.isAuthenticated) {
      await checkFavoriteStatus()
    }
    
  } catch (error: any) {
    console.error('加载商品失败:', error)
    message.error(error.response?.data?.detail || '加载商品失败')
  } finally {
    loading.value = false
  }
}

// 解析标签
const parseTags = (item: any): string[] => {
  const tags: string[] = []
  if (item.condition_type) tags.push(item.condition_type)
  if (item.is_negotiable) tags.push('可议价')
  if (item.is_shipped) tags.push('包邮')
  if (item.tags) {
    try {
      const parsed = typeof item.tags === 'string' ? JSON.parse(item.tags) : item.tags
      if (Array.isArray(parsed)) tags.push(...parsed)
    } catch { }
  }
  return tags.slice(0, 4) // 最多显示4个标签
}

// 检查收藏状态
const checkFavoriteStatus = async () => {
  try {
    const response = await http.get('/favorites')
    const favoriteIds = new Set(response.data.map((f: any) => f.item_id))
    items.value.forEach(item => {
      item.isFavorited = favoriteIds.has(item.id)
    })
  } catch (error) {
    console.error('检查收藏状态失败:', error)
  }
}

// 加载分类统计
const loadCategoryStats = async () => {
  try {
    // 获取各分类商品数量
    for (const cat of categories.value) {
      if (cat.id === null) {
        // 全部分类
        const res = await http.get('/items', { params: { page_size: 1, status: 'available' } })
        cat.count = res.data.total
      } else {
        const slug = categorySlugMap[cat.id]
        if (slug) {
          const res = await http.get('/items', { params: { page_size: 1, category: slug, status: 'available' } })
          cat.count = res.data.total
        }
      }
    }
  } catch (error) {
    console.error('加载分类统计失败:', error)
  }
}

// ========== 用户操作 ==========

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadItems()
}

// 选择分类
const selectCategory = (categoryId: number | null) => {
  selectedCategory.value = categoryId
  currentPage.value = 1
  loadItems()
}

// 选择成色
const handleConditionChange = (value: string | null) => {
  selectedCondition.value = value
  currentPage.value = 1
  loadItems()
}

// 排序变更
const handleSortChange = (value: string) => {
  sortBy.value = value
  currentPage.value = 1
  loadItems()
}

// 页码变更
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadItems()
}

// 每页数量变更
const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadItems()
}

// 计算总页数
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

// ========== 商品详情弹窗 ==========
const showDetailModal = ref(false)
const currentItem = ref<ItemData | null>(null)
const currentImageIndex = ref(0)

const viewItemDetail = (item: ItemData) => {
  currentItem.value = item
  currentImageIndex.value = 0
  showDetailModal.value = true
}

// 跳转到商品详情页
const goToItemDetail = (itemId: number) => {
  router.push(`/item/${itemId}`)
}

// ========== 购物车 & 收藏 ==========

// 加入购物车
const handleAddToCart = async (item: ItemData) => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  try {
    await http.post('/cart', {
      item_id: item.id,
      quantity: 1
    })
    message.success(`"${item.title}" 已加入购物车`)
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (detail === '不能购买自己发布的商品') {
      message.warning('不能购买自己的商品哦~')
    } else if (detail?.includes('已下架') || detail?.includes('已售出')) {
      message.warning('该商品已下架或已售出')
    } else {
      message.error(detail || '加入购物车失败')
    }
  }
}

// 收藏/取消收藏
const handleToggleFavorite = async (item: ItemData) => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  try {
    if (item.isFavorited) {
      await http.delete(`/favorites/${item.id}`)
      item.isFavorited = false
      message.success('已取消收藏')
    } else {
      await http.post(`/favorites/${item.id}`)
      item.isFavorited = true
      message.success('收藏成功')
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || '操作失败')
  }
}

// 联系卖家
const handleContactSeller = (item: ItemData) => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  router.push(`/messages?userId=${item.seller_id}`)
}

// ========== 发布商品弹窗 ==========
const showPublishModal = ref(false)
const newItem = ref({
  name: '',
  category_id: null as number | null,
  price: 0,
  condition: '二手',
  description: '',
  location: ''
})

const categoryOptions = computed(() => 
  categories.value
    .filter(c => c.id !== null)
    .map(c => ({ label: `${c.icon} ${c.name}`, value: c.id }))
)

const handlePublish = async () => {
  if (!newItem.value.name || !newItem.value.category_id || !newItem.value.price) {
    message.warning('请填写完整信息')
    return
  }
  
  try {
    const categorySlug = categorySlugMap[newItem.value.category_id] || 'other'
    await http.post('/items', {
      title: newItem.value.name,
      description: newItem.value.description || newItem.value.name,
      price: newItem.value.price,
      category: categorySlug,
      condition: newItem.value.condition,
      status: 'available',
      images: []
    })
    
    message.success('发布成功!')
    showPublishModal.value = false
    
    // 重置表单
    newItem.value = {
      name: '',
      category_id: null,
      price: 0,
      condition: '二手',
      description: '',
      location: ''
    }
    
    // 刷新列表
    await loadItems()
  } catch (error: any) {
    message.error(error.response?.data?.detail || '发布失败')
  }
}

// 格式化时间
const formatTime = (dateStr: string) => {
  if (!dateStr) return '刚刚'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  
  return date.toLocaleDateString()
}

// 页面加载时获取数据
onMounted(() => {
  loadItems()
  loadCategoryStats()
})
</script>

<style scoped>
.marketplace-view {
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

.item-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.item-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
