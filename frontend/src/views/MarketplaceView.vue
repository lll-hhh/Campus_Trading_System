<template>
  <div class="marketplace-view">
    <!-- Hero Section / Banner -->
    <div class="relative bg-dark overflow-hidden mb-8 rounded-xl">
      <div class="max-w-7xl mx-auto px-8 py-16 flex flex-col md:flex-row items-center justify-between relative z-10">
        <div class="text-white max-w-xl">
          <h2 class="text-primary font-black tracking-widest uppercase text-sm mb-4">Phoenix Exclusive Offer</h2>
          <h1 class="text-5xl md:text-6xl font-black tracking-tighter mb-6 leading-none">
            PHOENIX-BC86 <br/>
            <span class="text-primary">BRAKE CALIPER</span> <br/>
            <span class="text-yellow-400">KILLER PRICE</span>
          </h1>
          <p class="text-gray-400 text-lg mb-8 font-medium">
            原厂品质制动钳，限时 8 折优惠。为您的行车安全保驾护航。
          </p>
          <div class="flex gap-4">
            <n-button type="primary" size="large" strong round>
              立即抢购
            </n-button>
            <n-button ghost color="#ffffff" size="large" strong round>
              了解更多
            </n-button>
          </div>
        </div>
        <div class="mt-12 md:mt-0 relative">
          <div class="absolute inset-0 bg-primary/20 blur-3xl rounded-full"></div>
          <img 
            src="https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&q=80&w=600" 
            alt="Brake Caliper" 
            class="relative z-10 w-full max-w-md drop-shadow-2xl rotate-12 hover:rotate-0 transition-transform duration-500"
          />
        </div>
      </div>
      <!-- Background Pattern -->
      <div class="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-primary/10 to-transparent"></div>
    </div>

    <!-- 搜索栏 (更专业的设计) -->
    <div class="bg-white p-6 rounded-xl shadow-sm mb-8 border border-gray-100">
      <div class="flex flex-col md:flex-row items-center gap-4 max-w-5xl mx-auto">
        <div class="flex-1 w-full">
          <n-input
            v-model:value="searchKeyword"
            placeholder="输入零件名称、OEM编号或品牌..."
            size="large"
            round
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <span class="text-gray-400">🔍</span>
            </template>
          </n-input>
        </div>
        <n-button type="primary" size="large" strong round class="px-10" @click="handleSearch">
          搜索零件
        </n-button>
        <n-button 
          v-if="authStore.isAuthenticated"
          type="primary" 
          ghost
          size="large" 
          strong
          round
          @click="showPublishModal = true"
        >
          发布供应
        </n-button>
      </div>
      
      <!-- 热门搜索 -->
      <div class="flex items-center gap-3 mt-4 max-w-5xl mx-auto text-xs font-bold uppercase tracking-wider text-gray-400">
        <span class="text-dark">热门搜索:</span>
        <span 
          v-for="keyword in ['刹车片', '火花塞', '机油滤清器', '雨刮片', '蓄电池']" 
          :key="keyword"
          class="cursor-pointer hover:text-primary transition-colors"
          @click="searchKeyword = keyword; handleSearch()"
        >
          {{ keyword }}
        </span>
      </div>
    </div>

    <!-- 分类导航 (更现代的图标按钮) -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-black tracking-tighter text-dark uppercase">零件分类 <span class="text-primary">Categories</span></h3>
        <n-button text type="primary" size="small">查看全部</n-button>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-4">
        <div
          v-for="cat in categories.slice(0, 8)"
          :key="cat.id ?? 'all'"
          class="group cursor-pointer"
          @click="selectCategory(cat.id)"
        >
          <div 
            class="h-20 rounded-xl flex flex-col items-center justify-center transition-all border-2"
            :class="selectedCategory === cat.id ? 'bg-primary border-primary text-white shadow-lg shadow-primary/20' : 'bg-white border-gray-100 text-gray-500 hover:border-primary hover:text-primary'"
          >
            <span class="text-2xl mb-1 group-hover:scale-110 transition-transform">{{ cat.icon }}</span>
            <span class="text-[10px] font-black uppercase tracking-widest">{{ cat.name }}</span>
          </div>
        </div>
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

    <!-- 零件列表 -->
    <n-spin :show="loading">
      <div v-if="items.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
        <div
          v-for="item in items"
          :key="item.id"
          class="group bg-white rounded-xl overflow-hidden border border-gray-100 hover:shadow-2xl hover:shadow-primary/10 transition-all duration-500 flex flex-col"
          @click="goToItemDetail(item.id)"
        >
          <!-- 零件图片 -->
          <div class="relative aspect-square overflow-hidden bg-gray-50">
            <img
              :src="getItemImageUrl(item.images, item.id)"
              :alt="item.title"
              class="w-full h-full object-contain p-4 group-hover:scale-110 transition-transform duration-700"
              loading="lazy"
            />
            <!-- 悬浮操作 -->
            <div class="absolute inset-0 bg-dark/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
              <n-button circle type="primary" @click.stop="handleAddToCart(item)">
                <template #icon>🛒</template>
              </n-button>
              <n-button circle @click.stop="goToItemDetail(item.id)">
                <template #icon>👁️</template>
              </n-button>
            </div>
            <!-- 标签 -->
            <div class="absolute top-4 left-4 flex flex-col gap-2">
              <span v-if="item.condition_type === '全新'" class="bg-primary text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full shadow-lg">New</span>
              <span v-if="item.is_shipped" class="bg-dark text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full shadow-lg">Free Shipping</span>
            </div>
          </div>

          <!-- 零件信息 -->
          <div class="p-6 flex-1 flex flex-col">
            <div class="mb-auto">
              <h3 class="text-dark font-black tracking-tighter text-lg mb-1 line-clamp-1 group-hover:text-primary transition-colors">
                {{ item.title }}
              </h3>
              <p class="text-gray-400 text-[10px] font-bold uppercase tracking-widest mb-4">
                OEM: {{ item.id.toString().padStart(8, '0') }} | {{ item.seller_name }}
              </p>
            </div>

            <div class="flex items-center justify-between pt-4 border-t border-gray-50">
              <div class="flex flex-col">
                <span class="text-gray-400 text-[10px] font-bold uppercase tracking-widest">价格 Price</span>
                <span class="text-dark font-black text-xl tracking-tighter">¥{{ item.price }}</span>
              </div>
              <n-button 
                strong 
                secondary 
                round
                size="small"
                :type="item.isFavorited ? 'primary' : 'default'"
                class="uppercase text-[10px] tracking-widest font-black"
                @click.stop="handleToggleFavorite(item)"
              >
                <template #icon>{{ item.isFavorited ? '❤️' : '🤍' }}</template>
                LIKE
              </n-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <n-empty v-else-if="!loading" description="暂无零件，快来发布第一件吧~">
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

    <!-- 发布零件对话框 -->
    <n-modal 
      v-model:show="showPublishModal" 
      preset="card" 
      title="📤 发布零件" 
      style="width: 600px"
    >
      <n-form :model="newItem" label-placement="left" label-width="80">
        <n-form-item label="零件名称">
          <n-input v-model:value="newItem.name" placeholder="例如：零件iPhone 13 Pro" />
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
              { label: '全新', value: 'new' },
              { label: '99新', value: 'like-new' },
              { label: '95新', value: 'excellent' },
              { label: '9成新', value: 'good' },
              { label: '零件', value: 'used' }
            ]"
          />
        </n-form-item>
        
        <n-form-item label="描述">
          <n-input
            v-model:value="newItem.description"
            type="textarea"
            placeholder="详细描述零件情况..."
            :rows="4"
          />
        </n-form-item>
        
        <n-form-item label="零件图片">
          <n-upload
            v-model:file-list="newItem.images"
            :max="5"
            :accept="'.jpg,.jpeg,.png,.gif'"
            :show-file-list="true"
            :show-preview-button="true"
            :show-remove-button="true"
            :show-download-button="false"
            :show-retry-button="false"
            list-type="image-card"
            :custom-request="customUpload"
            @before-upload="handleBeforeUpload"
            @remove="handleRemoveImage"
          >
            <n-upload-dragger>
              <div style="margin-bottom: 12px">
                <n-icon size="48" :depth="3">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                  </svg>
                </n-icon>
              </div>
              <n-text style="font-size: 14px; text-align: center;">
                点击或拖拽上传图片
              </n-text>
              <n-p depth="3" style="margin: 8px 0 0 0; font-size: 12px; text-align: center; line-height: 1.4;">
                支持 JPG、PNG、GIF 格式<br>最多 5 张图片
              </n-p>
            </n-upload-dragger>
          </n-upload>
        </n-form-item>
        
        <n-form-item label="交易地点">
          <n-input v-model:value="newItem.location" placeholder="例如：东区2号楼" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showPublishModal = false">取消</n-button>
          <n-button type="primary" @click="handlePublish">发布零件</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 零件详情对话框 -->
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
              v-for="(img, idx) in (currentItem.images?.length ? currentItem.images : ['placeholder'])"
              :key="idx"
              :src="currentItem.images?.length ? getFullImageUrl(img) : getItemImageUrl([], currentItem.id)"
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
              🛒 加入采购车
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
import { useRouter, useRoute } from 'vue-router'
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
import { CloseOutline, TimeOutline } from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
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

// 零件列表 - 改为响应式数据
const items = ref<any[]>([])
const totalItems = ref(0)

// 搜索相关状态
const autocompleteOptions = ref<any[]>([])
const searchLoading = ref(false)
const showHotSearches = ref(false)
const showSearchHistory = ref(false)
const hotSearches = ref<any[]>([])
const searchHistory = ref<string[]>([])
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// 分类数据
const categories = ref([
  { id: null, name: '全部分类', icon: '🏪', count: 0 },
  { id: 1, name: '发动机系统', icon: '⚙️', count: 0 },
  { id: 2, name: '传动系统', icon: '�', count: 0 },
  { id: 3, name: '制动系统', icon: '�', count: 0 },
  { id: 4, name: '悬挂转向', icon: '⛓️', count: 0 },
  { id: 5, name: '车身附件', icon: '�', count: 0 },
  { id: 6, name: '电器仪表', icon: '�', count: 0 },
  { id: 7, name: '保养滤芯', icon: '🧪', count: 0 }
])

// 成色选项
const conditionOptions = [
  { label: '全部', value: null },
  { label: '原厂全新', value: '原厂全新' },
  { label: '品牌件', value: '品牌件' },
  { label: '拆车件', value: '拆车件' },
  { label: '翻新件', value: '翻新件' },
  { label: '副厂件', value: '副厂件' }
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

// 加载零件列表
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
    
    // 成色筛选
    if (selectedCondition.value) {
      params.condition = selectedCondition.value
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
    console.error('加载零件失败:', error)
    message.error(error.response?.data?.detail || '加载零件失败')
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
    // 获取各分类零件数量
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

// 搜索相关方法
const handleInput = (value: string) => {
  if (!value) {
    autocompleteOptions.value = []
    showHotSearches.value = true
    showSearchHistory.value = false
    return
  }

  showHotSearches.value = false
  showSearchHistory.value = false

  // 防抖处理
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  debounceTimer = setTimeout(() => {
    fetchAutocomplete(value)
  }, 300)
}

const fetchAutocomplete = async (query: string) => {
  if (!query || query.length < 1) {
    return
  }

  searchLoading.value = true

  try {
    // 调用真实的自动补全API
    const response = await http.get('/search/autocomplete', {
      params: { query, limit: 10 }
    })
    
    // 转换为autocomplete选项格式
    autocompleteOptions.value = response.data.suggestions.map((item: any) => ({
      label: formatLabel(item),
      value: item.text,
      type: item.type,
      count: item.count
    }))
  } catch (error) {
    console.error('自动补全失败:', error)
    autocompleteOptions.value = []
  } finally {
    searchLoading.value = false
  }
}

const formatLabel = (item: any) => {
  const icon = item.type === 'category' ? '📁' : '🔍'
  return `${icon} ${item.text} ${item.count ? `(${item.count})` : ''}`
}

const handleSelect = (value: string) => {
  searchKeyword.value = value
  handleSearch()
}

const selectHotSearch = (keyword: string) => {
  searchKeyword.value = keyword
  handleSearch()
}

const selectHistoryItem = (keyword: string) => {
  searchKeyword.value = keyword
  handleSearch()
}

const clearSearchHistory = () => {
  searchHistory.value = []
  showSearchHistory.value = false
  message.success('搜索历史已清空')
}

const getTrendType = (trend: string) => {
  switch (trend) {
    case 'up':
      return 'error'
    case 'down':
      return 'info'
    default:
      return 'default'
  }
}

// 加载热门搜索
const loadHotSearches = async () => {
  try {
    // 调用真实API加载热门搜索
    const response = await http.get('/search/popular', { params: { limit: 10 } })
    if (response.data.keywords && response.data.keywords.length > 0) {
      hotSearches.value = response.data.keywords
    }
  } catch (error) {
    console.error('加载热门搜索失败:', error)
    // 使用默认数据
    hotSearches.value = [
      { keyword: 'iPhone', count: 150, trend: 'up' },
      { keyword: '自行车', count: 120, trend: 'down' },
      { keyword: '教材', count: 100, trend: 'up' }
    ]
  }
}

// 加载搜索历史
const loadSearchHistory = async () => {
  try {
    // 从localStorage加载
    const history = localStorage.getItem('searchHistory')
    if (history) {
      searchHistory.value = JSON.parse(history)
    }
    
    // 如果用户已登录，尝试从服务器加载
    if (authStore.isAuthenticated) {
      try {
        const response = await http.get('/search/history', { params: { page_size: 10 } })
        if (response.data.history && response.data.history.length > 0) {
          // 合并服务器历史和本地历史
          const serverKeywords = response.data.history.map((h: any) => h.keyword)
          const merged = [...new Set([...serverKeywords, ...searchHistory.value])]
          searchHistory.value = merged.slice(0, 10)
        }
      } catch {
        // 忽略服务器加载错误
      }
    }
  } catch (error) {
    console.error('加载搜索历史失败:', error)
  }
}

// 添加到搜索历史
const addToHistory = (keyword: string) => {
  // 检查是否已存在
  const existsIndex = searchHistory.value.findIndex(item => item === keyword)
  if (existsIndex !== -1) {
    // 移到最前面
    searchHistory.value.splice(existsIndex, 1)
  }

  // 添加新记录
  searchHistory.value.unshift(keyword)

  // 限制历史记录数量
  if (searchHistory.value.length > 10) {
    searchHistory.value = searchHistory.value.slice(0, 10)
  }

  // 保存到localStorage
  localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value))
}

// 搜索
const handleSearch = () => {
  if (!searchKeyword.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }

  // 添加到搜索历史
  addToHistory(searchKeyword.value)

  // 执行搜索
  currentPage.value = 1
  loadItems()

  // 清空建议
  autocompleteOptions.value = []
  showHotSearches.value = false
  showSearchHistory.value = false
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

// ========== 零件详情弹窗 ==========
const showDetailModal = ref(false)
const currentItem = ref<any | null>(null)
const currentImageIndex = ref(0)

const viewItemDetail = (item: any) => {
  currentItem.value = item
  currentImageIndex.value = 0
  showDetailModal.value = true
}

// 跳转到零件详情页
const goToItemDetail = (itemId: number) => {
  router.push(`/item/${itemId}`)
}

// ========== 采购车 & 收藏 ==========

// 加入采购车
const handleAddToCart = async (item: any) => {
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
    message.success(`"${item.title}" 已加入采购车`)
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (detail === '不能购买自己发布的零件') {
      message.warning('不能购买自己的零件哦~')
    } else if (detail?.includes('已下架') || detail?.includes('已售出')) {
      message.warning('该零件已下架或已售出')
    } else {
      message.error(detail || '加入采购车失败')
    }
  }
}

// 收藏/取消收藏
const handleToggleFavorite = async (item: any) => {
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
const handleContactSeller = (item: any) => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  router.push(`/messages?userId=${item.seller_id}&itemId=${item.id}`)
}

// ========== 发布零件弹窗 ==========
const showPublishModal = ref(false)
const newItem = ref({
  name: '',
  category_id: null as number | null,
  price: 0,
  condition: 'used',
  description: '',
  location: '',
  images: [] as any[]
})

const categoryOptions = computed(() => 
  categories.value
    .filter(c => c.id !== null)
    .map(c => ({ label: `${c.icon} ${c.name}`, value: c.id! })) as { label: string; value: number }[]
)

const handlePublish = async () => {
  if (!newItem.value.name || !newItem.value.category_id || !newItem.value.price) {
    message.warning('请填写完整信息')
    return
  }
  
  // 检查是否有图片正在上传
  const uploadingImages = newItem.value.images.filter((file: any) => file.status === 'uploading')
  if (uploadingImages.length > 0) {
    message.warning('请等待图片上传完成')
    return
  }
  
  // 检查是否有成功上传的图片（Naive UI状态为'finished'）
  console.log('当前图片列表:', newItem.value.images)  // 调试日志
  const uploadedImages = newItem.value.images.filter((file: any) => 
    (file.status === 'finished' || file.status === 'done') && file.url
  )
  console.log('已上传图片:', uploadedImages)  // 调试日志
  if (uploadedImages.length === 0) {
    message.warning('请至少上传一张零件图片')
    return
  }
  
  try {
    const categorySlug = categorySlugMap[newItem.value.category_id] || 'other'
    
    // 处理图片URL - 将完整URL转换为相对路径
    const imageUrls = newItem.value.images
      .filter((file: any) => file.url) // 只包含成功上传的文件
      .map((file: any) => {
        // 从完整URL中提取相对路径
        const url = new URL(file.url)
        return url.pathname
      })
    
    await http.post('/items', {
      title: newItem.value.name,
      description: newItem.value.description || newItem.value.name,
      price: newItem.value.price,
      category: categorySlug,
      condition: newItem.value.condition,
      status: 'available',
      images: imageUrls
    })
    
    message.success('发布成功!')
    showPublishModal.value = false
    
    // 重置表单
    newItem.value = {
      name: '',
      category_id: null,
      price: 0,
      condition: 'used',
      description: '',
      location: '',
      images: []
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
  // 处理URL参数
  if (route.query.keyword) {
    searchKeyword.value = route.query.keyword as string
  }
  loadItems()
  loadCategoryStats()
  loadHotSearches()
  loadSearchHistory()
})

// 图片上传处理
const handleBeforeUpload = async (data: { file: File; fileList: any[] }) => {
  // 检查文件类型
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
  if (!allowedTypes.includes(data.file.type)) {
    message.error('只支持 JPG、PNG、GIF 格式的图片')
    return false
  }
  
  // 检查文件大小 (5MB)
  if (data.file.size > 5 * 1024 * 1024) {
    message.error('图片大小不能超过 5MB')
    return false
  }
  
  return true
}

const handleRemoveImage = (file: any) => {
  // 从newItem.images中移除
  const index = newItem.value.images.findIndex((img: any) => img.id === file.id)
  if (index > -1) {
    newItem.value.images.splice(index, 1)
  }
}

// 自定义上传函数
const customUpload = async ({ file, onFinish, onError }: any) => {
  try {
    const formData = new FormData()
    formData.append('file', file.file)
    
    const response = await http.post('/items/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    // 设置文件的URL为完整的服务器URL
    const serverUrl = window.location.origin
    file.url = `${serverUrl}${response.data.url}`
    file.status = 'finished'  // Naive UI 使用 'finished' 表示上传完成
    file.name = file.file.name
    
    console.log('图片上传成功:', file)  // 调试日志
    onFinish()
    message.success('图片上传成功')
  } catch (error: any) {
    console.error('图片上传失败', error)
    file.status = 'error'
    onError()
    message.error(error.response?.data?.detail || '图片上传失败')
  }
}

// 本地占位图列表（存放于public/demo-images目录）
const PLACEHOLDER_IMAGES = [
  '/demo-images/placeholder1.jpg',
  '/demo-images/placeholder2.jpg',
  '/demo-images/placeholder3.jpg',
  '/demo-images/placeholder4.jpg',
  '/demo-images/placeholder5.jpg',
  '/demo-images/placeholder6.jpg',
]

// 根据零件ID获取占位图 URL，保证每个零件稳定但又有区分度
const getPlaceholderImage = (itemId: number) => {
  if (PLACEHOLDER_IMAGES.length === 0) {
    return ''
  }
  const index = Math.abs(itemId) % PLACEHOLDER_IMAGES.length
  return PLACEHOLDER_IMAGES[index]
}

const getFullImageUrl = (relativeUrl: string) => {
  if (!relativeUrl) return ''
  if (/^https?:/i.test(relativeUrl) || relativeUrl.startsWith('data:')) {
    return relativeUrl
  }
  const serverUrl = window.location.origin
  return `${serverUrl}${relativeUrl}`
}

// 获取零件图片URL，支持多图/字符串字段/无图情况
const getItemImageUrl = (images: string[] | string | undefined | null, itemId?: number) => {
  if (Array.isArray(images) && images.length > 0) {
    return getFullImageUrl(images[0])
  }

  if (typeof images === 'string') {
    try {
      const parsed = JSON.parse(images)
      if (Array.isArray(parsed) && parsed.length > 0) {
        return getFullImageUrl(parsed[0])
      }
    } catch (err) {
      // ignore json parse error
    }
    if (images.startsWith('http') || images.startsWith('data:')) {
      return images
    }
    if (images.startsWith('/')) {
      return getFullImageUrl(images)
    }
  }

  return getPlaceholderImage(itemId || 0)
}

// 监听搜索关键词变化
watch(searchKeyword, (newVal) => {
  if (!newVal) {
    showHotSearches.value = true
    showSearchHistory.value = false
  }
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
  line-clamp: 2;
}
</style>
