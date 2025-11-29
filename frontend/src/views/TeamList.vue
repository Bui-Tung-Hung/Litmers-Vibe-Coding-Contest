<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
      <NH1 style="margin: 0;">Teams</NH1>
      <NButton type="primary" @click="showCreateModal = true">
        Create Team
      </NButton>
    </div>

    <NSpin :show="loading">
      <div v-if="teamStore.teams.length > 0" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;">
        <NCard
          v-for="team in teamStore.teams"
          :key="team.id"
          hoverable
          style="cursor: pointer;"
          @click="$router.push(`/teams/${team.id}`)"
        >
          <h2 style="margin: 0 0 12px 0;">{{ team.name }}</h2>
          <div style="display: flex; gap: 16px; color: #999; font-size: 14px;">
            <span>{{ team.member_count || 0 }} members</span>
            <span>{{ team.project_count || 0 }} projects</span>
          </div>
          <div style="margin-top: 12px; font-size: 12px; color: #999;">
            Created {{ formatRelative(team.created_at) }}
          </div>
        </NCard>
      </div>
      <NEmpty v-else description="No teams yet">
        <template #extra>
          <NButton @click="showCreateModal = true">Create Your First Team</NButton>
        </template>
      </NEmpty>
    </NSpin>

    <!-- Create Team Modal -->
    <NModal v-model:show="showCreateModal" preset="card" title="Create Team" style="max-width: 500px;">
      <NForm ref="formRef" :model="formData" :rules="rules">
        <NFormItem path="name" label="Team Name">
          <NInput v-model:value="formData.name" placeholder="Enter team name" />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px;">
          <NButton @click="showCreateModal = false">Cancel</NButton>
          <NButton type="primary" :loading="creating" @click="handleCreate">Create</NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NH1, NCard, NButton, NSpin, NEmpty, NModal, NForm, NFormItem, NInput, useMessage } from 'naive-ui'
import { useTeamStore } from '../stores/team'
import { teamsAPI } from '../api/teams'
import { formatRelative } from '../utils/date'

const router = useRouter()
const message = useMessage()
const teamStore = useTeamStore()

const loading = ref(false)
const creating = ref(false)
const showCreateModal = ref(false)
const formRef = ref(null)

const formData = reactive({
  name: '',
})

const rules = {
  name: [{ required: true, message: 'Team name is required', trigger: 'blur' }],
}

onMounted(async () => {
  loading.value = true
  try {
    await teamStore.fetchTeams()
  } catch (error) {
    message.error('Failed to load teams')
  } finally {
    loading.value = false
  }
})

const handleCreate = async () => {
  try {
    await formRef.value?.validate()
    creating.value = true

    await teamsAPI.create(formData)
    message.success('Team created successfully')
    showCreateModal.value = false
    formData.name = ''
    await teamStore.fetchTeams()
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to create team')
  } finally {
    creating.value = false
  }
}
</script>
