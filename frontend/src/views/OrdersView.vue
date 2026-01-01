<template>
  <div class="orders min-h-screen bg-slate-50 py-12">
    <div class="max-w-6xl mx-auto px-4">
      <div class="mb-10">
        <h1 class="text-4xl font-black tracking-tighter text-dark uppercase">订单管理 <span class="text-primary">Orders</span></h1>
        <p class="text-gray-400 text-[10px] font-bold uppercase tracking-[0.2em] mt-2">Track your procurement and sales history</p>
      </div>
      
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <!-- 标签页 -->
        <n-spin :show="loading">
          <n-tabs v-model:value="activeTab" type="line" animated class="p-8">
            <n-tab-pane name="buying" tab="采购订单 PROCUREMENT">
              <div class="space-y-6 mt-6">
                <div
                  v-for="order in buyingOrders"
                  :key="order.id"
                  class="group bg-white rounded-xl border border-gray-100 p-6 hover:shadow-xl hover:shadow-primary/5 transition-all flex flex-col md:flex-row gap-6 items-center"
                >
                  <div class="w-24 h-24 bg-gray-50 rounded-xl flex items-center justify-center text-4xl group-hover:scale-110 transition-transform">
                    {{ order.emoji }}
                  </div>
                  <div class="flex-1 text-center md:text-left">
                    <div class="flex items-center justify-center md:justify-start gap-3 mb-2">
                      <span class="text-[10px] font-black uppercase tracking-widest text-gray-400">Order #{{ order.id }}</span>
                      <n-tag :type="getStatusType(order.status)" size="small" round class="uppercase text-[10px] font-black tracking-widest">
                        {{ getStatusText(order.status) }}
                      </n-tag>
                    </div>
                    <h3 class="text-xl font-black tracking-tighter text-dark mb-1">{{ order.itemName }}</h3>
                    <p class="text-gray-400 text-[10px] font-bold uppercase tracking-widest">供应商: {{ order.seller }} | {{ formatDate(order.created_at) }}</p>
                  </div>
                  <div class="flex flex-col items-center md:items-end gap-2">
                    <span class="text-2xl font-black tracking-tighter text-dark">¥{{ order.price }}</span>
                    <div class="flex gap-2">
                      <n-button v-if="order.status === 'pending'" size="small" strong round type="primary" class="uppercase text-[10px] tracking-widest font-black" @click="handleContactSeller(order)">
                        联系商户
                      </n-button>
                      <n-button v-if="order.status === 'completed'" size="small" strong round class="uppercase text-[10px] tracking-widest font-black">
                        评价零件
                      </n-button>
                    </div>
                  </div>
                </div>
                
                <n-empty v-if="buyingOrders.length === 0" description="暂无采购记录">
                  <template #extra>
                    <n-button type="primary" strong round @click="$router.push('/marketplace')">前往零件市场</n-button>
                  </template>
                </n-empty>
              </div>
            </n-tab-pane>
            
            <n-tab-pane name="selling" tab="销售订单 SALES">
              <div class="space-y-6 mt-6">
                <div
                  v-for="order in sellingOrders"
                  :key="order.id"
                  class="group bg-white rounded-xl border border-gray-100 p-6 hover:shadow-xl hover:shadow-primary/5 transition-all flex flex-col md:flex-row gap-6 items-center"
                >
                  <div class="w-24 h-24 bg-gray-50 rounded-xl flex items-center justify-center text-4xl group-hover:scale-110 transition-transform">
                    {{ order.emoji }}
                  </div>
                  <div class="flex-1 text-center md:text-left">
                    <div class="flex items-center justify-center md:justify-start gap-3 mb-2">
                      <span class="text-[10px] font-black uppercase tracking-widest text-gray-400">Order #{{ order.id }}</span>
                      <n-tag :type="getStatusType(order.status)" size="small" round class="uppercase text-[10px] font-black tracking-widest">
                        {{ getStatusText(order.status) }}
                      </n-tag>
                    </div>
                    <h3 class="text-xl font-black tracking-tighter text-dark mb-1">{{ order.itemName }}</h3>
                    <p class="text-gray-400 text-[10px] font-bold uppercase tracking-widest">采购商: {{ order.buyer }} | {{ formatDate(order.created_at) }}</p>
                  </div>
                  <div class="flex flex-col items-center md:items-end gap-2">
                    <span class="text-2xl font-black tracking-tighter text-primary">+¥{{ order.price }}</span>
                    <div class="flex gap-2">
                      <n-button v-if="order.status === 'pending'" size="small" strong round type="primary" class="uppercase text-[10px] tracking-widest font-black" @click="handleConfirmTransaction(order)">
                        确认发货
                      </n-button>
                    </div>
                  </div>
                </div>
                
                <n-empty v-if="sellingOrders.length === 0" description="暂无销售记录">
                  <template #extra>
                    <n-button type="primary" strong round @click="$router.push('/marketplace')">发布零件供应</n-button>
                  </template>
                </n-empty>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-spin>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { NTabs, NTabPane, NTimeline, NTimelineItem, NCard, NButton, NTag, useMessage } from 'naive-ui';
import { http } from '@/lib/http'

const router = useRouter()
const message = useMessage()
const activeTab = ref('buying');
const loading = ref(false)

interface OrderItem {
  id: number
  itemName: string
  seller: string
  seller_id?: number
  buyer: string
  buyer_id?: number
  price: number
  status: string
  emoji: string
  created_at: string
  item_id?: number
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
      itemName: order.item_info?.item_title || '零件',
      seller: order.seller_name,
      seller_id: order.seller_id,
      item_id: order.item_id,
      price: order.item_info?.item_price || order.total_amount,
      status: order.status,
      emoji: '📦',
      created_at: order.created_at
    }))

    // 加载我卖出的订单
    const sellingResponse = await http.get('/orders', { params: { role: 'seller' } })
    sellingOrders.value = sellingResponse.data.orders.map((order: any) => ({
      id: order.id,
      itemName: order.item_info?.item_title || '零件',
      buyer: order.buyer_name,
      buyer_id: order.buyer_id,
      item_id: order.item_id,
      price: order.item_info?.item_price || order.total_amount,
      status: order.status,
      emoji: '📦',
      created_at: order.created_at
    }))
  } catch (error: any) {
    console.error('加载订单失败:', error)
    message.error(error.response?.data?.detail || '加载订单失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
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
  // 跳转到消息页面与卖家对话
  const sellerId = order.seller_id
  if (sellerId) {
    router.push({
      path: '/messages',
      query: { 
        userId: sellerId.toString(),
        itemId: order.item_id?.toString(),
        orderId: order.id.toString()
      }
    })
  } else {
    message.warning('无法获取卖家信息')
  }
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
