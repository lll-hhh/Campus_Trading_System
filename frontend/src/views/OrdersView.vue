<template>
  <div class="orders min-h-screen bg-gray-50">
    <div class="max-w-6xl mx-auto py-6 px-4">
      <div class="bg-white rounded-lg shadow p-6">
        <h1 class="text-2xl font-bold mb-6">📝 我的订单</h1>
        
        <!-- 标签页 -->
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
                          <n-button v-if="order.status === 'pending'" size="small" type="primary">
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
                          <n-button v-if="order.status === 'pending'" size="small" type="success">
                            确认交易
                          </n-button>
                        </div>
                      </div>
                    </div>
                  </div>
                </n-card>
              </n-timeline-item>
            </n-timeline>
          </n-tab-pane>
        </n-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { NTabs, NTabPane, NTimeline, NTimelineItem, NCard, NButton, NTag } from 'naive-ui';

const activeTab = ref('buying');

const buyingOrders = ref([
  { id: 1001, itemName: '电竞显示器', seller: '赵六', price: 1200, status: 'pending', emoji: '🖥️' },
  { id: 1002, itemName: '羽毛球拍', seller: '钱七', price: 380, status: 'completed', emoji: '🏸' },
]);

const sellingOrders = ref([
  { id: 2001, itemName: '高等数学教材', buyer: '李四', price: 25, status: 'completed', emoji: '📚' },
  { id: 2002, itemName: '小米台灯', buyer: '王五', price: 80, status: 'pending', emoji: '💡' },
]);

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
</script>
