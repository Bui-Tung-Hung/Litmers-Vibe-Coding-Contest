<template>
  <div class="auth-container">
    <NCard title="Create Account" style="max-width: 400px; width: 100%;">
      <NForm ref="formRef" :model="formData" :rules="rules">
        <NFormItem path="name" label="Name">
          <NInput v-model:value="formData.name" placeholder="Enter your name" />
        </NFormItem>
        <NFormItem path="email" label="Email">
          <NInput v-model:value="formData.email" placeholder="Enter your email" />
        </NFormItem>
        <NFormItem path="password" label="Password">
          <NInput
            v-model:value="formData.password"
            type="password"
            show-password-on="click"
            placeholder="Min 6 characters"
          />
        </NFormItem>
        <NFormItem path="confirmPassword" label="Confirm Password">
          <NInput
            v-model:value="formData.confirmPassword"
            type="password"
            show-password-on="click"
            placeholder="Re-enter password"
            @keydown.enter="handleRegister"
          />
        </NFormItem>
        <NButton type="primary" block :loading="loading" @click="handleRegister">
          Register
        </NButton>
      </NForm>

      <NDivider>OR</NDivider>

      <NButton block secondary @click="handleGoogleSignup">
        <template #icon>
          <span style="font-size: 18px;">🔐</span>
        </template>
        Sign up with Google
      </NButton>

      <NDivider />

      <NButton text @click="$router.push('/login')">
        Already have an account? Login
      </NButton>
    </NCard>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NDivider, useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { validateEmail, validatePassword } from '../utils/validation'
import { authAPI } from '../api/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const formData = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const rules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { 
      validator: (rule, value) => {
        if (!validateEmail(value)) {
          return new Error('Invalid email format')
        }
        return true
      },
      trigger: 'blur'
    },
  ],
  password: [
    { required: true, message: 'Password is required', trigger: 'blur' },
    { 
      validator: (rule, value) => {
        if (!validatePassword(value)) {
          return new Error('Password must be at least 6 characters')
        }
        return true
      },
      trigger: 'blur'
    },
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    {
      validator: (rule, value) => {
        if (value !== formData.password) {
          return new Error('Passwords do not match')
        }
        return true
      },
      trigger: 'blur',
    },
  ],
}

const handleRegister = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await authStore.register({
      name: formData.name,
      email: formData.email,
      password: formData.password,
    })

    message.success('Registration successful! Welcome!')
    router.push('/')  // Redirect to dashboard after auto-login
  } catch (error) {
    if (error.response) {
      // API error
      message.error(error.response.data.detail || 'Registration failed')
    }
    // Form validation errors are automatically shown below each field by Naive UI
  } finally {
    loading.value = false
  }
}

const handleGoogleSignup = async () => {
  try {
    const response = await authAPI.googleLogin()
    window.location.href = response.data.auth_url
  } catch (error) {
    message.error('Failed to initiate Google signup')
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
