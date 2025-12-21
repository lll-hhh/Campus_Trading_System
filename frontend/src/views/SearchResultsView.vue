<template>
  <div class="search-results-view">
    <!-- 搜索栏 -->
    <div class="search-header">
      <n-space vertical size="large">
        <n-input
          v-model:value="searchQuery"
          size="large"
          placeholder="搜索商品..."
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
          <template #suffix>
            <n-button type="primary" @click="handleSearch">搜索</n-button>
          </template>
        </n-input>

        <!-- 筛选条件 -->
        <n-space>
          <n-select
            v-model:value="filters.category"
            placeholder="分类"
            :options="categoryOptions"
            clearable
            style="width: 150px"
            @update:value="handleSearch"
          />
          
          <n-input-group>
            <n-input-number
              v-model:value="filters.minPrice"
              placeholder="最低价"
              :min="0"
              style="width: 120px"
              @blur="handleSearch"
            />
            <n-input-number
              v-model:value="filters.maxPrice"
              placeholder="最高价"
              :min="0"
              style="width: 120px"
              @blur="handleSearch"
            />
          </n-input-group>

          <n-select
            v-model:value="filters.status"
            placeholder="状态"
            :options="statusOptions"
            clearable
            style="width: 120px"
            @update:value="handleSearch"
          />

          <n-select
            v-model:value="filters.sortBy"
            placeholder="排序"
            :options="sortOptions"
            style="width: 150px"
            @update:value="handleSearch"
          />
        </n-space>
      </n-space>
    </div>

    <!-- 搜索信息栏 -->
    <div class="search-info">
      <n-space justify="space-between">
        <div class="result-count">
          找到 <strong>{{ total }}</strong> 个结果，关键词：<strong>"{{ currentQuery }}"</strong>
        </div>
        <div class="clear-filters" v-if="hasFilters">
          <n-button text type="primary" @click="clearFilters">
            <template #icon>
              <n-icon><CloseCircleOutline /></n-icon>
            </template>
            清除筛选
          </n-button>
        </div>
      </n-space>
    </div>

    <!-- 相关搜索建议 -->
    <div class="related-searches" v-if="suggestions.length > 0">
      <n-space>
        <span class="label">相关搜索：</span>
        <n-tag
          v-for="(suggestion, index) in suggestions"
          :key="index"
          :bordered="false"
          style="cursor: pointer"
          @click="searchBySuggestion(suggestion)"
        >
          {{ suggestion }}
        </n-tag>
      </n-space>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <n-spin size="large" />
    </div>

    <!-- 搜索结果 -->
    <div v-else-if="items.length > 0" class="search-results">
      <n-grid :x-gap="16" :y-gap="16" :cols="4" responsive="screen">
        <n-grid-item v-for="item in items" :key="item.id">
          <n-card
            :title="item.title"
            hoverable
            class="item-card"
            @click="goToDetail(item.id)"
          >
            <template #cover>
              <img :src="item.image" :alt="item.title" class="item-image" />
            </template>
            
            <div class="item-content">
              <!-- 高亮摘要 -->
              <div class="item-highlight" v-if="item.highlight" v-html="item.highlight"></div>
              
              <div class="item-info">
                <div class="price">¥{{ item.price.toFixed(2) }}</div>
                <div class="category">{{ item.category }}</div>
              </div>

              <n-space class="item-meta" size="small">
                <n-tag size="small" :bordered="false">
                  <template #icon>
                    <n-icon><EyeOutline /></n-icon>
                  </template>
                  {{ item.view_count }}
                </n-tag>
                <n-tag size="small" :bordered="false">
                  <template #icon>
                    <n-icon><HeartOutline /></n-icon>
                  </template>
                  {{ item.favorite_count }}
                </n-tag>
                <n-tag
                  size="small"
                  :type="item.status === '在售' ? 'success' : 'default'"
                  :bordered="false"
                >
                  {{ item.status }}
                </n-tag>
              </n-space>

              <div class="seller-info">
                <n-avatar
                  v-if="item.seller_avatar"
                  :src="item.seller_avatar"
                  size="small"
                  round
                />
                <n-avatar v-else size="small" round>
                  {{ item.seller_name[0] }}
                </n-avatar>
                <span class="seller-name">{{ item.seller_name }}</span>
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- 分页 -->
      <div class="pagination">
        <n-pagination
          v-model:page="currentPage"
          :page-count="pageCount"
          :page-size="pageSize"
          show-size-picker
          :page-sizes="[12, 20, 40, 60]"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <n-empty description="没有找到相关商品">
        <template #icon>
          <n-icon size="64" :component="SearchOutline" />
        </template>
        <template #extra>
          <n-space vertical>
            <div>尝试：</div>
            <n-space>
              <n-button @click="clearFilters">清除筛选条件</n-button>
              <n-button @click="searchQuery = ''; handleSearch()">查看全部</n-button>
            </n-space>
          </n-space>
        </template>
      </n-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  SearchOutline,
  EyeOutline,
  HeartOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'
import { http } from '@/lib/http'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 状态
const searchQuery = ref('')
const currentQuery = ref('')
const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const suggestions = ref<string[]>([])

// 筛选条件
const filters = ref({
  category: null as string | null,
  minPrice: null as number | null,
  maxPrice: null as number | null,
  status: null as string | null,
  sortBy: 'relevance'
})

// 选项
const categoryOptions = [
  { label: '数码产品', value: '数码产品' },
  { label: '图书教材', value: '图书教材' },
  { label: '生活用品', value: '生活用品' },
  { label: '服装配饰', value: '服装配饰' },
  { label: '运动健身', value: '运动健身' },
  { label: '其他', value: '其他' }
]

const statusOptions = [
  { label: '在售', value: '在售' },
  { label: '已售出', value: '已售出' }
]

const sortOptions = [
  { label: '相关度', value: 'relevance' },
  { label: '价格从低到高', value: 'price_asc' },
  { label: '价格从高到低', value: 'price_desc' },
  { label: '最新发布', value: 'time_desc' },
  { label: '最受欢迎', value: 'popular' }
]

// 计算属性
const pageCount = computed(() => Math.ceil(total.value / pageSize.value))

const hasFilters = computed(() => {
  return (
    filters.value.category !== null ||
    filters.value.minPrice !== null ||
    filters.value.maxPrice !== null ||
    filters.value.status !== null ||
    filters.value.sortBy !== 'relevance'
  )
})

// 方法
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  currentQuery.value = searchQuery.value
  currentPage.value = 1

  try {
    // 调用真实的搜索API
    const params: Record<string, any> = {
      q: searchQuery.value,
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: filters.value.sortBy
    }

    if (filters.value.category) {
      params.category = filters.value.category
    }
    if (filters.value.minPrice !== null) {
      params.min_price = filters.value.minPrice
    }
    if (filters.value.maxPrice !== null) {
      params.max_price = filters.value.maxPrice
    }
    if (filters.value.status) {
      params.item_status = filters.value.status === '在售' ? 'available' : 'sold'
    }

    const response = await http.get('/search/search', { params })
    
    // 处理返回数据
    items.value = response.data.items.map((item: any) => ({
      id: item.id,
      title: item.title,
      price: item.price,
      image: item.image || `https://picsum.photos/300/300?random=${item.id}`,
      category: item.category,
      seller_name: item.seller_name,
      seller_avatar: item.seller_avatar,
      view_count: item.view_count || 0,
      favorite_count: item.favorite_count || 0,
      status: item.status === 'available' ? '在售' : '已售出',
      highlight: item.highlight,
      created_at: item.created_at
    }))

    total.value = response.data.total
    suggestions.value = response.data.suggestions || []
  } catch (error: any) {
    console.error('搜索失败:', error)
    message.error(error.response?.data?.detail || '搜索失败，请重试')
  } finally {
    loading.value = false
  }
}

const clearFilters = () => {
  filters.value = {
    category: null,
    minPrice: null,
    maxPrice: null,
    status: null,
    sortBy: 'relevance'
  }
  handleSearch()
}

const searchBySuggestion = (suggestion: string) => {
  searchQuery.value = suggestion
  handleSearch()
}

const goToDetail = (itemId: number) => {
  router.push(`/items/${itemId}`)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  handleSearch()
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  handleSearch()
}

// 初始化
onMounted(() => {
  const query = route.query.q as string
  if (query) {
    searchQuery.value = query
    handleSearch()
  }
})
</script>

<style scoped>
.search-results-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.search-header {
  background: white;
  padding: 24px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.search-info {
  padding: 16px 0;
  margin-bottom: 16px;
}

.result-count {
  font-size: 14px;
  color: #666;
}

.related-searches {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 24px;
}

.related-searches .label {
  color: #666;
  font-size: 14px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.search-results {
  min-height: 400px;
}

.item-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.item-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.item-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.item-content {
  padding: 12px 0;
}

.item-highlight {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-highlight :deep(em) {
  color: #18a058;
  font-style: normal;
  font-weight: bold;
}

.item-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.price {
  font-size: 20px;
  font-weight: bold;
  color: #d03050;
}

.category {
  font-size: 13px;
  color: #999;
}

.item-meta {
  margin-bottom: 12px;
}

.seller-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.seller-name {
  font-size: 13px;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding: 24px 0;
}

.empty-state {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 响应式 */
@media (max-width: 1200px) {
  .search-results :deep(.n-grid) {
    grid-template-columns: repeat(3, 1fr) !important;
  }
}

@media (max-width: 768px) {
  .search-results :deep(.n-grid) {
    grid-template-columns: repeat(2, 1fr) !important;
  }
  
  .search-header {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .search-results :deep(.n-grid) {
    grid-template-columns: 1fr !important;
  }
}
</style>
