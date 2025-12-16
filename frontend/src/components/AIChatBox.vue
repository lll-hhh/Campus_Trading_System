<template>
  <div v-if="isVisible" class="ai-chatbox-container">
    <div class="chat-header">
      <div class="header-left">
        <span class="ai-icon">🤖</span>
        <span class="header-title">AI 助手</span>
      </div>
      <div class="header-actions">
        <button @click="toggleMinimize" class="action-btn">
          {{ isMinimized ? '📖' : '➖' }}
        </button>
        <button @click="closeChat" class="action-btn close-btn">✕</button>
      </div>
    </div>

    <div v-show="!isMinimized" class="chat-body">
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-message">
          <p>👋 您好!我是AI助手,可以帮您:</p>
          <ul>
            <li>🔍 分析产品详情和价格</li>
            <li>⚖️ 解决交易冲突</li>
            <li>💡 提供购物建议</li>
            <li>❓ 回答各种问题</li>
          </ul>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message', msg.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-avatar">
            {{ msg.role === 'user' ? '��' : '🤖' }}
          </div>
          <div class="message-content">
            <div v-if="msg.role === 'assistant'" v-html="formatMessage(msg.content)"></div>
            <div v-else>{{ msg.content }}</div>
          </div>
        </div>

        <div v-if="isLoading" class="message ai-message">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="quick-actions">
        <button @click="analyzeCurrentItem" class="quick-btn" :disabled="!currentItemId">
          🔍 分析当前商品
        </button>
        <button @click="showConflictHelp" class="quick-btn">
          ⚖️ 冲突解决帮助
        </button>
      </div>

      <div class="input-area">
        <n-input
          v-model:value="userInput"
          type="textarea"
          placeholder="输入您的问题..."
          :autosize="{ minRows: 1, maxRows: 4 }"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <button @click="sendMessage" :disabled="!userInput.trim() || isLoading" class="send-btn">
          {{ isLoading ? '⏳' : '➤' }}
        </button>
      </div>
    </div>
  </div>

  <button v-else @click="openChat" class="chat-toggle-btn">
    💬
  </button>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { NInput } from 'naive-ui'
import { useRoute } from 'vue-router'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const isVisible = ref(false)
const isMinimized = ref(false)
const messages = ref<Message[]>([])
const userInput = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const route = useRoute()
const currentItemId = ref<string | null>(null)

watch(() => route.params.id, (newId) => {
  if (route.name === 'item-detail' && newId) {
    currentItemId.value = newId as string
  } else {
    currentItemId.value = null
  }
}, { immediate: true })

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (content: string) => {
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const userMessage = userInput.value.trim()
  messages.value.push({ role: 'user', content: userMessage })
  userInput.value = ''
  isLoading.value = true

  await scrollToBottom()

  try {
    const token = localStorage.getItem('campuswap_token')
    const response = await axios.post(
      '/api/v1/ai/chat',
      {
        messages: messages.value,
        context_type: currentItemId.value ? 'item_analysis' : 'general',
        context_data: currentItemId.value ? { item_id: currentItemId.value } : null
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (response.data.message) {
      messages.value.push({
        role: 'assistant',
        content: response.data.message
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: '抱歉,我遇到了一些问题,请稍后再试。'
      })
    }
  } catch (error) {
    console.error('AI聊天错误:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉,连接AI服务失败,请检查网络或稍后再试。'
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

const analyzeCurrentItem = async () => {
  if (!currentItemId.value) return

  isLoading.value = true
  messages.value.push({
    role: 'user',
    content: '请帮我分析一下当前这个商品'
  })

  await scrollToBottom()

  try {
    const token = localStorage.getItem('campuswap_token')
    const response = await axios.post(
      '/api/v1/ai/quick-actions/analyze-item',
      { item_id: parseInt(currentItemId.value) },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (response.data.analysis) {
      messages.value.push({
        role: 'assistant',
        content: response.data.analysis
      })
    }
  } catch (error) {
    console.error('商品分析错误:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉,无法分析该商品,请稍后再试。'
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

const showConflictHelp = () => {
  messages.value.push({
    role: 'user',
    content: '我需要关于交易冲突解决的帮助'
  })

  messages.value.push({
    role: 'assistant',
    content: `**交易冲突解决指南:**

1. **沟通优先** - 先与对方友好沟通,了解问题所在
2. **保留证据** - 截图聊天记录、商品照片等
3. **平台介入** - 如无法协商,可申请平台客服介入
4. **合理退款** - 根据实际情况协商退款方案

**常见冲突类型:**
- 商品描述不符
- 质量问题
- 物流延误
- 沟通误解

如需具体帮助,请描述您遇到的情况。`
  })

  scrollToBottom()
}

const openChat = () => {
  isVisible.value = true
  isMinimized.value = false
}

const closeChat = () => {
  isVisible.value = false
}

const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value
}

onMounted(() => {
  const savedState = localStorage.getItem('aiChatVisible')
  if (savedState === 'true') {
    isVisible.value = true
  }
})

watch(isVisible, (newVal) => {
  localStorage.setItem('aiChatVisible', newVal.toString())
})
</script>

<style scoped>
.ai-chatbox-container {
  position: fixed;
  bottom: 80px;
  right: 20px;
  width: 380px;
  max-height: 600px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px 12px 0 0;
  cursor: move;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 24px;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.8);
}

.chat-body {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.welcome-message {
  text-align: center;
  padding: 20px;
  color: #718096;
}

.welcome-message p {
  font-size: 16px;
  margin-bottom: 16px;
}

.welcome-message ul {
  text-align: left;
  list-style: none;
  padding: 0;
}

.welcome-message li {
  padding: 8px 0;
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  font-size: 32px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  font-size: 14px;
}

.user-message .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-message .message-content {
  background: #f7fafc;
  color: #2d3748;
  border: 1px solid #e2e8f0;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #a0aec0;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.quick-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #e2e8f0;
}

.quick-btn {
  flex: 1;
  padding: 8px 12px;
  background: white;
  border: 1px solid #cbd5e0;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover:not(:disabled) {
  background: #f7fafc;
  border-color: #667eea;
  color: #667eea;
}

.quick-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #e2e8f0;
  background: #fafafa;
}

.send-btn {
  padding: 0 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  transition: transform 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-toggle-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  font-size: 28px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  z-index: 999;
  transition: transform 0.2s;
}

.chat-toggle-btn:hover {
  transform: scale(1.1);
}
</style>
