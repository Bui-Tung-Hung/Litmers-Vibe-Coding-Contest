import apiClient from './axios'

export const notificationsAPI = {
  getAll() {
    return apiClient.get('/api/notifications')
  },
  
  markAsRead(id) {
    return apiClient.put(`/api/notifications/${id}/read`)
  },
  
  markAllAsRead() {
    return apiClient.put('/api/notifications/read-all')
  },
}
