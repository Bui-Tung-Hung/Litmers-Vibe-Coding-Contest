<template>
  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
    <div style="display: flex; align-items: center; gap: 16px;">
      <NButton v-if="isMobile" text @click="$emit('toggle-mobile-menu')">
        <template #icon>
          <NIcon :component="MenuOutline" :size="24" />
        </template>
      </NButton>
      <h2 style="margin: 0;">Litmer</h2>
    </div>

    <div style="display: flex; align-items: center; gap: 16px;">
      <!-- Notifications -->
      <NPopover trigger="click" placement="bottom-end">
        <template #trigger>
          <NBadge :value="notificationStore.unreadCount" :max="99">
            <NButton text>
              <template #icon>
                <NIcon :component="NotificationsOutline" :size="22" />
              </template>
            </NButton>
          </NBadge>
        </template>
        <div style="width: 360px; max-width: 90vw;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 style="margin: 0;">Notifications</h3>
            <NButton v-if="notificationStore.unreadCount > 0" text size="small" @click="handleMarkAllRead">
              Mark all read
            </NButton>
          </div>
          <NDivider style="margin: 8px 0;" />
          <div v-if="notificationStore.notifications.length === 0" style="padding: 24px; text-align: center; color: #999;">
            No notifications
          </div>
          <div v-else style="max-height: 400px; overflow-y: auto;">
            <div
              v-for="notification in notificationStore.notifications.slice(0, 10)"
              :key="notification.id"
              :style="{
                padding: '12px',
                cursor: 'pointer',
                backgroundColor: notification.is_read ? 'transparent' : '#f0f8ff',
                borderBottom: '1px solid #f0f0f0',
              }"
              @click="handleNotificationClick(notification)"
            >
              <div style="font-size: 14px;">{{ notification.content }}</div>
              <div style="font-size: 12px; color: #999; margin-top: 4px;">
                {{ formatRelative(notification.created_at) }}
              </div>
            </div>
          </div>
        </div>
      </NPopover>

      <!-- User Menu -->
      <NDropdown :options="userMenuOptions" @select="handleUserMenuSelect">
        <NButton text>
          <template #icon>
            <NAvatar round :size="32">
              {{ authStore.user?.name?.charAt(0).toUpperCase() || 'U' }}
            </NAvatar>
          </template>
        </NButton>
      </NDropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NIcon, NBadge, NPopover, NDivider, NDropdown, NAvatar, useMessage } from 'naive-ui'
import { NotificationsOutline, PersonOutline, LogOutOutline, MenuOutline } from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth'
import { useNotificationStore } from '../stores/notification'
import { formatRelative } from '../utils/date'

defineEmits(['toggle-mobile-menu'])

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const isMobile = computed(() => window.innerWidth < 768)

const userMenuOptions = [
  {
    label: 'Profile',
    key: 'profile',
    icon: () => h(NIcon, { component: PersonOutline }),
  },
  {
    label: 'Logout',
    key: 'logout',
    icon: () => h(NIcon, { component: LogOutOutline }),
  },
]

const handleUserMenuSelect = (key) => {
  if (key === 'profile') {
    router.push('/profile')
  } else if (key === 'logout') {
    authStore.logout()
    router.push('/login')
    message.success('Logged out successfully')
  }
}

const handleMarkAllRead = async () => {
  try {
    await notificationStore.markAllAsRead()
    message.success('All notifications marked as read')
  } catch (error) {
    message.error('Failed to mark notifications as read')
  }
}

const handleNotificationClick = async (notification) => {
  if (!notification.is_read) {
    await notificationStore.markAsRead(notification.id)
  }
}
</script>
