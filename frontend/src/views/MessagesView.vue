<template>
  <div class="messages-view">
    <n-card>
      <template #header>
        <div class="messages-header">
          <n-space align="center" justify="space-between">
            <n-space align="center">
              <n-icon size="24" :component="ChatboxEllipses" />
              <h2 class="messages-title">消息中心</h2>
            </n-space>
            <n-space>
              <n-button @click="markAllAsRead" :disabled="unreadCount === 0">
                <template #icon>
                  <n-icon :component="CheckmarkDone" />
                </template>
                全部标记已读
              </n-button>
              <n-button @click="refreshMessages">
                <template #icon>
                  <n-icon :component="Refresh" />
                </template>
                刷新
              </n-button>
            </n-space>
          </n-space>
        </div>
      </template>

      <n-layout has-sider class="messages-layout">
        <!-- 左侧：会话列表 -->
        <n-layout-sider
          bordered
          :width="320"
          :native-scrollbar="false"
          class="conversation-list"
        >
          <n-input
            v-model:value="searchQuery"
            placeholder="搜索会话..."
            class="search-input"
          >
            <template #prefix>
              <n-icon :component="Search" />
            </template>
          </n-input>

          <n-scrollbar style="max-height: calc(100vh - 280px)">
            <n-list hoverable clickable>
              <n-list-item
                v-for="conversation in filteredConversations"
                :key="conversation.id"
                @click="selectConversation(conversation)"
                :class="{ 'active-conversation': selectedConversation?.id === conversation.id }"
              >
                <n-thing>
                  <template #avatar>
                    <n-badge :value="conversation.unreadCount" :max="99" :show="conversation.unreadCount > 0">
                      <n-avatar
                        round
                        :size="48"
                        :src="conversation.avatar"
                        :fallback-src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${conversation.username}`"
                      />
                    </n-badge>
                  </template>
                  <template #header>
                    <n-space align="center" justify="space-between">
                      <span :class="{ 'unread-text': conversation.unreadCount > 0 }">
                        {{ conversation.username }}
                      </span>
                      <n-time
                        :time="new Date(conversation.lastMessageTime)"
                        type="relative"
                        class="message-time"
                      />
                    </n-space>
                  </template>
                  <template #description>
                    <n-ellipsis :line-clamp="1" class="last-message">
                      {{ conversation.lastMessage }}
                    </n-ellipsis>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>

            <n-empty
              v-if="filteredConversations.length === 0"
              description="暂无会话"
              size="large"
              style="margin-top: 60px"
            >
              <template #icon>
                <n-icon :component="ChatboxEllipses" />
              </template>
            </n-empty>
          </n-scrollbar>
        </n-layout-sider>

        <!-- 右侧：聊天区域 -->
        <n-layout-content
          class="chat-area"
          :native-scrollbar="false"
        >
          <div v-if="selectedConversation" class="chat-container">
            <!-- 聊天头部 -->
            <div class="chat-header">
              <n-space align="center">
                <n-avatar
                  round
                  :size="40"
                  :src="selectedConversation.avatar"
                  :fallback-src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedConversation.username}`"
                />
                <div>
                  <div class="chat-username">{{ selectedConversation.username }}</div>
                  <div class="chat-status">
                    <n-tag :type="selectedConversation.online ? 'success' : 'default'" size="small">
                      {{ selectedConversation.online ? '在线' : '离线' }}
                    </n-tag>
                  </div>
                </div>
              </n-space>
            </div>

            <!-- 消息列表 -->
            <n-scrollbar ref="messageScrollbar" class="message-list">
              <div class="messages-container">
                <div
                  v-for="message in messages"
                  :key="message.id"
                  :class="['message-item', message.isSent ? 'sent' : 'received']"
                >
                  <n-avatar
                    v-if="!message.isSent"
                    round
                    :size="32"
                    :src="selectedConversation.avatar"
                    :fallback-src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedConversation.username}`"
                    class="message-avatar"
                  />
                  
                  <div class="message-content-wrapper">
                    <div :class="['message-bubble', message.isSent ? 'sent-bubble' : 'received-bubble']">
                      <!-- 文本消息 -->
                      <div v-if="message.type === 'text'" class="message-text">
                        {{ message.content }}
                      </div>
                      
                      <!-- 图片消息 -->
                      <n-image
                        v-else-if="message.type === 'image'"
                        :src="message.content"
                        :width="200"
                        object-fit="cover"
                        class="message-image"
                      />
                      
                      <!-- 商品卡片 -->
                      <div v-else-if="message.type === 'item'" class="message-item-card">
                        <n-card size="small" hoverable>
                          <template #cover>
                            <img :src="message.itemData.image" style="height: 120px; object-fit: cover" />
                          </template>
                          <n-ellipsis :line-clamp="1">{{ message.itemData.title }}</n-ellipsis>
                          <div class="item-price">¥{{ message.itemData.price }}</div>
                        </n-card>
                      </div>
                    </div>
                    
                    <div class="message-time">
                      <n-time :time="new Date(message.timestamp)" format="HH:mm" />
                    </div>
                  </div>
                  
                  <n-avatar
                    v-if="message.isSent"
                    round
                    :size="32"
                    :src="currentUserAvatar"
                    fallback-src="https://api.dicebear.com/7.x/avataaars/svg?seed=currentuser"
                    class="message-avatar"
                  />
                </div>
              </div>
            </n-scrollbar>

            <!-- 消息输入框 -->
            <div class="message-input-area">
              <n-space vertical :size="8" style="width: 100%">
                <n-space>
                  <n-button text @click="handleImageUpload">
                    <template #icon>
                      <n-icon :component="Image" />
                    </template>
                    图片
                  </n-button>
                  <n-button text>
                    <template #icon>
                      <n-icon :component="Happy" />
                    </template>
                    表情
                  </n-button>
                </n-space>
                
                <n-input
                  v-model:value="inputMessage"
                  type="textarea"
                  placeholder="输入消息... (按Enter发送，Shift+Enter换行)"
                  :autosize="{ minRows: 2, maxRows: 4 }"
                  @keydown.enter.exact.prevent="sendMessage"
                  @keydown.shift.enter.prevent="inputMessage += '\n'"
                />
                
                <n-space justify="end">
                  <n-button type="primary" @click="sendMessage" :disabled="!inputMessage.trim()">
                    <template #icon>
                      <n-icon :component="Send" />
                    </template>
                    发送
                  </n-button>
                </n-space>
              </n-space>
            </div>
          </div>

          <!-- 未选择会话时的提示 -->
          <n-empty
            v-else
            description="选择一个会话开始聊天"
            size="huge"
            class="empty-chat"
          >
            <template #icon>
              <n-icon :component="ChatboxEllipses" size="80" />
            </template>
          </n-empty>
        </n-layout-content>
      </n-layout>
    </n-card>

    <!-- 图片上传（隐藏） -->
    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleImageSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useMessage } from 'naive-ui';
import { 
  ChatboxEllipses, 
  Send, 
  Search, 
  Refresh, 
  CheckmarkDone,
  Image as ImageIcon,
  Happy
} from '@vicons/ionicons5';
import { useAuthStore } from '@/stores/auth';
import http from '@/lib/http';

interface Conversation {
  id: number;
  userId: number;
  username: string;
  avatar: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  online: boolean;
}

interface Message {
  id: number;
  content: string;
  timestamp: string;
  isSent: boolean;
  type: 'text' | 'image' | 'item';
  itemData?: {
    image: string;
    title: string;
    price: number;
  };
}

const message = useMessage();
const authStore = useAuthStore();

const searchQuery = ref('');
const conversations = ref<Conversation[]>([]);
const selectedConversation = ref<Conversation | null>(null);
const messages = ref<Message[]>([]);
const inputMessage = ref('');
const messageScrollbar = ref();
const imageInput = ref<HTMLInputElement>();
const currentUserAvatar = ref('');

// 未读消息总数
const unreadCount = computed(() => {
  return conversations.value.reduce((sum, conv) => sum + conv.unreadCount, 0);
});

// 过滤后的会话列表
const filteredConversations = computed(() => {
  if (!searchQuery.value) return conversations.value;
  
  return conversations.value.filter(conv =>
    conv.username.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

// 加载会话列表
const loadConversations = async () => {
  try {
    const response = await http.get('/api/v1/messages/conversations');
    conversations.value = response.data.map((conv: any) => ({
      id: conv.id,
      userId: conv.other_user_id,
      username: conv.other_user_name,
      avatar: conv.other_user_avatar || '',
      lastMessage: conv.last_message,
      lastMessageTime: conv.last_message_time,
      unreadCount: conv.unread_count || 0,
      online: conv.online || false
    }));
  } catch (error) {
    console.error('加载会话列表失败:', error);
    message.error('加载会话列表失败');
  }
};

// 加载消息历史
const loadMessages = async (conversationId: number) => {
  try {
    const response = await http.get(`/api/v1/messages/conversation/${conversationId}`);
    messages.value = response.data.map((msg: any) => ({
      id: msg.id,
      content: msg.content,
      timestamp: msg.created_at,
      isSent: msg.sender_id === authStore.user?.id,
      type: msg.message_type || 'text',
      itemData: msg.item_data
    }));
    
    // 滚动到底部
    await nextTick();
    scrollToBottom();
    
    // 标记消息为已读
    markConversationAsRead(conversationId);
  } catch (error) {
    console.error('加载消息失败:', error);
    message.error('加载消息失败');
  }
};

// 选择会话
const selectConversation = (conversation: Conversation) => {
  selectedConversation.value = conversation;
  loadMessages(conversation.id);
};

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !selectedConversation.value) return;
  
  try {
    const response = await http.post('/api/v1/messages/send', {
      receiver_id: selectedConversation.value.userId,
      content: inputMessage.value,
      message_type: 'text'
    });
    
    // 添加到消息列表
    messages.value.push({
      id: response.data.id,
      content: inputMessage.value,
      timestamp: new Date().toISOString(),
      isSent: true,
      type: 'text'
    });
    
    // 清空输入框
    inputMessage.value = '';
    
    // 滚动到底部
    await nextTick();
    scrollToBottom();
    
    // 更新会话列表中的最后消息
    const conv = conversations.value.find(c => c.id === selectedConversation.value!.id);
    if (conv) {
      conv.lastMessage = response.data.content;
      conv.lastMessageTime = new Date().toISOString();
    }
  } catch (error) {
    console.error('发送消息失败:', error);
    message.error('发送消息失败');
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messageScrollbar.value) {
    messageScrollbar.value.scrollTo({ top: 999999, behavior: 'smooth' });
  }
};

// 标记会话为已读
const markConversationAsRead = async (conversationId: number) => {
  try {
    await http.post(`/api/v1/messages/conversation/${conversationId}/read`);
    
    const conv = conversations.value.find(c => c.id === conversationId);
    if (conv) {
      conv.unreadCount = 0;
    }
  } catch (error) {
    console.error('标记已读失败:', error);
  }
};

// 标记全部已读
const markAllAsRead = async () => {
  try {
    await http.post('/api/v1/messages/read-all');
    conversations.value.forEach(conv => {
      conv.unreadCount = 0;
    });
    message.success('已全部标记为已读');
  } catch (error) {
    console.error('标记全部已读失败:', error);
    message.error('操作失败');
  }
};

// 刷新消息
const refreshMessages = () => {
  loadConversations();
  if (selectedConversation.value) {
    loadMessages(selectedConversation.value.id);
  }
};

// 处理图片上传
const handleImageUpload = () => {
  imageInput.value?.click();
};

const handleImageSelected = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  
  // TODO: 实现图片上传逻辑
  message.info('图片上传功能开发中...');
};

// 组件挂载时加载数据
onMounted(() => {
  loadConversations();
  currentUserAvatar.value = authStore.user?.avatar || '';
  
  // 定时刷新会话列表（每30秒）
  setInterval(() => {
    loadConversations();
  }, 30000);
});

// 监听选中的会话变化
watch(selectedConversation, (newVal) => {
  if (newVal) {
    loadMessages(newVal.id);
  }
});
</script>

<style scoped>
.messages-view {
  height: 100%;
  padding: 20px;
}

.messages-header {
  width: 100%;
}

.messages-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.messages-layout {
  height: calc(100vh - 200px);
}

.conversation-list {
  background: var(--n-color);
}

.search-input {
  margin: 16px;
  width: calc(100% - 32px);
}

.active-conversation {
  background: var(--n-item-color-active);
}

.unread-text {
  font-weight: 600;
  color: var(--n-text-color);
}

.message-time {
  font-size: 12px;
  color: var(--n-text-color-disabled);
}

.last-message {
  color: var(--n-text-color-disabled);
  font-size: 13px;
}

.chat-area {
  padding: 0;
  background: var(--n-color);
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color);
}

.chat-username {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.chat-status {
  font-size: 12px;
}

.message-list {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.messages-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.message-item.sent {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 60%;
}

.message-item.sent .message-content-wrapper {
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
}

.sent-bubble {
  background: var(--n-color-target);
  color: white;
}

.received-bubble {
  background: var(--n-color-hover);
  color: var(--n-text-color);
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-image {
  border-radius: 8px;
}

.message-item-card {
  width: 200px;
}

.item-price {
  color: var(--n-color-target);
  font-size: 16px;
  font-weight: 600;
  margin-top: 8px;
}

.message-input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--n-border-color);
  background: var(--n-color);
}

.empty-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
