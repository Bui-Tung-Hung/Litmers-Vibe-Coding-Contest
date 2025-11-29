<template>
  <div class="auth-container">
    <NCard title="Reset Password" style="max-width: 400px; width: 100%;">
      <NForm ref="formRef" :model="formData" :rules="rules">
        <NFormItem path="newPassword" label="New Password">
          <NInput
            v-model:value="formData.newPassword"
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
            @keydown.enter="handleSubmit"
          />
        </NFormItem>
        <NButton type="primary" block :loading="loading" @click="handleSubmit">
          Reset Password
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
import { useRoute, useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NDivider, useMessage } from 'naive-ui'
import { authAPI } from '../api/auth'
import { validatePassword } from '../utils/validation'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const formRef = ref(null)
const loading = ref(false)

const formData = reactive({
  newPassword: '',
  confirmPassword: '',
})

const rules = {
  newPassword: [
    { required: true, message: 'Password is required', trigger: 'blur' },
    { validator: (rule, value) => validatePassword(value), message: 'Password must be at least 6 characters', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    {
      validator: (rule, value) => value === formData.newPassword,
      message: 'Passwords do not match',
      trigger: 'blur',
    },
  ],
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await authAPI.resetPassword({
      token: route.params.token,
      new_password: formData.newPassword,
    })

    message.success('Password reset successful!')
    router.push('/login')
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to reset password')
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
