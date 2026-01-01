<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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
import { http as api } from '@/lib/http'

const router = useRouter()
const message = useMessage()

interface SearchRecord {
  id: number
  keyword: string
  result_count: number
  searched_at: string
}

const searchHistory = ref<SearchRecord[]>([])
const loading = ref(false)
const deletingId = ref<number | null>(null)
const clearing = ref(false)

const hasRecords = computed(() => searchHistory.value.length > 0)

const searchAgain = (keyword: string) => {
  router.push({
    path: '/marketplace',
    query: { search: keyword },
  })
}

const deleteRecord = async (id: number) => {
  try {
    deletingId.value = id
    await api.delete(`/search/history/${id}`)
    const index = searchHistory.value.findIndex(r => r.id === id)
    if (index > -1) {
      searchHistory.value.splice(index, 1)
      message.success('已删除')
    }
  } catch (error) {
    message.error('删除失败')
  } finally {
    deletingId.value = null
  }
}

const clearAll = async () => {
  try {
    if (!hasRecords.value) {
      message.info('暂无可清空的历史记录')
      return
    }
    clearing.value = true
    await api.delete('/search/history')
    searchHistory.value = []
    message.success('已清空搜索历史')
  } catch (error) {
    message.error('清空失败')
  } finally {
    clearing.value = false
  }
}

const loadSearchHistory = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/search/history', {
      params: { page: 1, page_size: 50 },
    })
    searchHistory.value = (data?.history || []).map((item: any) => ({
      id: item.id,
      keyword: item.keyword,
      result_count: item.result_count ?? item.results_count ?? 0,
      searched_at: item.searched_at ?? item.created_at,
    }))
  } catch (error) {
    message.error('加载搜索历史失败')
  } finally {
    loading.value = false
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
        <n-popconfirm @positive-click="clearAll" :show-icon="hasRecords">
          <template #trigger>
            <n-button
              type="error"
              secondary
              :disabled="!hasRecords || loading"
              :loading="clearing"
            >清空全部</n-button>
          </template>
          确定要清空所有搜索历史吗？
        </n-popconfirm>
      </template>

      <n-empty v-if="!loading && searchHistory.length === 0" description="暂无搜索历史">
        <template #extra>
          <n-button @click="router.push('/marketplace')">去搜索零件</n-button>
        </template>
      </n-empty>

      <n-spin :show="loading">
        <n-list v-if="searchHistory.length > 0" hoverable clickable>
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
                找到 {{ record.result_count }} 个结果
              </span>
              <span style="color: #999">•</span>
              <n-time :time="new Date(record.searched_at)" type="relative" />
            </n-space>
          </div>

          <template #suffix>
            <n-space>
              <n-button size="small" @click="searchAgain(record.keyword)">
                再次搜索
              </n-button>
              <n-popconfirm @positive-click="deleteRecord(record.id)">
                <template #trigger>
                  <n-button
                    size="small"
                    type="error"
                    secondary
                    :loading="deletingId === record.id"
                  >删除</n-button>
                </template>
                确定删除此条记录吗？
              </n-popconfirm>
            </n-space>
          </template>
        </n-list-item>
        </n-list>
      </n-spin>
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
