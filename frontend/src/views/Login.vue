<template>
  <div class="auth-container">
    <NCard title="Login to Litmer" style="max-width: 400px; width: 100%;">
      <NForm ref="formRef" :model="formData" :rules="rules">
        <NFormItem path="email" label="Email">
          <NInput v-model:value="formData.email" placeholder="Enter your email" @keydown.enter="handleLogin" />
        </NFormItem>
        <NFormItem path="password" label="Password">
          <NInput
            v-model:value="formData.password"
            type="password"
            show-password-on="click"
            placeholder="Enter your password"
            @keydown.enter="handleLogin"
          />
        </NFormItem>
        <NButton type="primary" block :loading="loading" @click="handleLogin">
          Login
        </NButton>
      </NForm>

      <NDivider>OR</NDivider>

      <NButton block secondary @click="handleGoogleLogin">
        <template #icon>
          <span style="font-size: 18px;">🔐</span>
        </template>
        Sign in with Google
      </NButton>

      <NDivider />

      <div style="display: flex; flex-direction: column; gap: 12px;">
        <NButton text @click="$router.push('/register')">
          Don't have an account? Register
        </NButton>
        <NButton text @click="$router.push('/forgot-password')">
          Forgot password?
        </NButton>
      </div>
    </NCard>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NDivider, useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { validateEmail, validateRequired } from '../utils/validation'
import { authAPI } from '../api/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const formData = reactive({
  email: '',
  password: '',
})

const rules = {
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { validator: (rule, value) => validateEmail(value), message: 'Invalid email format', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Password is required', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await authStore.login(formData)
    message.success('Login successful!')
    router.push('/')
  } catch (error) {
    if (error.response) {
      message.error(error.response.data.detail || 'Login failed')
    } else if (!error.response) {
      message.error('Please fill in all required fields correctly')
    }
  } finally {
    loading.value = false
  }
}

const handleGoogleLogin = async () => {
  try {
    const response = await authAPI.googleLogin()
    window.location.href = response.data.auth_url
  } catch (error) {
    message.error('Failed to initiate Google login')
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
