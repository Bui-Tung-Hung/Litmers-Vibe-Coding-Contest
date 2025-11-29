<template>
  <NLayout has-sider style="min-height: 100vh;">
    <NLayoutSider
      v-if="!isMobile"
      bordered
      :collapsed="collapsed"
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
    >
      <AppSidebar :collapsed="collapsed" />
    </NLayoutSider>

    <NLayout>
      <NLayoutHeader bordered style="height: 64px; padding: 0 24px; display: flex; align-items: center;">
        <AppHeader @toggle-mobile-menu="showMobileMenu = !showMobileMenu" />
      </NLayoutHeader>

      <NLayoutContent style="padding: 32px; background: #f5f5f5;">
        <div style="max-width: 1600px; margin: 0 auto; width: 100%;">
          <router-view />
        </div>
      </NLayoutContent>
    </NLayout>

    <!-- Mobile Drawer -->
    <NDrawer v-model:show="showMobileMenu" :width="280" placement="left">
      <NDrawerContent title="Menu">
        <AppSidebar :collapsed="false" @navigate="showMobileMenu = false" />
      </NDrawerContent>
    </NDrawer>
  </NLayout>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NDrawer, NDrawerContent } from 'naive-ui'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import { useNotificationStore } from '../stores/notification'

const collapsed = ref(false)
const showMobileMenu = ref(false)
const isMobile = ref(window.innerWidth < 768)

const notificationStore = useNotificationStore()

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  notificationStore.startPolling()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  notificationStore.stopPolling()
})
</script>
