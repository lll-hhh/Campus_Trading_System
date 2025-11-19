<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NList,
  NListItem,
  NSpace,
  NButton,
  NTag,
  NEmpty,
  NTime,
  NPopconfirm,
  useMessage,
} from 'naive-ui'
import api from '../lib/http'

const router = useRouter()
const message = useMessage()

interface SearchRecord {
  id: number
  keyword: string
  results_count: number
  created_at: string
}

const searchHistory = ref<SearchRecord[]>([
  {
    id: 1,
    keyword: 'iPhone',
    results_count: 25,
    created_at: '2024-11-19T10:30:00',
  },
  {
    id: 2,
    keyword: 'MacBook',
    results_count: 12,
    created_at: '2024-11-19T09:15:00',
  },
  {
    id: 3,
    keyword: '自行车',
    results_count: 8,
    created_at: '2024-11-18T16:20:00',
  },
])

const searchAgain = (keyword: string) => {
  router.push({
    path: '/marketplace',
    query: { search: keyword },
  })
}

const deleteRecord = async (id: number) => {
  try {
    // await api.delete(`/api/search-history/${id}`)
    const index = searchHistory.value.findIndex(r => r.id === id)
    if (index > -1) {
      searchHistory.value.splice(index, 1)
      message.success('已删除')
    }
  } catch (error) {
    message.error('删除失败')
  }
}

const clearAll = async () => {
  try {
    // await api.delete('/api/search-history')
    searchHistory.value = []
    message.success('已清空搜索历史')
  } catch (error) {
    message.error('清空失败')
  }
}

const loadSearchHistory = async () => {
  try {
    // const response = await api.get('/api/search-history')
    // searchHistory.value = response.data
  } catch (error) {
    message.error('加载搜索历史失败')
  }
}

onMounted(() => {
  loadSearchHistory()
})
</script>

<template>
  <div class="search-history-page">
    <n-card title="搜索历史">
      <template #header-extra>
        <n-popconfirm @positive-click="clearAll">
          <template #trigger>
            <n-button type="error" secondary>清空全部</n-button>
          </template>
          确定要清空所有搜索历史吗？
        </n-popconfirm>
      </template>

      <n-empty v-if="searchHistory.length === 0" description="暂无搜索历史">
        <template #extra>
          <n-button @click="router.push('/marketplace')">去搜索商品</n-button>
        </template>
      </n-empty>

      <n-list v-else hoverable clickable>
        <n-list-item v-for="record in searchHistory" :key="record.id">
          <template #prefix>
            <div style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: #f0f9ff; border-radius: 50%">
              🔍
            </div>
          </template>

          <div @click="searchAgain(record.keyword)" style="cursor: pointer; flex: 1">
            <div style="font-size: 16px; font-weight: 500; margin-bottom: 4px">
              {{ record.keyword }}
            </div>
            <n-space align="center" :size="12">
              <span style="font-size: 14px; color: #666">
                找到 {{ record.results_count }} 个结果
              </span>
              <span style="color: #999">•</span>
              <n-time :time="new Date(record.created_at)" type="relative" />
            </n-space>
          </div>

          <template #suffix>
            <n-space>
              <n-button size="small" @click="searchAgain(record.keyword)">
                再次搜索
              </n-button>
              <n-popconfirm @positive-click="deleteRecord(record.id)">
                <template #trigger>
                  <n-button size="small" type="error" secondary>删除</n-button>
                </template>
                确定删除此条记录吗？
              </n-popconfirm>
            </n-space>
          </template>
        </n-list-item>
      </n-list>
    </n-card>
  </div>
</template>

<style scoped>
.search-history-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}
</style>
