<template>
  <div v-if="isVisible" class="ai-chatbox-container" :class="{ 'minimized': isMinimized }">
    <div class="chat-header">
      <div class="header-left">
        <span class="ai-icon">🛠️</span>
        <span class="header-title">凤凰汽配 AI 助手</span>
      </div>
      <div class="header-actions">
        <button @click="toggleMinimize" class="action-btn">
          {{ isMinimized ? '展开' : '最小化' }}
        </button>
        <button @click="closeChat" class="action-btn close-btn">✕</button>
      </div>
    </div>

    <div v-show="!isMinimized" class="chat-body">
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-message">
          <p class="welcome-title">🔧 凤凰汽配技术支持</p>
          <p class="welcome-subtitle">您好！我是您的智能汽配专家，随时为您提供技术支持：</p>
          <ul>
            <li>📊 <strong>零件分析</strong>：深度解析规格与适配性</li>
            <li>🛡️ <strong>交易保障</strong>：协助处理订单与冲突</li>
            <li>📈 <strong>市场建议</strong>：提供零件采购与库存建议</li>
            <li>💬 <strong>即时问答</strong>：解答任何关于平台的问题</li>
          </ul>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message', msg.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
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
          🔍 零件深度分析
        </button>
        <button @click="showConflictHelp" class="quick-btn">
          🛡️ 售后/冲突帮助
        </button>
      </div>

      <div class="input-area">
        <n-input
          v-model:value="userInput"
          type="textarea"
          placeholder="描述您的问题或零件需求..."
          :autosize="{ minRows: 1, maxRows: 4 }"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <button @click="sendMessage" :disabled="!userInput.trim() || isLoading" class="send-btn">
          {{ isLoading ? '...' : '发送' }}
        </button>
      </div>
    </div>
  </div>

  <button v-else @click="openChat" class="chat-toggle-btn">
    <span class="toggle-icon">🛠️</span>
    <span class="toggle-text">AI 助手</span>
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
    const token = localStorage.getItem('regionwap_token')
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
    content: '请帮我分析一下当前这个零件'
  })

  await scrollToBottom()

  try {
    const token = localStorage.getItem('regionwap_token')
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
    console.error('零件分析错误:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉,无法分析该零件,请稍后再试。'
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
2. **保留证据** - 截图聊天记录、零件照片等
3. **平台介入** - 如无法协商,可申请平台客服介入
4. **合理退款** - 根据实际情况协商退款方案

**常见冲突类型:**
- 零件描述不符
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
  background: #1a1a1a;
  border-radius: 16px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(163, 230, 53, 0.2);
  font-family: 'Inter', sans-serif;
}

.chat-header {
  padding: 16px 20px;
  background: #242424;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-icon {
  font-size: 20px;
}

.header-title {
  font-weight: 800;
  font-size: 14px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #a3e635;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.05);
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.close-btn:hover {
  background: #ef4444;
  color: white;
}

.chat-body {
  display: flex;
  flex-direction: column;
  height: 500px;
  background: #1a1a1a;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  text-align: center;
  padding: 20px;
  color: #888;
}

.welcome-title {
  font-size: 18px;
  font-weight: 900;
  color: #a3e635;
  margin-bottom: 8px;
}

.welcome-subtitle {
  font-size: 13px;
  margin-bottom: 20px;
  line-height: 1.6;
}

.welcome-message ul {
  text-align: left;
  list-style: none;
  padding: 0;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;
}

.welcome-message li {
  padding: 6px 0;
  font-size: 13px;
  color: #ccc;
}

.welcome-message li strong {
  color: #a3e635;
}

.message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease-out;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  background: #242424;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
}

.user-message .message-content {
  background: #a3e635;
  color: #0a0a0a;
  font-weight: 700;
}

.ai-message .message-content {
  background: #242424;
  color: #eee;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.quick-actions {
  display: flex;
  gap: 10px;
  padding: 12px 20px;
  background: #242424;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.quick-btn {
  flex: 1;
  padding: 10px;
  background: #1a1a1a;
  border: 1px solid rgba(163, 230, 53, 0.3);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #a3e635;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quick-btn:hover:not(:disabled) {
  background: #a3e635;
  color: #0a0a0a;
}

.input-area {
  display: flex;
  gap: 12px;
  padding: 20px;
  background: #242424;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.send-btn {
  padding: 0 20px;
  background: #a3e635;
  color: #0a0a0a;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 900;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #bef264;
  transform: translateY(-2px);
}

.chat-toggle-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  height: 48px;
  padding: 0 24px;
  border-radius: 24px;
  background: #1a1a1a;
  color: #a3e635;
  border: 2px solid #a3e635;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  z-index: 999;
  transition: all 0.3s;
}

.chat-toggle-btn:hover {
  background: #a3e635;
  color: #0a0a0a;
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(163, 230, 53, 0.4);
}

.toggle-icon {
  font-size: 20px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #a3e635;
  border-radius: 50%;
  animation: typing 1s infinite;
}

@keyframes typing {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
