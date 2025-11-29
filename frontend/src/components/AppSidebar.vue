<template>
  <div style="padding: 24px 0;">
    <NMenu
      :collapsed="collapsed"
      :collapsed-width="64"
      :collapsed-icon-size="22"
      :options="menuOptions"
      :value="activeKey"
      @update:value="handleMenuSelect"
    />
  </div>
</template>

<script setup>
import { computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NMenu, NIcon } from 'naive-ui'
import { HomeOutline, PeopleOutline, FolderOutline, GridOutline } from '@vicons/ionicons5'

defineProps({
  collapsed: Boolean,
})

defineEmits(['navigate'])

const router = useRouter()
const route = useRoute()

const activeKey = computed(() => {
  if (route.path === '/') return 'dashboard'
  if (route.path.startsWith('/teams')) return 'teams'
  if (route.path.startsWith('/projects')) return 'projects'
  return route.name?.toLowerCase() || ''
})

const menuOptions = [
  {
    label: 'Dashboard',
    key: 'dashboard',
    icon: () => h(NIcon, { component: HomeOutline }),
  },
  {
    label: 'Teams',
    key: 'teams',
    icon: () => h(NIcon, { component: PeopleOutline }),
  },
]

const handleMenuSelect = (key) => {
  if (key === 'dashboard') {
    router.push('/')
  } else if (key === 'teams') {
    router.push('/teams')
  }
}
</script>
