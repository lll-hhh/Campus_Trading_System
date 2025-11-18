<template>
  <div class="my-items min-h-screen bg-gray-50">
    <div class="max-w-6xl mx-auto py-6 px-4">
      <div class="bg-white rounded-lg shadow p-6">
        <h1 class="text-2xl font-bold mb-6">📦 我的商品</h1>
        
        <!-- 标签页 -->
        <n-tabs v-model:value="activeTab" type="segment" animated>
          <n-tab-pane name="selling" tab="在售中">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
              <n-card v-for="item in sellingItems" :key="item.id" hoverable>
                <div class="flex gap-4">
                  <div class="w-24 h-24 bg-gradient-to-br from-blue-100 to-purple-100 rounded flex items-center justify-center flex-shrink-0">
                    <span class="text-4xl">{{ item.emoji }}</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h3 class="font-bold mb-1 truncate">{{ item.name }}</h3>
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
          </n-tab-pane>
          
          <n-tab-pane name="sold" tab="已售出">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
              <n-card v-for="item in soldItems" :key="item.id">
                <div class="flex gap-4">
                  <div class="w-24 h-24 bg-gray-200 rounded flex items-center justify-center flex-shrink-0">
                    <span class="text-4xl opacity-50">{{ item.emoji }}</span>
                  </div>
                  <div class="flex-1">
                    <h3 class="font-bold mb-1">{{ item.name }}</h3>
                    <p class="text-gray-500 mb-2">¥{{ item.price }}</p>
                    <n-tag type="success" size="small">已售出</n-tag>
                    <div class="text-sm text-gray-500 mt-2">
                      买家: {{ item.buyer }}
                    </div>
                  </div>
                </div>
              </n-card>
            </div>
          </n-tab-pane>
          
          <n-tab-pane name="removed" tab="已下架">
            <div class="text-center text-gray-400 py-12">
              <span class="text-6xl block mb-4">📭</span>
              <p>暂无下架商品</p>
            </div>
          </n-tab-pane>
        </n-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { NTabs, NTabPane, NCard, NButton, NTag, useMessage } from 'naive-ui';

const message = useMessage();
const activeTab = ref('selling');

const sellingItems = ref([
  { id: 1, name: 'iPhone 13 Pro', price: 4999, views: 234, inquiries: 12, emoji: '📱' },
  { id: 2, name: '山地自行车', price: 800, views: 156, inquiries: 8, emoji: '🚲' },
  { id: 3, name: '机械键盘', price: 450, views: 201, inquiries: 15, emoji: '⌨️' },
]);

const soldItems = ref([
  { id: 4, name: '高等数学教材', price: 25, buyer: '李四', emoji: '📚' },
  { id: 5, name: '小米台灯', price: 80, buyer: '王五', emoji: '💡' },
]);

const editItem = (item: any) => {
  message.info(`编辑: ${item.name}`);
};

const removeItem = (item: any) => {
  message.warning(`下架: ${item.name}`);
};
</script>
