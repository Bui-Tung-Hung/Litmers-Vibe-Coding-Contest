import { defineStore } from 'pinia'
import { authAPI } from '../api/auth'
import { usersAPI } from '../api/users'
import { setAuthToken } from '../api/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    loading: false,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
  },
  
  actions: {
    async login(credentials) {
      try {
        this.loading = true
        const response = await authAPI.login(credentials)
        this.token = response.data.access_token
        this.user = response.data.user
        setAuthToken(this.token)
        return response.data
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async register(data) {
      try {
        this.loading = true
        const response = await authAPI.register(data)
        // Backend returns token and user info, so auto-login after registration
        this.token = response.data.access_token
        this.user = response.data.user
        setAuthToken(this.token)
        return response.data
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchUser() {
      try {
        const response = await usersAPI.getMe()
        this.user = response.data
      } catch (error) {
        this.logout()
        throw error
      }
    },
    
    logout() {
      this.user = null
      this.token = null
      setAuthToken(null)
    },
  },
})
