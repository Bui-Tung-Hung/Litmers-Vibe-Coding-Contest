<template>
  <div>
    <NSpin :show="loading">
      <div v-if="team">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
          <NH1 style="margin: 0;">{{ team.name }}</NH1>
          <NSpace>
            <NButton v-if="canManageTeam" @click="showInviteModal = true">Invite Member</NButton>
            <NButton v-if="canManageTeam" @click="showEditModal = true">Edit Team</NButton>
          </NSpace>
        </div>

        <NTabs type="line" animated>
          <NTabPane name="projects" tab="Projects">
            <!-- Projects Section -->
            <div style="margin-bottom: 16px; display: flex; justify-content: flex-end;">
              <NButton type="primary" @click="showCreateProjectModal = true">
                <template #icon>✨</template>
                New Project
              </NButton>
            </div>
            <NCard style="margin-bottom: 24px;">
              <div v-if="projects.length > 0" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;">
                <NCard
                  v-for="project in projects"
                  :key="project.id"
                  hoverable
                  style="cursor: pointer; position: relative;"
                  @click="$router.push(`/projects/${project.id}`)"
                >
                  <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                      <h3 style="margin: 0 0 8px 0;">{{ project.name }}</h3>
                      <p style="color: #999; font-size: 14px; margin: 0;">
                        {{ project.description || 'No description' }}
                      </p>
                    </div>
                    <NSpace @click.stop>
                      <NButton
                        text
                        :type="project.is_favorite ? 'warning' : 'default'"
                        @click="handleToggleFavorite(project, $event)"
                      >
                        {{ project.is_favorite ? '★' : '☆' }}
                      </NButton>
                      <NDropdown :options="getProjectOptions(project)" @select="(key) => handleProjectAction(key, project, $event)">
                        <NButton text size="small">⋯</NButton>
                      </NDropdown>
                    </NSpace>
                  </div>
                </NCard>
              </div>
              <NEmpty v-else description="No projects yet" />
            </NCard>
          </NTabPane>

          <NTabPane name="members" tab="Members">
            <!-- Members Section -->
            <NCard>
              <NList>
                <NListItem v-for="member in members" :key="member.user_id">
                  <template #prefix>
                    <NAvatar round>{{ member.user_name?.charAt(0).toUpperCase() }}</NAvatar>
                  </template>
                  <div>
                    <div style="font-weight: 500;">{{ member.user_name }}</div>
                    <div style="font-size: 12px; color: #999;">{{ member.user_email }}</div>
                  </div>
                  <template #suffix>
                    <NSpace>
                      <NTag :type="getRoleType(member.role)">{{ member.role }}</NTag>
                      <NDropdown v-if="canManageMember(member)" :options="getMemberOptions(member)" @select="(key) => handleMemberAction(key, member)">
                        <NButton size="small" text>⋯</NButton>
                      </NDropdown>
                    </NSpace>
                  </template>
                </NListItem>
              </NList>
            </NCard>
          </NTabPane>

          <NTabPane name="activity" tab="Activity Log">
            <NCard>
              <NTimeline>
                <NTimelineItem
                  v-for="activity in activities"
                  :key="activity.id"
                  :type="getActivityType(activity.action)"
                  :title="formatActivityAction(activity)"
                  :time="formatDate(activity.created_at)"
                >
                  <template #icon>
                    <span style="font-size: 16px;">{{ getActivityIcon(activity.action) }}</span>
                  </template>
                  <div style="color: #666; font-size: 14px;">
                    <strong>{{ activity.user.name }}</strong> {{ formatActivityDescription(activity) }}
                  </div>
                </NTimelineItem>
              </NTimeline>
              <NEmpty v-if="activities.length === 0" description="No activity yet" />
              <div v-if="hasMoreActivities" style="text-align: center; margin-top: 16px;">
                <NButton @click="loadMoreActivities">Load More</NButton>
              </div>
            </NCard>
          </NTabPane>
        </NTabs>
      </div>
    </NSpin>

    <!-- Modals -->
    <NModal v-model:show="showEditModal" preset="card" title="Edit Team" style="max-width: 500px;">
      <NForm ref="editFormRef" :model="editData" :rules="rules">
        <NFormItem path="name" label="Team Name">
          <NInput v-model:value="editData.name" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showEditModal = false">Cancel</NButton>
          <NButton type="primary" @click="handleUpdate">Update</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal v-model:show="showInviteModal" preset="card" title="Invite Member" style="max-width: 500px;">
      <NForm ref="inviteFormRef" :model="inviteData" :rules="inviteRules">
        <NFormItem path="email" label="Email">
          <NInput v-model:value="inviteData.email" placeholder="member@example.com" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showInviteModal = false">Cancel</NButton>
          <NButton type="primary" @click="handleInvite">Send Invite</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal v-model:show="showCreateProjectModal" preset="card" title="Create Project" style="max-width: 500px;">
      <NForm ref="projectFormRef" :model="projectData" :rules="projectRules">
        <NFormItem path="name" label="Project Name">
          <NInput v-model:value="projectData.name" />
        </NFormItem>
        <NFormItem path="description" label="Description">
          <NInput v-model:value="projectData.description" type="textarea" :rows="3" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showCreateProjectModal = false">Cancel</NButton>
          <NButton type="primary" @click="handleCreateProject">Create</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NH1, NCard, NButton, NSpin, NSpace, NEmpty, NList, NListItem, NAvatar, NTag, NDropdown, NModal, NForm, NFormItem, NInput, NTabs, NTabPane, NTimeline, NTimelineItem, useMessage, useDialog } from 'naive-ui'
import { teamsAPI } from '../api/teams'
import { projectsAPI } from '../api/projects'
import { useAuthStore } from '../stores/auth'
import { validateEmail } from '../utils/validation'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const loading = ref(false)
const team = ref(null)
const members = ref([])
const projects = ref([])
const activities = ref([])
const activityOffset = ref(0)
const hasMoreActivities = ref(true)

const showEditModal = ref(false)
const showInviteModal = ref(false)
const showCreateProjectModal = ref(false)

const editFormRef = ref(null)
const inviteFormRef = ref(null)
const projectFormRef = ref(null)

const editData = reactive({ name: '' })
const inviteData = reactive({ email: '' })
const projectData = reactive({ name: '', description: '' })

const rules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
}

const inviteRules = {
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { validator: (rule, value) => validateEmail(value), message: 'Invalid email', trigger: 'blur' },
  ],
}

const projectRules = {
  name: [{ required: true, message: 'Project name is required', trigger: 'blur' }],
}

const currentUserRole = computed(() => {
  const member = members.value.find(m => m.user_id === authStore.user?.id)
  return member?.role || null
})

const canManageTeam = computed(() => ['OWNER', 'ADMIN'].includes(currentUserRole.value))

const canManageMember = (member) => {
  if (currentUserRole.value === 'OWNER') return member.role !== 'OWNER'
  if (currentUserRole.value === 'ADMIN') return member.role === 'MEMBER'
  return false
}

const getRoleType = (role) => {
  const types = { OWNER: 'error', ADMIN: 'warning', MEMBER: 'default' }
  return types[role] || 'default'
}

const getMemberOptions = (member) => {
  const options = []
  if (currentUserRole.value === 'OWNER' && member.role !== 'OWNER') {
    options.push({ label: 'Change Role', key: 'change-role' })
  }
  options.push({ label: 'Remove', key: 'remove' })
  return options
}

const getProjectOptions = (project) => {
  const options = []
  if (project.is_archived) {
    options.push({ label: 'Restore', key: 'restore' })
  } else {
    options.push({ label: 'Archive', key: 'archive' })
  }
  return options
}

const handleMemberAction = (action, member) => {
  if (action === 'remove') {
    dialog.warning({
      title: 'Remove Member',
      content: `Remove ${member.user_name} from team?`,
      positiveText: 'Remove',
      negativeText: 'Cancel',
      onPositiveClick: async () => {
        try {
          await teamsAPI.kickMember(team.value.id, member.user_id)
          message.success('Member removed')
          loadMembers()
        } catch (error) {
          message.error('Failed to remove member')
        }
      },
    })
  }
}

const handleProjectAction = (action, project, event) => {
  if (action === 'archive' || action === 'restore') {
    handleArchiveProject(project, event)
  }
}

const loadTeamData = async () => {
  loading.value = true
  try {
    const [teamRes, membersRes, projectsRes] = await Promise.all([
      teamsAPI.getById(route.params.teamId),
      teamsAPI.getMembers(route.params.teamId),
      projectsAPI.getAll(route.params.teamId),
    ])
    team.value = teamRes.data
    members.value = membersRes.data
    // Sort projects: favorites first, then by creation date
    projects.value = projectsRes.data.sort((a, b) => {
      if (a.is_favorite && !b.is_favorite) return -1
      if (!a.is_favorite && b.is_favorite) return 1
      return new Date(b.created_at) - new Date(a.created_at)
    })
    editData.name = team.value.name
  } catch (error) {
    message.error('Failed to load team')
    router.push('/teams')
  } finally {
    loading.value = false
  }
}

const loadMembers = async () => {
  const res = await teamsAPI.getMembers(route.params.teamId)
  members.value = res.data
}

const handleUpdate = async () => {
  try {
    await editFormRef.value?.validate()
    await teamsAPI.update(team.value.id, editData)
    message.success('Team updated')
    showEditModal.value = false
    loadTeamData()
  } catch (error) {
    message.error('Failed to update team')
  }
}

const handleInvite = async () => {
  try {
    await inviteFormRef.value?.validate()
    await teamsAPI.inviteMember(team.value.id, inviteData)
    message.success('Invitation sent')
    showInviteModal.value = false
    inviteData.email = ''
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to send invitation')
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

const getActivityIcon = (action) => {
  const icons = {
    MEMBER_JOINED: '👋',
    MEMBER_LEFT: '👋',
    MEMBER_KICKED: '🚫',
    ROLE_CHANGED: '🔄',
    PROJECT_CREATED: '✨',
    PROJECT_ARCHIVED: '📦',
    PROJECT_RESTORED: '📂',
    PROJECT_DELETED: '🗑️',
    TEAM_UPDATED: '✏️'
  }
  return icons[action] || '📌'
}

const getActivityType = (action) => {
  if (action === 'MEMBER_KICKED' || action === 'PROJECT_DELETED') return 'error'
  if (action === 'PROJECT_CREATED' || action === 'MEMBER_JOINED') return 'success'
  return 'info'
}

const formatActivityAction = (activity) => {
  const actions = {
    MEMBER_JOINED: 'Member Joined',
    MEMBER_LEFT: 'Member Left',
    MEMBER_KICKED: 'Member Kicked',
    ROLE_CHANGED: 'Role Changed',
    PROJECT_CREATED: 'Project Created',
    PROJECT_ARCHIVED: 'Project Archived',
    PROJECT_RESTORED: 'Project Restored',
    PROJECT_DELETED: 'Project Deleted',
    TEAM_UPDATED: 'Team Updated'
  }
  return actions[activity.action] || activity.action
}

const formatActivityDescription = (activity) => {
  try {
    switch (activity.action) {
      case 'MEMBER_JOINED':
        return `invited ${activity.target_name} to the team`
      case 'MEMBER_LEFT':
        return `left the team`
      case 'MEMBER_KICKED':
        return `removed ${activity.target_name} from the team`
      case 'ROLE_CHANGED': {
        const details = activity.details ? JSON.parse(activity.details) : {}
        return `changed ${activity.target_name}'s role from ${details.old_role} to ${details.new_role}`
      }
      case 'PROJECT_CREATED':
        return `created project "${activity.target_name}"`
      case 'PROJECT_ARCHIVED':
        return `archived project "${activity.target_name}"`
      case 'PROJECT_RESTORED':
        return `restored project "${activity.target_name}"`
      case 'PROJECT_DELETED':
        return `deleted project "${activity.target_name}"`
      case 'TEAM_UPDATED': {
        const details = activity.details ? JSON.parse(activity.details) : {}
        return `renamed team from "${details.old_name}" to "${details.new_name}"`
      }
      default:
        return activity.action
    }
  } catch (e) {
    return activity.action
  }
}

const loadMoreActivities = async () => {
  try {
    const res = await teamsAPI.getActivity(team.value.id, 20, activityOffset.value)
    if (res.data.length < 20) {
      hasMoreActivities.value = false
    }
    activities.value.push(...res.data)
    activityOffset.value += 20
  } catch (error) {
    message.error('Failed to load more activities')
  }
}

const handleCreateProject = async () => {
  try {
    await projectFormRef.value?.validate()
    await projectsAPI.create(team.value.id, projectData)
    message.success('Project created')
    showCreateProjectModal.value = false
    projectData.name = ''
    projectData.description = ''
    const res = await projectsAPI.getAll(team.value.id)
    projects.value = res.data
  } catch (error) {
    message.error('Failed to create project')
  }
}

const handleArchiveProject = async (project, event) => {
  event.stopPropagation()
  const action = project.is_archived ? 'restore' : 'archive'
  dialog.warning({
    title: `${action === 'archive' ? 'Archive' : 'Restore'} Project`,
    content: `Are you sure you want to ${action} "${project.name}"?`,
    positiveText: action === 'archive' ? 'Archive' : 'Restore',
    negativeText: 'Cancel',
    onPositiveClick: async () => {
      try {
        await projectsAPI.archive(project.id, { is_archived: !project.is_archived })
        message.success(`Project ${action}d successfully`)
        const res = await projectsAPI.getAll(team.value.id)
        projects.value = res.data
      } catch (error) {
        message.error(`Failed to ${action} project`)
      }
    }
  })
}

const handleToggleFavorite = async (project, event) => {
  event.stopPropagation()
  try {
    await projectsAPI.toggleFavorite(project.id)
    message.success(project.is_favorite ? 'Removed from favorites' : 'Added to favorites')
    const res = await projectsAPI.getAll(team.value.id)
    projects.value = res.data
  } catch (error) {
    message.error('Failed to update favorite status')
  }
}

onMounted(async () => {
  await loadTeamData()
  loadActivities()
})

const loadActivities = async () => {
  if (!team.value) return
  try {
    const res = await teamsAPI.getActivity(team.value.id, 20, 0)
    activities.value = res.data
    activityOffset.value = 20
    hasMoreActivities.value = res.data.length === 20
  } catch (error) {
    message.error('Failed to load activities')
  }
}
</script>
