<template>
  <div class="orders min-h-screen bg-gray-50">
    <div class="max-w-6xl mx-auto py-6 px-4">
      <div class="bg-white rounded-lg shadow p-6">
        <h1 class="text-2xl font-bold mb-6">📝 我的订单</h1>
        
        <!-- 标签页 -->
        <n-spin :show="loading">
          <n-tabs v-model:value="activeTab" type="segment" animated>
            <n-tab-pane name="buying" tab="我买到的">
              <n-timeline class="mt-6">
                <n-timeline-item
                  v-for="order in buyingOrders"
                  :key="order.id"
                  :type="order.status === 'completed' ? 'success' : 'info'"
                >
                  <template #header>
                    <div class="flex items-center justify-between">
                      <span class="font-bold">订单 #{{ order.id }}</span>
                      <n-tag :type="getStatusType(order.status)" size="small">
                        {{ getStatusText(order.status) }}
                      </n-tag>
                    </div>
                  </template>
                  
                  <n-card class="mt-2">
                    <div class="flex gap-4">
                      <div class="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded flex items-center justify-center">
                        <span class="text-3xl">{{ order.emoji }}</span>
                      </div>
                      <div class="flex-1">
                        <h3 class="font-bold mb-1">{{ order.itemName }}</h3>
                        <p class="text-gray-600 text-sm mb-2">卖家: {{ order.seller }}</p>
                        <div class="flex items-center justify-between">
                          <span class="text-red-500 font-bold">¥{{ order.price }}</span>
                          <div class="flex gap-2">
                            <n-button v-if="order.status === 'pending'" size="small" type="primary" @click="handleContactSeller(order)">
                              联系卖家
                            </n-button>
                            <n-button v-if="order.status === 'completed'" size="small">
                              评价
                            </n-button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </n-card>
                </n-timeline-item>
                
                <n-empty v-if="buyingOrders.length === 0" description="暂无购买记录">
                  <template #extra>
                    <n-button type="primary" @click="$router.push('/marketplace')">去逛逛</n-button>
                  </template>
                </n-empty>
              </n-timeline>
            </n-tab-pane>
            
            <n-tab-pane name="selling" tab="我卖出的">
              <n-timeline class="mt-6">
                <n-timeline-item
                  v-for="order in sellingOrders"
                  :key="order.id"
                  :type="order.status === 'completed' ? 'success' : 'warning'"
                >
                  <template #header>
                    <div class="flex items-center justify-between">
                      <span class="font-bold">订单 #{{ order.id }}</span>
                      <n-tag :type="getStatusType(order.status)" size="small">
                        {{ getStatusText(order.status) }}
                      </n-tag>
                    </div>
                  </template>
                  
                  <n-card class="mt-2">
                    <div class="flex gap-4">
                      <div class="w-20 h-20 bg-gradient-to-br from-green-100 to-blue-100 rounded flex items-center justify-center">
                        <span class="text-3xl">{{ order.emoji }}</span>
                      </div>
                      <div class="flex-1">
                        <h3 class="font-bold mb-1">{{ order.itemName }}</h3>
                        <p class="text-gray-600 text-sm mb-2">买家: {{ order.buyer }}</p>
                        <div class="flex items-center justify-between">
                          <span class="text-green-600 font-bold">+¥{{ order.price }}</span>
                          <div class="flex gap-2">
                            <n-button v-if="order.status === 'pending'" size="small" type="success" @click="handleConfirmTransaction(order)">
                              确认交易
                            </n-button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </n-card>
                </n-timeline-item>
                
                <n-empty v-if="sellingOrders.length === 0" description="暂无销售记录">
                  <template #extra>
                    <n-button type="primary" @click="$router.push('/publish')">发布商品</n-button>
                  </template>
                </n-empty>
              </n-timeline>
            </n-tab-pane>
          </n-tabs>
        </n-spin>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { NTabs, NTabPane, NTimeline, NTimelineItem, NCard, NButton, NTag, useMessage } from 'naive-ui';
import { http } from '@/lib/http'

const message = useMessage()
const activeTab = ref('buying');
const loading = ref(false)

interface OrderItem {
  id: number
  itemName: string
  seller: string
  buyer: string
  price: number
  status: string
  emoji: string
  created_at: string
}

const buyingOrders = ref<OrderItem[]>([])
const sellingOrders = ref<OrderItem[]>([])

const loadOrders = async () => {
  loading.value = true
  try {
    // 加载我买到的订单
    const buyingResponse = await http.get('/orders', { params: { role: 'buyer' } })
    buyingOrders.value = buyingResponse.data.orders.map((order: any) => ({
      id: order.id,
      itemName: order.item_info.item_title,
      seller: order.seller_name,
      price: order.item_info.item_price,
      status: order.status,
      emoji: '📦', // 可以根据商品类别设置不同的emoji
      created_at: order.created_at
    }))

    // 加载我卖出的订单
    const sellingResponse = await http.get('/orders', { params: { role: 'seller' } })
    sellingOrders.value = sellingResponse.data.orders.map((order: any) => ({
      id: order.id,
      itemName: order.item_info.item_title,
      buyer: order.buyer_name,
      price: order.item_info.item_price,
      status: order.status,
      emoji: '📦', // 可以根据商品类别设置不同的emoji
      created_at: order.created_at
    }))
  } catch (error: any) {
    console.error('加载订单失败:', error)
    message.error(error.response?.data?.detail || '加载订单失败')
  } finally {
    loading.value = false
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'warning',
    completed: 'success',
    cancelled: 'error'
  };
  return types[status] || 'default';
};

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  };
  return texts[status] || status;
};

const handleContactSeller = (order: OrderItem) => {
  // TODO: 跳转到消息页面联系卖家
  message.info('联系卖家功能开发中...')
}

const handleConfirmTransaction = async (order: OrderItem) => {
  try {
    await http.put(`/orders/${order.id}/status`, { status: 'completed' })
    message.success('交易已确认完成')
    loadOrders() // 重新加载数据
  } catch (error: any) {
    message.error(error.response?.data?.detail || '确认交易失败')
  }
}

onMounted(() => {
  loadOrders()
})
</script>
