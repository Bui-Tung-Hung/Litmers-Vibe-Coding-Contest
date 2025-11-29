<template>
  <div class="callback-container">
    <NCard style="max-width: 400px; width: 100%; text-align: center;">
      <NSpin size="large" />
      <p style="margin-top: 16px;">Processing Google authentication...</p>
    </NCard>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NCard, NSpin, useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { setAuthToken } from '../api/axios'
import { usersAPI } from '../api/users'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const authStore = useAuthStore()

onMounted(async () => {
  const token = route.query.token

  if (!token) {
    message.error('Authentication failed: No token received')
    router.push('/login')
    return
  }

  try {
    // Set token in axios and localStorage
    setAuthToken(token)
    authStore.token = token

    // Fetch user info
    const response = await usersAPI.getMe()
    authStore.user = response.data

    message.success('Google authentication successful!')
    router.push('/')
  } catch (error) {
    message.error('Failed to authenticate with Google')
    setAuthToken(null)
    authStore.token = null
    authStore.user = null
    router.push('/login')
  }
})
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
