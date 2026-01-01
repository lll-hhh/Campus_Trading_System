<template>
  <div class="my-items min-h-screen bg-[#f4f4f4]">
    <!-- Header Section -->
    <div class="bg-[#2e3235] text-white py-8 mb-8">
      <div class="max-w-7xl mx-auto px-4">
        <h1 class="text-3xl font-black tracking-tighter uppercase italic">
          My <span class="text-primary">Inventory</span>
          <span class="block text-sm font-normal tracking-widest mt-1 opacity-60 italic">PHOENIX AUTO PARTS / STOCK MANAGEMENT</span>
        </h1>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 pb-12">
      <div class="bg-white shadow-sm border border-gray-200">
        <n-spin :show="loading">
          <n-tabs v-model:value="activeTab" type="line" animated class="px-6 pt-4">
            <n-tab-pane name="selling" tab="在售中 (SELLING)">
              <div v-if="sellingItems.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6 pb-6">
                <div v-for="item in sellingItems" :key="item.id" class="group bg-white border border-gray-200 hover:border-primary transition-all duration-300">
                  <div class="relative aspect-video overflow-hidden bg-gray-100">
                    <img
                      :src="getItemImageUrl(item.images, item.id)"
                      :alt="item.title"
                      class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div class="absolute top-0 left-0 bg-primary text-white text-[10px] font-bold px-2 py-1 uppercase tracking-tighter">
                      Active
                    </div>
                  </div>
                  <div class="p-4">
                    <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">Part ID: #{{ item.id }}</div>
                    <h3 class="font-black text-lg leading-tight mb-2 uppercase italic truncate">{{ item.title }}</h3>
                    <div class="flex items-baseline gap-2 mb-4">
                      <span class="text-2xl font-black text-[#2e3235]">¥{{ item.price }}</span>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-2 mb-4 text-[10px] font-bold uppercase tracking-tighter text-gray-500">
                      <div class="bg-gray-50 p-2 border border-gray-100">
                        👁️ {{ item.views }} Views
                      </div>
                      <div class="bg-gray-50 p-2 border border-gray-100">
                        💬 {{ item.inquiries }} Inquiries
                      </div>
                    </div>

                    <div class="flex gap-2">
                      <n-button block strong secondary type="primary" @click="editItem(item)" class="uppercase font-bold italic">
                        Edit
                      </n-button>
                      <n-button block strong secondary type="error" @click="removeItem(item)" class="uppercase font-bold italic">
                        Remove
                      </n-button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center text-gray-400 py-20">
                <p class="text-xl font-bold uppercase italic tracking-widest">No active parts in inventory</p>
                <n-button type="primary" class="mt-4 uppercase font-bold italic" @click="router.push('/publish')">Add New Part</n-button>
              </div>
            </n-tab-pane>

            <n-tab-pane name="sold" tab="已售出 (SOLD)">
              <div v-if="soldItems.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6 pb-6">
                <div v-for="item in soldItems" :key="item.id" class="bg-white border border-gray-200 opacity-75">
                  <div class="relative aspect-video overflow-hidden bg-gray-100">
                    <img
                      :src="getItemImageUrl(item.images, item.id)"
                      :alt="item.title"
                      class="w-full h-full object-cover grayscale"
                    />
                    <div class="absolute inset-0 bg-black/40 flex items-center justify-center">
                      <span class="text-white font-black text-2xl uppercase italic tracking-tighter border-4 border-white px-4 py-1">SOLD</span>
                    </div>
                  </div>
                  <div class="p-4">
                    <h3 class="font-black text-lg leading-tight mb-2 uppercase italic truncate text-gray-500">{{ item.title }}</h3>
                    <p class="text-xl font-black text-gray-400 mb-2">¥{{ item.price }}</p>
                    <div class="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                      Sold Date: {{ formatDate(item.updated_at || item.created_at) }}
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center text-gray-400 py-20">
                <p class="text-xl font-bold uppercase italic tracking-widest">No sold parts yet</p>
              </div>
            </n-tab-pane>

            <n-tab-pane name="removed" tab="已下架 (ARCHIVED)">
              <div v-if="removedItems.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6 pb-6">
                <div v-for="item in removedItems" :key="item.id" class="bg-white border border-gray-200">
                  <div class="relative aspect-video overflow-hidden bg-gray-100">
                    <img
                      :src="getItemImageUrl(item.images, item.id)"
                      :alt="item.title"
                      class="w-full h-full object-cover grayscale"
                    />
                  </div>
                  <div class="p-4">
                    <h3 class="font-black text-lg leading-tight mb-2 uppercase italic truncate">{{ item.title }}</h3>
                    <p class="text-xl font-black text-gray-400 mb-4">¥{{ item.price }}</p>
                    <n-button block strong secondary @click="restoreItem(item)" class="uppercase font-bold italic">
                      Relist Part
                    </n-button>
                  </div>
                </div>
              </div>
              <div v-else class="text-center text-gray-400 py-20">
                <p class="text-xl font-bold uppercase italic tracking-widest">Archive is empty</p>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-spin>
      </div>
    </div>

    <!-- Edit Item Modal -->
    <n-modal
      v-model:show="editModalVisible"
      preset="card"
      title="编辑零件"
      size="huge"
      :bordered="false"
      :segmented="false"
    >
      <n-form :model="editForm" label-placement="top">
        <n-form-item label="零件标题" path="title">
          <n-input v-model:value="editForm.title" placeholder="请输入零件标题" />
        </n-form-item>
        
        <n-form-item label="零件描述" path="description">
          <n-input 
            v-model:value="editForm.description" 
            type="textarea" 
            placeholder="请输入零件描述"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </n-form-item>
        
        <n-form-item label="价格" path="price">
          <n-input-number 
            v-model:value="editForm.price" 
            :min="0" 
            :precision="2"
            placeholder="请输入价格"
            class="w-full"
          />
        </n-form-item>
        
        <n-form-item label="零件成色" path="condition">
          <n-select 
            v-model:value="editForm.condition" 
            :options="conditionOptions"
            placeholder="请选择零件成色"
          />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="cancelEdit">取消</n-button>
          <n-button type="primary" @click="saveEdit">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NSpin, NTabPane, NTabs, NTag, useMessage, NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NSpace, NAvatar } from 'naive-ui'
import { http } from '@/lib/http'

type TabKey = 'selling' | 'sold' | 'removed'

const router = useRouter()
const message = useMessage()
const activeTab = ref<TabKey>('selling')
const loading = ref(false)

const itemsByTab = reactive<Record<TabKey, any[]>>({
  selling: [],
  sold: [],
  removed: []
})

const fetchedTabs = reactive<Record<TabKey, boolean>>({
  selling: false,
  sold: false,
  removed: false
})

const statusMap: Record<TabKey, string> = {
  selling: 'available',
  sold: 'sold',
  removed: 'removed'
}

const categoryEmojiMap: Record<string, string> = {
  electronics: '📱',
  books: '📚',
  daily: '🛋️',
  sports: '⚽',
  fashion: '👕',
  beauty: '💄',
  other: '📦'
}

// Edit modal state
const editModalVisible = ref(false)
const editingItem = ref<any>(null)
const editForm = reactive({
  title: '',
  description: '',
  price: 0,
  condition: 'good'
})

const conditionOptions = [
  { label: '全新', value: 'new' },
  { label: '良好', value: 'good' },
  { label: '一般', value: 'fair' },
  { label: '较差', value: 'poor' }
]

const formatItems = (items: any[]) => {
  return items.map((item) => ({
    ...item,
    emoji: categoryEmojiMap[item.category] || '📦',
    views: item.view_count ?? 0,
    inquiries: item.inquiry_count ?? 0,
    price: Number(item.price) || 0
  }))
}

const loadItems = async (tabKey: TabKey, options: { force?: boolean } = {}) => {
  const force = options.force ?? false
  if (!force && fetchedTabs[tabKey]) {
    return
  }
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: 1,
      page_size: 50,
      status: statusMap[tabKey]
    }
    const response = await http.get('/items/my', { params })
    itemsByTab[tabKey] = formatItems(response.data.items)
    fetchedTabs[tabKey] = true
  } catch (error: any) {
    console.error('加载我的零件失败:', error)
    message.error(error.response?.data?.detail || '加载我的零件失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (value?: string) => {
  if (!value) return '-'
  return new Date(value).toLocaleDateString()
}

const refreshTab = async (tabKey: TabKey) => {
  fetchedTabs[tabKey] = false
  await loadItems(tabKey, { force: true })
}

const editItem = (item: any) => {
  editingItem.value = item
  editForm.title = item.title
  editForm.description = item.description || ''
  editForm.price = item.price
  editForm.condition = item.condition || 'good'
  editModalVisible.value = true
}

const saveEdit = async () => {
  if (!editingItem.value) return
  
  try {
    await http.put(`/items/${editingItem.value.id}`, {
      title: editForm.title,
      description: editForm.description,
      price: editForm.price,
      condition: editForm.condition
    })
    
    message.success('零件信息已更新')
    editModalVisible.value = false
    editingItem.value = null
    
    // Refresh the current tab
    await refreshTab(activeTab.value)
  } catch (error: any) {
    console.error('编辑失败:', error)
    message.error('编辑失败，请重试')
  }
}

const cancelEdit = () => {
  editModalVisible.value = false
  editingItem.value = null
}

const removeItem = async (item: any) => {
  try {
    await http.put(`/items/${item.id}`, { status: 'removed' })
    message.success('零件已下架')
    fetchedTabs.removed = false
    await refreshTab(activeTab.value)
  } catch (error: any) {
    console.error('下架失败:', error)
    message.error(error.response?.data?.detail || '下架失败')
  }
}

const restoreItem = async (item: any) => {
  try {
    await http.put(`/items/${item.id}`, { status: 'available' })
    message.success('零件已重新上架')
    fetchedTabs.selling = false
    await refreshTab(activeTab.value)
  } catch (error: any) {
    console.error('上架失败:', error)
    message.error(error.response?.data?.detail || '上架失败')
  }
}

const sellingItems = computed(() => itemsByTab.selling)
const soldItems = computed(() => itemsByTab.sold)
const removedItems = computed(() => itemsByTab.removed)

// 本地占位图列表
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
      // ignore
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

watch(activeTab, (tab) => {
  loadItems(tab)
})

onMounted(() => {
  loadItems('selling', { force: true })
})
</script>

<style scoped>
.n-tabs :deep(.n-tabs-tab-wrapper) {
  padding: 0 16px;
}

.n-tabs :deep(.n-tabs-tab__label) {
  font-weight: 900;
  text-transform: uppercase;
  font-style: italic;
  letter-spacing: 0.05em;
}

.n-tabs :deep(.n-tabs-bar) {
  height: 4px;
  background-color: #82b440 !important;
}
</style>
