import apiClient from './axios'

export const authAPI = {
  register(data) {
    return apiClient.post('/api/auth/register', data)
  },
  
  login(data) {
    return apiClient.post('/api/auth/login', data)
  },
  
  forgotPassword(data) {
    return apiClient.post('/api/auth/forgot-password', data)
  },
  
  resetPassword(data) {
    return apiClient.post('/api/auth/reset-password', data)
  },
  
  googleLogin() {
    return apiClient.get('/api/auth/google/login')
  },
}
