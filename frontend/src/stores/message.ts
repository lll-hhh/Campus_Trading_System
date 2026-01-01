import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { http } from '@/lib/http'
import { useAuthStore } from './auth'

export const useMessageStore = defineStore('message', () => {
  const authStore = useAuthStore()
  const totalUnread = ref(0)
  const pollingInterval = ref<number | null>(null)

  const fetchUnreadCount = async () => {
    if (!authStore.isAuthenticated) {
      totalUnread.value = 0
      return
    }
    try {
      const response = await http.get('/messages/conversations')
      // 后端返回的格式是 { conversations: [...], total: 10, total_unread: 5 }
      totalUnread.value = response.data.total_unread || 0
    } catch (error) {
      console.error('获取未读消息数失败:', error)
    }
  }

  const startPolling = () => {
    if (pollingInterval.value) return
    fetchUnreadCount()
    pollingInterval.value = window.setInterval(fetchUnreadCount, 30000) // 每30秒轮询一次
  }

  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
  }

  const setUnreadCount = (count: number) => {
    totalUnread.value = count
  }

  return {
    totalUnread,
    fetchUnreadCount,
    startPolling,
    stopPolling,
    setUnreadCount
  }
})
