<template>
  <div class="messages min-h-screen bg-gray-50">
    <div class="max-w-6xl mx-auto py-6 px-4">
      <div class="bg-white rounded-lg shadow-lg overflow-hidden" style="height: calc(100vh - 120px)">
        <div class="grid grid-cols-3 h-full">
          <!-- 左侧会话列表 -->
          <div class="border-r border-gray-200 flex flex-col">
            <div class="p-4 border-b border-gray-200 bg-gray-50">
              <h2 class="text-xl font-bold mb-3">💬 消息</h2>
              <n-input placeholder="搜索聊天记录..." clearable>
                <template #prefix>🔍</template>
              </n-input>
            </div>
            
            <div class="flex-1 overflow-y-auto">
              <div
                v-for="conv in conversations"
                :key="conv.id"
                :class="[
                  'p-4 border-b border-gray-100 cursor-pointer transition-colors',
                  activeConversation?.id === conv.id ? 'bg-blue-50' : 'hover:bg-gray-50'
                ]"
                @click="selectConversation(conv)"
              >
                <div class="flex items-start gap-3">
                  <n-avatar :size="48" :src="conv.avatar">
                    {{ conv.name[0] }}
                  </n-avatar>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-1">
                      <span class="font-bold">{{ conv.name }}</span>
                      <span class="text-xs text-gray-500">{{ conv.time }}</span>
                    </div>
                    <p class="text-sm text-gray-600 truncate">{{ conv.lastMessage }}</p>
                  </div>
                  <n-badge v-if="conv.unread" :value="conv.unread" />
                </div>
              </div>
            </div>
          </div>
          
          <!-- 右侧聊天区域 -->
          <div class="col-span-2 flex flex-col" v-if="activeConversation">
            <!-- 聊天头部 -->
            <div class="p-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <n-avatar :size="40" :src="activeConversation.avatar">
                  {{ activeConversation.name[0] }}
                </n-avatar>
                <div>
                  <div class="font-bold">{{ activeConversation.name }}</div>
                  <div class="text-xs text-gray-500">在线</div>
                </div>
              </div>
              <div class="flex gap-2">
                <n-button text>📞</n-button>
                <n-button text>🎥</n-button>
                <n-button text>ℹ️</n-button>
              </div>
            </div>
            
            <!-- 消息列表 -->
            <div class="flex-1 overflow-y-auto p-4 space-y-4">
              <div
                v-for="msg in messages"
                :key="msg.id"
                :class="[
                  'flex',
                  msg.isMine ? 'justify-end' : 'justify-start'
                ]"
              >
                <div :class="['max-w-md', msg.isMine ? 'order-2' : '']">
                  <div
                    :class="[
                      'rounded-2xl px-4 py-2 inline-block',
                      msg.isMine 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-200 text-gray-900'
                    ]"
                  >
                    <p v-if="msg.type === 'text'">{{ msg.content }}</p>
                    <img v-else-if="msg.type === 'image'" :src="msg.content" class="max-w-xs rounded" />
                    <div v-else-if="msg.type === 'item'" class="bg-white rounded-lg p-3 text-gray-900">
                      <div class="flex gap-3">
                        <div class="w-16 h-16 bg-gray-200 rounded"></div>
                        <div>
                          <p class="font-bold">iPhone 13 Pro</p>
                          <p class="text-red-500 font-bold">¥4999</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="text-xs text-gray-500 mt-1" :class="msg.isMine ? 'text-right' : ''">
                    {{ msg.time }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 输入区域 -->
            <div class="p-4 border-t border-gray-200 bg-gray-50">
              <div class="flex gap-2 mb-3">
                <n-button text title="表情">😊</n-button>
                <n-button text title="图片">🖼️</n-button>
                <n-button text title="文件">📎</n-button>
                <n-button text title="商品">🛍️</n-button>
              </div>
              <div class="flex gap-2">
                <n-input
                  v-model:value="messageInput"
                  type="textarea"
                  placeholder="输入消息..."
                  :rows="3"
                  @keyup.enter.exact="sendMessage"
                />
                <n-button type="primary" @click="sendMessage">发送</n-button>
              </div>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-else class="col-span-2 flex items-center justify-center text-gray-400">
            <div class="text-center">
              <span class="text-6xl block mb-4">💬</span>
              <p>选择一个会话开始聊天</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { NInput, NAvatar, NBadge, NButton, useMessage } from 'naive-ui';

const message = useMessage();

const conversations = ref([
  { id: 1, name: '张三', avatar: '', lastMessage: '这个还在吗？', time: '10:30', unread: 2 },
  { id: 2, name: '李四', avatar: '', lastMessage: '可以便宜点吗', time: '昨天', unread: 0 },
  { id: 3, name: '王五', avatar: '', lastMessage: '好的，明天见', time: '昨天', unread: 0 },
  { id: 4, name: '赵六', avatar: '', lastMessage: '[图片]', time: '2天前', unread: 1 },
]);

const activeConversation = ref<any>(null);

const messages = ref([
  { id: 1, type: 'text', content: '你好，请问这个商品还在吗？', isMine: false, time: '10:25' },
  { id: 2, type: 'text', content: '在的，9成新', isMine: true, time: '10:26' },
  { id: 3, type: 'item', content: '', isMine: true, time: '10:27' },
  { id: 4, type: 'text', content: '可以当面交易吗？', isMine: false, time: '10:28' },
  { id: 5, type: 'text', content: '可以的，明天下午3点图书馆门口可以吗？', isMine: true, time: '10:29' },
  { id: 6, type: 'text', content: '好的，明天见！', isMine: false, time: '10:30' },
]);

const messageInput = ref('');

const selectConversation = (conv: any) => {
  activeConversation.value = conv;
  conv.unread = 0;
};

const sendMessage = () => {
  if (!messageInput.value.trim()) return;
  
  messages.value.push({
    id: Date.now(),
    type: 'text',
    content: messageInput.value,
    isMine: true,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  });
  
  messageInput.value = '';
};
</script>
