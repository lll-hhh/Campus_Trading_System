<template>
  <div class="search-autocomplete">
    <n-auto-complete
      v-model:value="searchValue"
      :options="autocompleteOptions"
      :loading="loading"
      placeholder="搜索商品、分类..."
      size="large"
      clearable
      @select="handleSelect"
      @update:value="handleInput"
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <n-icon><SearchOutline /></n-icon>
      </template>
      <template #suffix>
        <n-button
          type="primary"
          :loading="loading"
          @click="handleSearch"
        >
          搜索
        </n-button>
      </template>
    </n-auto-complete>

    <!-- 热门搜索下拉面板 -->
    <transition name="fade">
      <div v-if="showHotSearches && !searchValue" class="hot-searches-panel">
        <div class="panel-header">
          <n-space justify="space-between">
            <span class="title">🔥 热门搜索</span>
            <n-button text size="small" @click="showHotSearches = false">
              <template #icon>
                <n-icon><CloseOutline /></n-icon>
              </template>
            </n-button>
          </n-space>
        </div>
        <div class="panel-content">
          <n-space>
            <n-tag
              v-for="(item, index) in hotSearches"
              :key="index"
              :type="getTrendType(item.trend)"
              :bordered="false"
              style="cursor: pointer"
              @click="selectHotSearch(item.keyword)"
            >
              <template #icon>
                <n-icon v-if="item.trend === 'up'"><TrendingUpOutline /></n-icon>
                <n-icon v-else-if="item.trend === 'down'"><TrendingDownOutline /></n-icon>
              </template>
              {{ item.keyword }}
            </n-tag>
          </n-space>
        </div>
      </div>
    </transition>

    <!-- 搜索历史下拉面板 -->
    <transition name="fade">
      <div v-if="showHistory && searchHistory.length > 0" class="history-panel">
        <div class="panel-header">
          <n-space justify="space-between">
            <span class="title">🕒 搜索历史</span>
            <n-button text size="small" @click="clearHistory">
              清空
            </n-button>
          </n-space>
        </div>
        <div class="panel-content">
          <div
            v-for="item in searchHistory"
            :key="item.id"
            class="history-item"
            @click="selectHistory(item.keyword)"
          >
            <n-space justify="space-between">
              <span class="keyword">{{ item.keyword }}</span>
              <n-button
                text
                size="small"
                @click.stop="deleteHistoryItem(item.id)"
              >
                <template #icon>
                  <n-icon><CloseOutline /></n-icon>
                </template>
              </n-button>
            </n-space>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  SearchOutline,
  CloseOutline,
  TrendingUpOutline,
  TrendingDownOutline
} from '@vicons/ionicons5'
import { http } from '@/lib/http'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

// Props
const props = defineProps<{
  modelValue?: string
}>()

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'search', query: string): void
}>()

// 状态
const searchValue = ref(props.modelValue || '')
const loading = ref(false)
const autocompleteOptions = ref<any[]>([])
const showHotSearches = ref(false)
const showHistory = ref(false)

// 热门搜索
const hotSearches = ref([
  { keyword: 'iPhone 15', count: 1234, trend: 'up' },
  { keyword: 'MacBook', count: 890, trend: 'stable' },
  { keyword: 'AirPods', count: 756, trend: 'up' },
  { keyword: 'iPad', count: 654, trend: 'down' },
  { keyword: '小米手机', count: 543, trend: 'up' }
])

// 搜索历史
const searchHistory = ref<any[]>([])

// 防抖定时器
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// 监听值变化
watch(() => props.modelValue, (newVal) => {
  searchValue.value = newVal || ''
})

watch(searchValue, (newVal) => {
  emit('update:modelValue', newVal)
})

// 方法
const handleInput = (value: string) => {
  if (!value) {
    autocompleteOptions.value = []
    showHotSearches.value = true
    return
  }

  showHotSearches.value = false
  showHistory.value = false

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

  loading.value = true

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
    // 降级使用本地模糊匹配
    autocompleteOptions.value = []
  } finally {
    loading.value = false
  }
}

const formatLabel = (item: any) => {
  const icon = item.type === 'category' ? '📁' : '🔍'
  return `${icon} ${item.text} ${item.count ? `(${item.count})` : ''}`
}

const handleSelect = (value: string) => {
  searchValue.value = value
  handleSearch()
}

const handleSearch = () => {
  if (!searchValue.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }

  // 添加到搜索历史
  addToHistory(searchValue.value)

  // 触发搜索事件
  emit('search', searchValue.value)

  // 跳转到搜索结果页
  router.push({
    path: '/search',
    query: { q: searchValue.value }
  })

  // 清空建议
  autocompleteOptions.value = []
  showHotSearches.value = false
}

const selectHotSearch = (keyword: string) => {
  searchValue.value = keyword
  handleSearch()
}

const selectHistory = (keyword: string) => {
  searchValue.value = keyword
  handleSearch()
}

const addToHistory = (keyword: string) => {
  // 检查是否已存在
  const exists = searchHistory.value.find(item => item.keyword === keyword)
  if (exists) {
    // 移到最前面
    searchHistory.value = [
      exists,
      ...searchHistory.value.filter(item => item.keyword !== keyword)
    ]
  } else {
    // 添加新记录
    searchHistory.value.unshift({
      id: Date.now(),
      keyword,
      searched_at: new Date(),
      result_count: 0
    })

    // 限制历史记录数量
    if (searchHistory.value.length > 10) {
      searchHistory.value = searchHistory.value.slice(0, 10)
    }
  }
  
  // 保存到 localStorage
  try {
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value))
  } catch (e) {
    console.error('保存搜索历史失败:', e)
  }
}

const deleteHistoryItem = async (id: number) => {
  searchHistory.value = searchHistory.value.filter(item => item.id !== id)
  // 如果用户已登录，调用API删除
  if (authStore.isAuthenticated) {
    try {
      await http.delete(`/search/history/${id}`)
    } catch (error) {
      console.error('删除搜索历史失败:', error)
    }
  }
  // 更新 localStorage
  localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value))
}

const clearHistory = async () => {
  // 如果用户已登录，调用API清空
  if (authStore.isAuthenticated) {
    try {
      await http.delete('/search/history')
    } catch (error) {
      console.error('清空搜索历史失败:', error)
    }
  }
  searchHistory.value = []
  showHistory.value = false
  localStorage.removeItem('searchHistory')
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

// 加载搜索历史
const loadSearchHistory = async () => {
  try {
    // 优先从 localStorage 加载
    const localHistory = localStorage.getItem('searchHistory')
    if (localHistory) {
      searchHistory.value = JSON.parse(localHistory)
    }
    
    // 如果用户已登录，从API加载并合并
    if (authStore.isAuthenticated) {
      const response = await http.get('/search/history', {
        params: { page: 1, page_size: 10 }
      })
      if (response.data.history && response.data.history.length > 0) {
        // 合并服务器历史和本地历史
        const serverHistory = response.data.history
        const merged = [...serverHistory]
        searchHistory.value.forEach((item: any) => {
          if (!merged.find((h: any) => h.keyword === item.keyword)) {
            merged.push(item)
          }
        })
        searchHistory.value = merged.slice(0, 10)
      }
    }
  } catch (error) {
    console.error('加载搜索历史失败:', error)
  }
}

// 加载热门搜索
const loadHotSearches = async () => {
  try {
    const response = await http.get('/search/popular', {
      params: { limit: 10 }
    })
    if (response.data.keywords && response.data.keywords.length > 0) {
      hotSearches.value = response.data.keywords
    }
  } catch (error) {
    console.error('加载热门搜索失败:', error)
    // 使用默认热搜
  }
}

// 初始化
onMounted(() => {
  loadSearchHistory()
  loadHotSearches()
})
</script>

<style scoped>
.search-autocomplete {
  position: relative;
  width: 100%;
}

.hot-searches-panel,
.history-panel {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header .title {
  font-weight: 500;
  font-size: 14px;
}

.panel-content {
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.history-item:hover {
  background: #f5f5f5;
}

.history-item .keyword {
  font-size: 14px;
  color: #333;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
