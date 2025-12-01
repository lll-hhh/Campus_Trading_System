<template>
  <div class="my-items min-h-screen bg-gray-50">
    <div class="max-w-6xl mx-auto py-6 px-4">
      <div class="bg-white rounded-lg shadow p-6">
        <h1 class="text-2xl font-bold mb-6">📦 我的商品</h1>
        <n-spin :show="loading">
          <n-tabs v-model:value="activeTab" type="segment" animated>
            <n-tab-pane name="selling" tab="在售中">
              <div v-if="sellingItems.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                <n-card v-for="item in sellingItems" :key="item.id" hoverable>
                  <div class="flex gap-4">
                    <div class="w-24 h-24 bg-gradient-to-br from-blue-100 to-purple-100 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
                      <img
                        v-if="item.images?.length"
                        :src="item.images[0]"
                        :alt="item.title"
                        class="w-full h-full object-cover"
                      />
                      <span v-else class="text-4xl">{{ item.emoji }}</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="font-bold mb-1 truncate">{{ item.title }}</h3>
                      <p class="text-red-500 font-bold mb-2">¥{{ item.price }}</p>
                      <div class="text-sm text-gray-500 space-y-1">
                        <div>👁️ {{ item.views }} 浏览</div>
                        <div>💬 {{ item.inquiries }} 咨询</div>
                      </div>
                      <div class="flex gap-2 mt-3">
                        <n-button size="small" @click="editItem(item)">编辑</n-button>
                        <n-button size="small" type="error" @click="removeItem(item)">下架</n-button>
                      </div>
                    </div>
                  </div>
                </n-card>
              </div>
              <div v-else class="text-center text-gray-400 py-12">
                <span class="text-4xl block mb-2">🤔</span>
                <p>还没有在售商品，快去发布吧～</p>
              </div>
            </n-tab-pane>

            <n-tab-pane name="sold" tab="已售出">
              <div v-if="soldItems.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                <n-card v-for="item in soldItems" :key="item.id">
                  <div class="flex gap-4">
                    <div class="w-24 h-24 bg-gray-200 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
                      <img
                        v-if="item.images?.length"
                        :src="item.images[0]"
                        :alt="item.title"
                        class="w-full h-full object-cover opacity-80"
                      />
                      <span v-else class="text-4xl opacity-50">{{ item.emoji }}</span>
                    </div>
                    <div class="flex-1">
                      <h3 class="font-bold mb-1">{{ item.title }}</h3>
                      <p class="text-gray-500 mb-2">¥{{ item.price }}</p>
                      <n-tag type="success" size="small">已售出</n-tag>
                      <div class="text-sm text-gray-500 mt-2">
                        成交时间: {{ formatDate(item.updated_at || item.created_at) }}
                      </div>
                    </div>
                  </div>
                </n-card>
              </div>
              <div v-else class="text-center text-gray-400 py-12">
                <span class="text-4xl block mb-2">🕒</span>
                <p>还没有售出的商品</p>
              </div>
            </n-tab-pane>

            <n-tab-pane name="removed" tab="已下架">
              <div v-if="removedItems.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                <n-card v-for="item in removedItems" :key="item.id">
                  <div class="flex gap-4">
                    <div class="w-24 h-24 bg-gray-100 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
                      <img
                        v-if="item.images?.length"
                        :src="item.images[0]"
                        :alt="item.title"
                        class="w-full h-full object-cover grayscale"
                      />
                      <span v-else class="text-4xl opacity-40">{{ item.emoji }}</span>
                    </div>
                    <div class="flex-1">
                      <h3 class="font-bold mb-1">{{ item.title }}</h3>
                      <p class="text-gray-500 mb-2">¥{{ item.price }}</p>
                      <n-tag size="small">已下架</n-tag>
                      <div class="text-sm text-gray-500 mt-2">
                        下架时间: {{ formatDate(item.updated_at || item.created_at) }}
                      </div>
                    </div>
                  </div>
                </n-card>
              </div>
              <div v-else class="text-center text-gray-400 py-12">
                <span class="text-6xl block mb-4">📭</span>
                <p>暂无下架商品</p>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-spin>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { NButton, NCard, NSpin, NTabPane, NTabs, NTag, useMessage } from 'naive-ui'
import { http } from '@/lib/http'

type TabKey = 'selling' | 'sold' | 'removed'

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
  fashion: '👔',
  beauty: '💄',
  other: '📦'
}

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
    console.error('加载我的商品失败:', error)
    message.error(error.response?.data?.detail || '加载我的商品失败')
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
  message.info(`后续将支持编辑「${item.title}」`)
}

const removeItem = async (item: any) => {
  try {
    await http.put(`/items/${item.id}`, { status: 'removed' })
    message.success('商品已下架')
    fetchedTabs.removed = false
    await refreshTab(activeTab.value)
  } catch (error: any) {
    console.error('下架失败:', error)
    message.error(error.response?.data?.detail || '下架失败')
  }
}

const sellingItems = computed(() => itemsByTab.selling)
const soldItems = computed(() => itemsByTab.sold)
const removedItems = computed(() => itemsByTab.removed)

watch(activeTab, (tab) => {
  loadItems(tab)
})

onMounted(() => {
  loadItems('selling', { force: true })
})
</script>
