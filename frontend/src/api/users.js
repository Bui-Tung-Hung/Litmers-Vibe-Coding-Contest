import apiClient from './axios'

export const usersAPI = {
  getMe() {
    return apiClient.get('/api/users/me')
  },
  
  updateMe(data) {
    return apiClient.put('/api/users/me', data)
  },
  
  changePassword(data) {
    return apiClient.put('/api/users/me/password', data)
  },
  
  deleteAccount() {
    return apiClient.delete('/api/users/me')
  },
}
