<template>
  <div class="auth-container">
    <NCard title="Forgot Password" style="max-width: 400px; width: 100%;">
      <NAlert v-if="success" type="success" style="margin-bottom: 16px;">
        Password reset link has been sent to your email.
      </NAlert>

      <NForm ref="formRef" :model="formData" :rules="rules">
        <NFormItem path="email" label="Email">
          <NInput v-model:value="formData.email" placeholder="Enter your email" @keydown.enter="handleSubmit" />
        </NFormItem>
        <NButton type="primary" block :loading="loading" @click="handleSubmit">
          Send Reset Link
        </NButton>
      </NForm>

      <NDivider />

      <NButton text @click="$router.push('/login')">
        Back to Login
      </NButton>
    </NCard>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton, NDivider, NAlert, useMessage } from 'naive-ui'
import { authAPI } from '../api/auth'
import { validateEmail } from '../utils/validation'

const message = useMessage()
const formRef = ref(null)
const loading = ref(false)
const success = ref(false)

const formData = reactive({
  email: '',
})

const rules = {
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { validator: (rule, value) => validateEmail(value), message: 'Invalid email format', trigger: 'blur' },
  ],
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await authAPI.forgotPassword(formData)
    success.value = true
    message.success('Password reset link sent!')
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to send reset link')
  } finally {
    loading.value = false
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
