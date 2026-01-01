<template>
  <div class="store-network-view p-4 max-w-7xl mx-auto">
    <n-h1 align="center" class="mb-8 text-primary">📍 Phoenix 凤凰汽配 门店网络</n-h1>
    
    <n-grid :cols="1" :x-gap="12" :y-gap="12" class="mt-4">
      <n-grid-item v-for="store in stores" :key="store.id">
        <n-card hoverable class="store-card border-l-4 border-primary">
          <div class="flex flex-col md:flex-row gap-6">
            <!-- 左侧：门店图片 -->
            <div class="w-full md:w-1/3 h-48 md:h-auto overflow-hidden rounded-lg">
              <img 
                :src="store.image_url || '/demo-images/store-placeholder.jpg'" 
                :alt="store.name"
                class="w-full h-full object-cover transition-transform duration-300 hover:scale-110"
              />
            </div>
            
            <!-- 右侧：门店信息 -->
            <div class="flex-1 flex flex-col justify-center">
              <n-h2 class="m-0 text-primary">{{ store.name }}</n-h2>
              <n-divider />
              <n-space vertical size="large">
                <div class="flex items-center gap-2 text-lg">
                  <span class="text-gray-400">📍 门店地址：</span>
                  <span>{{ store.address }}</span>
                </div>
                <div class="flex items-center gap-2 text-lg">
                  <span class="text-gray-400">📞 服务热线：</span>
                  <span>{{ store.phone || '暂无' }}</span>
                </div>
                <div class="mt-4 text-gray-600 italic">
                  {{ store.description }}
                </div>
              </n-space>
              
              <div class="mt-6 flex gap-4">
                <n-button type="primary" @click="handleViewMap(store)">
                  查看地图
                </n-button>
                <n-button type="primary" ghost @click="handleContact(store)">
                  联系门店
                </n-button>
              </div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-empty v-if="stores.length === 0" description="暂无门店信息" class="mt-20" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NH1, NH2, NGrid, NGridItem, NCard, NDivider, NSpace, NButton, NEmpty, useMessage } from 'naive-ui'
import axios from 'axios'

interface Store {
  id: number
  name: string
  address: string
  phone: string | null
  image_url: string | null
  description: string | null
  is_active: boolean
}

const stores = ref<Store[]>([])
const message = useMessage()

const fetchStores = async () => {
  try {
    const response = await axios.get('/api/v1/stores/')
    stores.value = response.data
  } catch (error) {
    console.error('获取门店信息失败:', error)
    message.error('获取门店信息失败，请稍后再试')
  }
}

const handleViewMap = (store: Store) => {
  message.info(`正在打开 ${store.name} 的地图位置...`)
}

const handleContact = (store: Store) => {
  if (store.phone) {
    message.success(`拨打电话: ${store.phone}`)
  } else {
    message.warning('该门店暂未提供联系电话')
  }
}

onMounted(() => {
  fetchStores()
})
</script>

<style scoped>
.store-card {
  transition: all 0.3s ease;
  border-radius: 12px;
}
.store-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}
</style>
