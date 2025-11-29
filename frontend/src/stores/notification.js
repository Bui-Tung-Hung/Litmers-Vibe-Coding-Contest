import { defineStore } from 'pinia'
import { notificationsAPI } from '../api/notifications'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [],
    unreadCount: 0,
    loading: false,
  }),
  
  actions: {
    async fetchNotifications() {
      try {
        this.loading = true
        const response = await notificationsAPI.getAll()
        this.notifications = Array.isArray(response.data) ? response.data : []
        this.unreadCount = this.notifications.filter(n => !n.is_read).length
      } catch (error) {
        this.notifications = []
        this.unreadCount = 0
        console.error('Failed to fetch notifications:', error)
      } finally {
        this.loading = false
      }
    },
    
    async markAsRead(id) {
      try {
        await notificationsAPI.markAsRead(id)
        const notification = this.notifications.find(n => n.id === id)
        if (notification) {
          notification.is_read = true
          this.unreadCount = Math.max(0, this.unreadCount - 1)
        }
      } catch (error) {
        throw error
      }
    },
    
    async markAllAsRead() {
      try {
        await notificationsAPI.markAllAsRead()
        this.notifications.forEach(n => n.is_read = true)
        this.unreadCount = 0
      } catch (error) {
        throw error
      }
    },
    
    // Polling for new notifications
    startPolling(interval = 30000) {
      this.fetchNotifications()
      this.pollingInterval = setInterval(() => {
        this.fetchNotifications()
      }, interval)
    },
    
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
      }
    },
  },
})
