import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Notification {
  id: string
  type: string
  title: string
  content: string
  timestamp: string
  read: boolean
  link?: string
  data?: any
}

export const useNotificationStore = defineStore('notification', () => {
  // 状态
  const notifications = ref<Notification[]>([])
  
  // 计算属性
  const unreadCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
  })
  
  const unreadNotifications = computed(() => {
    return notifications.value.filter(n => !n.read)
  })
  
  // 方法
  const addNotification = (notification: Notification) => {
    // 检查是否已存在（避免重复）
    const exists = notifications.value.some(n => n.id === notification.id)
    if (exists) {
      return
    }
    
    // 添加到列表开头
    notifications.value.unshift(notification)
    
    // 限制通知数量（最多保留50条）
    if (notifications.value.length > 50) {
      notifications.value = notifications.value.slice(0, 50)
    }
    
    // 保存到本地存储
    saveToLocalStorage()
  }
  
  const markAsRead = (id: string) => {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
      saveToLocalStorage()
    }
  }
  
  const markAllAsRead = () => {
    notifications.value.forEach(n => {
      n.read = true
    })
    saveToLocalStorage()
  }
  
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
      saveToLocalStorage()
    }
  }
  
  const clearAll = () => {
    notifications.value = []
    saveToLocalStorage()
  }
  
  const clearRead = () => {
    notifications.value = notifications.value.filter(n => !n.read)
    saveToLocalStorage()
  }
  
  // 本地存储
  const saveToLocalStorage = () => {
    try {
      localStorage.setItem('notifications', JSON.stringify(notifications.value))
    } catch (error) {
      console.error('保存通知到本地存储失败:', error)
    }
  }
  
  const loadFromLocalStorage = () => {
    try {
      const stored = localStorage.getItem('notifications')
      if (stored) {
        notifications.value = JSON.parse(stored)
      }
    } catch (error) {
      console.error('从本地存储加载通知失败:', error)
    }
  }
  
  // 初始化时加载
  loadFromLocalStorage()
  
  return {
    notifications,
    unreadCount,
    unreadNotifications,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
    clearRead
  }
})
