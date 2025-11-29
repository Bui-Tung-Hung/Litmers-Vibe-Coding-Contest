<template>
  <div>
    <NH1>Profile</NH1>

    <NCard title="Profile Information" style="max-width: 600px;">
      <NForm ref="formRef" :model="formData" :rules="rules">
        <NFormItem path="name" label="Name">
          <NInput v-model:value="formData.name" placeholder="Your name" />
        </NFormItem>
        <NFormItem path="email" label="Email">
          <NInput v-model:value="formData.email" disabled />
        </NFormItem>
        <NButton type="primary" :loading="loading" @click="handleUpdateProfile">
          Update Profile
        </NButton>
      </NForm>
    </NCard>

    <NCard title="Change Password" style="max-width: 600px; margin-top: 24px;">
      <NForm ref="passwordFormRef" :model="passwordData" :rules="passwordRules">
        <NFormItem path="currentPassword" label="Current Password">
          <NInput v-model:value="passwordData.currentPassword" type="password" show-password-on="click" />
        </NFormItem>
        <NFormItem path="newPassword" label="New Password">
          <NInput v-model:value="passwordData.newPassword" type="password" show-password-on="click" />
        </NFormItem>
        <NFormItem path="confirmPassword" label="Confirm Password">
          <NInput v-model:value="passwordData.confirmPassword" type="password" show-password-on="click" />
        </NFormItem>
        <NButton type="primary" :loading="passwordLoading" @click="handleChangePassword">
          Change Password
        </NButton>
      </NForm>
    </NCard>

    <NCard title="Danger Zone" style="max-width: 600px; margin-top: 24px;">
      <NButton type="error" @click="showDeleteModal = true">
        Delete Account
      </NButton>
    </NCard>

    <NModal v-model:show="showDeleteModal" preset="dialog" title="Delete Account" positive-text="Delete" negative-text="Cancel" @positive-click="handleDeleteAccount">
      <p>Are you sure you want to delete your account? This action cannot be undone.</p>
    </NModal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NH1, NCard, NForm, NFormItem, NInput, NButton, NModal, useMessage } from 'naive-ui'
import { usersAPI } from '../api/users'
import { useAuthStore } from '../stores/auth'
import { validatePassword } from '../utils/validation'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const formRef = ref(null)
const passwordFormRef = ref(null)
const loading = ref(false)
const passwordLoading = ref(false)
const showDeleteModal = ref(false)

const formData = reactive({
  name: '',
  email: '',
})

const passwordData = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const rules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
}

const passwordRules = {
  currentPassword: [{ required: true, message: 'Current password is required', trigger: 'blur' }],
  newPassword: [
    { required: true, message: 'New password is required', trigger: 'blur' },
    { validator: (rule, value) => validatePassword(value), message: 'Password must be at least 6 characters', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    { validator: (rule, value) => value === passwordData.newPassword, message: 'Passwords do not match', trigger: 'blur' },
  ],
}

onMounted(async () => {
  if (authStore.user) {
    formData.name = authStore.user.name
    formData.email = authStore.user.email
  } else {
    await authStore.fetchUser()
    formData.name = authStore.user.name
    formData.email = authStore.user.email
  }
})

const handleUpdateProfile = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await usersAPI.updateMe({ name: formData.name })
    await authStore.fetchUser()
    message.success('Profile updated successfully')
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to update profile')
  } finally {
    loading.value = false
  }
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value?.validate()
    passwordLoading.value = true

    await usersAPI.changePassword({
      current_password: passwordData.currentPassword,
      new_password: passwordData.newPassword,
    })

    message.success('Password changed successfully')
    passwordData.currentPassword = ''
    passwordData.newPassword = ''
    passwordData.confirmPassword = ''
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to change password')
  } finally {
    passwordLoading.value = false
  }
}

const handleDeleteAccount = async () => {
  try {
    await usersAPI.deleteAccount()
    message.success('Account deleted')
    authStore.logout()
    router.push('/login')
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to delete account')
  }
}
</script>
