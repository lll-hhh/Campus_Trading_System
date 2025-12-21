<template>
  <div class="notification-center">
    <n-popover
      trigger="click"
      placement="bottom-end"
      :show="showPopover"
      @update:show="handlePopoverUpdate"
    >
      <template #trigger>
        <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0">
          <n-button circle quaternary size="large" @click="togglePopover">
            <template #icon>
              <n-icon size="24" :color="unreadCount > 0 ? '#18a058' : undefined">
                <NotificationsOutline />
              </n-icon>
            </template>
          </n-button>
        </n-badge>
      </template>

      <div class="notification-popover">
        <!-- 头部 -->
        <div class="popover-header">
          <n-space justify="space-between" align="center">
            <span class="title">通知中心</span>
            <n-space size="small">
              <n-button
                text
                size="small"
                @click="markAllAsRead"
                v-if="unreadCount > 0"
              >
                全部已读
              </n-button>
              <n-button text size="small" @click="clearAll" v-if="notifications.length > 0">
                清空
              </n-button>
            </n-space>
          </n-space>
        </div>

        <!-- 通知列表 -->
        <div class="notification-list" v-if="notifications.length > 0">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.read }"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-icon">
              <n-icon size="24" :color="getNotificationColor(notification.type)">
                <component :is="getNotificationIcon(notification.type)" />
              </n-icon>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.content }}</div>
              <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
            </div>
            <div class="notification-actions">
              <n-button
                text
                size="small"
                @click.stop="removeNotification(notification.id)"
              >
                <template #icon>
                  <n-icon><CloseOutline /></n-icon>
                </template>
              </n-button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <n-empty description="暂无通知" size="small">
            <template #icon>
              <n-icon size="48" color="#999">
                <NotificationsOffOutline />
              </n-icon>
            </template>
          </n-empty>
        </div>

        <!-- 底部 -->
        <div class="popover-footer" v-if="notifications.length > 5">
          <n-button text block @click="goToNotifications">
            查看全部通知
          </n-button>
        </div>
      </div>
    </n-popover>

    <!-- 桌面通知权限提示 -->
    <n-modal v-model:show="showPermissionModal" preset="dialog" title="开启通知">
      <div>是否允许接收桌面通知？这将帮助您及时获取重要消息。</div>
      <template #action>
        <n-space>
          <n-button @click="showPermissionModal = false">取消</n-button>
          <n-button type="primary" @click="requestNotificationPermission">
            允许
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  NotificationsOutline,
  NotificationsOffOutline,
  CloseOutline,
  MailOutline,
  CartOutline,
  ChatbubbleOutline,
  StarOutline,
  AlertCircleOutline,
  CheckmarkCircleOutline
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// 状态
const showPopover = ref(false)
const showPermissionModal = ref(false)
const notifications = computed(() => notificationStore.notifications)
const unreadCount = computed(() => notificationStore.unreadCount)

// WebSocket连接
let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let heartbeatTimer: ReturnType<typeof setTimeout> | null = null

// 方法
const togglePopover = () => {
  showPopover.value = !showPopover.value
}

const handlePopoverUpdate = (show: boolean) => {
  showPopover.value = show
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'new_message':
      return MailOutline
    case 'new_order':
      return CartOutline
    case 'order_update':
      return CheckmarkCircleOutline
    case 'new_comment':
      return ChatbubbleOutline
    case 'item_favorited':
      return StarOutline
    case 'system':
      return AlertCircleOutline
    default:
      return NotificationsOutline
  }
}

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'new_message':
      return '#18a058'
    case 'new_order':
      return '#2080f0'
    case 'order_update':
      return '#f0a020'
    case 'new_comment':
      return '#d03050'
    case 'item_favorited':
      return '#f0a020'
    case 'system':
      return '#666'
    default:
      return '#999'
  }
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}天前`
  } else {
    return date.toLocaleDateString()
  }
}

const handleNotificationClick = (notification: any) => {
  // 标记为已读
  notificationStore.markAsRead(notification.id)

  // 跳转到相关页面
  if (notification.link) {
    router.push(notification.link)
    showPopover.value = false
  }

  // 播放通知音效（可选）
  playNotificationSound()
}

const markAllAsRead = () => {
  notificationStore.markAllAsRead()
  message.success('已全部标记为已读')
}

const removeNotification = (id: string) => {
  notificationStore.removeNotification(id)
}

const clearAll = () => {
  notificationStore.clearAll()
  message.success('已清空所有通知')
}

const goToNotifications = () => {
  router.push('/notifications')
  showPopover.value = false
}

// WebSocket连接管理
const connectWebSocket = () => {
  if (!authStore.isAuthenticated) {
    return
  }

  const userId = authStore.user?.id
  if (!userId) {
    return
  }

  try {
    // 构建WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    ws = new WebSocket(`${protocol}//${host}/api/v1/ws/notifications/${userId}`)

    ws.onopen = () => {
      console.log('WebSocket连接成功')
      // 启动心跳
      startHeartbeat()
    }

    ws.onmessage = (event) => {
      try {
        const notification = JSON.parse(event.data)
        handleWebSocketMessage(notification)
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket连接关闭')
      stopHeartbeat()
      // 尝试重连
      scheduleReconnect()
    }
  } catch (error) {
    console.error('WebSocket连接失败:', error)
    scheduleReconnect()
  }
}

const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  stopHeartbeat()
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

const scheduleReconnect = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
  // 5秒后重连
  reconnectTimer = setTimeout(() => {
    console.log('尝试重新连接WebSocket...')
    connectWebSocket()
  }, 5000)
}

const startHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
  }
  // 每30秒发送一次心跳
  heartbeatTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000)
}

const stopHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

const handleWebSocketMessage = (notification: any) => {
  // 忽略系统消息
  if (notification.type === 'system' && notification.message === '连接成功') {
    return
  }

  if (notification.type === 'pong') {
    return
  }

  // 添加通知到store
  notificationStore.addNotification(notification)

  // 显示桌面通知
  showDesktopNotification(notification)

  // 播放通知音效
  playNotificationSound()

  // 显示消息提示
  if (notification.type !== 'system') {
    message.info(notification.title)
  }
}

// 桌面通知
const showDesktopNotification = (notification: any) => {
  if (!('Notification' in window)) {
    return
  }

  if (Notification.permission === 'granted') {
    new Notification(notification.title, {
      body: notification.content,
      icon: '/favicon.ico',
      tag: notification.id,
      requireInteraction: false
    })
  } else if (Notification.permission !== 'denied') {
    showPermissionModal.value = true
  }
}

const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    message.warning('您的浏览器不支持桌面通知')
    showPermissionModal.value = false
    return
  }

  try {
    const permission = await Notification.requestPermission()
    if (permission === 'granted') {
      message.success('已开启桌面通知')
    } else {
      message.warning('您拒绝了桌面通知权限')
    }
  } catch (error) {
    console.error('请求通知权限失败:', error)
  }
  
  showPermissionModal.value = false
}

// 播放通知音效
const playNotificationSound = () => {
  try {
    const audio = new Audio('/notification.mp3')
    audio.volume = 0.3
    audio.play().catch(e => {
      // 忽略自动播放被阻止的错误
    })
  } catch (error) {
    // 忽略音效播放失败
  }
}

// 生命周期
onMounted(() => {
  connectWebSocket()
  
  // 检查通知权限
  if ('Notification' in window && Notification.permission === 'default') {
    // 延迟3秒后提示
    setTimeout(() => {
      showPermissionModal.value = true
    }, 3000)
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-popover {
  width: 400px;
  max-height: 600px;
  display: flex;
  flex-direction: column;
}

.popover-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.popover-header .title {
  font-size: 16px;
  font-weight: 500;
}

.notification-list {
  max-height: 500px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.notification-item:hover {
  background: #f5f5f5;
}

.notification-item.unread {
  background: #f0f7ff;
}

.notification-item.unread:hover {
  background: #e6f2ff;
}

.notification-icon {
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
  color: #333;
}

.notification-message {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.notification-actions {
  flex-shrink: 0;
}

.empty-state {
  padding: 40px 16px;
  text-align: center;
}

.popover-footer {
  padding: 8px 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
