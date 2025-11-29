<template>
  <div>
    <NSpin :show="loading">
      <div v-if="project">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
          <div>
            <NH1 style="margin: 0;">{{ project.name }}</NH1>
            <p style="color: #999; margin: 8px 0 0 0;">{{ project.description }}</p>
          </div>
          <NButton type="primary" @click="showCreateIssueModal = true">Create Issue</NButton>
        </div>

        <!-- Filters -->
        <NCard style="margin-bottom: 16px;">
          <NSpace>
            <NInput v-model:value="searchQuery" placeholder="Search issues..." clearable style="width: 250px;" />
            <NSelect
              v-model:value="filterAssignee"
              placeholder="Assignee"
              clearable
              filterable
              :options="assigneeOptions"
              style="width: 150px;"
            />
            <NSelect
              v-model:value="filterPriority"
              placeholder="Priority"
              clearable
              :options="priorityOptions"
              style="width: 120px;"
            />
          </NSpace>
        </NCard>

        <!-- Kanban Board -->
        <div style="display: flex; gap: 16px; overflow-x: auto; padding-bottom: 24px;">
          <div v-for="status in statuses" :key="status" style="min-width: 320px; flex: 1;">
            <NCard :title="status" size="small">
              <template #header-extra>
                <NTag size="small">{{ getIssuesByStatus(status).length }}</NTag>
              </template>
              
              <draggable
                :list="getIssuesByStatus(status)"
                group="issues"
                item-key="id"
                :animation="200"
                @end="handleDragEnd"
                style="min-height: 400px;"
              >
                <template #item="{ element: issue }">
                  <NCard
                    size="small"
                    hoverable
                    style="margin-bottom: 12px; cursor: pointer;"
                    @click="goToIssue(issue.id)"
                  >
                    <div>
                      <div style="font-weight: 500; margin-bottom: 8px;">{{ issue.title }}</div>
                      
                      <NSpace size="small" style="margin-bottom: 8px;">
                        <NTag v-if="issue.priority" :type="getPriorityType(issue.priority)" size="small">
                          {{ issue.priority }}
                        </NTag>
                        <NTag v-for="label in issue.labels || []" :key="label.id" size="small" :color="{ color: label.color }">
                          {{ label.name }}
                        </NTag>
                      </NSpace>

                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div v-if="issue.assignee_name" style="display: flex; align-items: center; gap: 4px;">
                          <NAvatar :size="20" round>{{ issue.assignee_name?.charAt(0).toUpperCase() }}</NAvatar>
                          <span style="font-size: 12px;">{{ issue.assignee_name }}</span>
                        </div>
                        <div v-if="issue.due_date" :style="{ fontSize: '12px', color: isDueSoon(issue.due_date) ? '#f00' : '#999' }">
                          {{ formatDate(issue.due_date) }}
                        </div>
                      </div>
                    </div>
                  </NCard>
                </template>
              </draggable>
            </NCard>
          </div>
        </div>
      </div>
    </NSpin>

    <!-- Create Issue Modal -->
    <NModal v-model:show="showCreateIssueModal" preset="card" title="Create Issue" style="max-width: 600px;">
      <NForm ref="formRef" :model="formData" :rules="rules">
        <NFormItem path="title" label="Title">
          <NInput v-model:value="formData.title" placeholder="Issue title" />
        </NFormItem>
        <NFormItem path="description" label="Description">
          <NInput v-model:value="formData.description" type="textarea" :rows="4" placeholder="Describe the issue..." />
        </NFormItem>
        <NFormItem path="priority" label="Priority">
          <NSelect v-model:value="formData.priority" :options="priorityOptions" />
        </NFormItem>
        <NFormItem path="assignee_id" label="Assignee">
          <NSelect v-model:value="formData.assignee_id" :options="assigneeOptions" clearable filterable />
        </NFormItem>
        <NFormItem path="due_date" label="Due Date">
          <NDatePicker v-model:value="formData.due_date" type="date" style="width: 100%;" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showCreateIssueModal = false">Cancel</NButton>
          <NButton type="primary" :loading="creating" @click="handleCreateIssue">Create</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NH1, NCard, NButton, NSpin, NSpace, NInput, NSelect, NTag, NAvatar, NModal, NForm, NFormItem, NDatePicker, useMessage } from 'naive-ui'
import draggable from 'vuedraggable'
import { projectsAPI } from '../api/projects'
import { issuesAPI } from '../api/issues'
import { teamsAPI } from '../api/teams'
import { formatDate, isDueSoon } from '../utils/date'
import { PRIORITIES, DEFAULT_STATUSES } from '../utils/constants'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const loading = ref(false)
const creating = ref(false)
const project = ref(null)
const issues = ref([])
const members = ref([])

const searchQuery = ref('')
const filterAssignee = ref(null)
const filterPriority = ref(null)

const showCreateIssueModal = ref(false)
const formRef = ref(null)

const formData = reactive({
  title: '',
  description: '',
  priority: 'MEDIUM',
  assignee_id: null,
  due_date: null,
})

const rules = {
  title: [{ required: true, message: 'Title is required', trigger: 'blur' }],
}

const statuses = DEFAULT_STATUSES

const priorityOptions = Object.values(PRIORITIES).map(p => ({ label: p.label, value: p.value }))

const assigneeOptions = computed(() => 
  members.value.map(m => ({ label: m.user_name, value: m.user_id }))
)

const filteredIssues = computed(() => {
  let result = issues.value

  if (searchQuery.value) {
    result = result.filter(i => i.title.toLowerCase().includes(searchQuery.value.toLowerCase()))
  }

  if (filterAssignee.value) {
    result = result.filter(i => i.assignee_id === filterAssignee.value)
  }

  if (filterPriority.value) {
    result = result.filter(i => i.priority === filterPriority.value)
  }

  return result
})

const getIssuesByStatus = (status) => {
  return filteredIssues.value.filter(i => i.status === status).sort((a, b) => a.position - b.position)
}

const getPriorityType = (priority) => {
  const types = { HIGH: 'error', MEDIUM: 'warning', LOW: 'success' }
  return types[priority] || 'default'
}

const goToIssue = (issueId) => {
  router.push(`/projects/${route.params.projectId}/issues/${issueId}`)
}

const handleDragEnd = async (evt) => {
  const { item, to, newIndex } = evt
  const issueId = parseInt(item.getAttribute('data-id') || item.querySelector('[data-id]')?.getAttribute('data-id'))
  const targetStatus = to.closest('[data-status]')?.getAttribute('data-status') || statuses[0]

  const targetIssues = getIssuesByStatus(targetStatus)
  const newPosition = newIndex

  try {
    await issuesAPI.updatePositions({
      issue_id: issueId,
      new_status: targetStatus,
      new_position: newPosition,
    })
    
    await loadIssues()
  } catch (error) {
    message.error('Failed to update issue position')
  }
}

const loadProject = async () => {
  loading.value = true
  try {
    const [projectRes, issuesRes] = await Promise.all([
      projectsAPI.getById(route.params.projectId),
      issuesAPI.getAll(route.params.projectId),
    ])
    
    project.value = projectRes.data
    issues.value = issuesRes.data

    // Load team members for assignee options
    const membersRes = await teamsAPI.getMembers(project.value.team_id)
    members.value = membersRes.data
  } catch (error) {
    message.error('Failed to load project')
  } finally {
    loading.value = false
  }
}

const loadIssues = async () => {
  const res = await issuesAPI.getAll(route.params.projectId)
  issues.value = res.data
}

const handleCreateIssue = async () => {
  try {
    await formRef.value?.validate()
    creating.value = true

    const data = {
      ...formData,
      due_date: formData.due_date ? new Date(formData.due_date).toISOString().split('T')[0] : null,
    }

    await issuesAPI.create(route.params.projectId, data)
    message.success('Issue created')
    showCreateIssueModal.value = false
    
    // Reset form
    formData.title = ''
    formData.description = ''
    formData.priority = 'MEDIUM'
    formData.assignee_id = null
    formData.due_date = null

    await loadIssues()
  } catch (error) {
    message.error(error.response?.data?.detail || 'Failed to create issue')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadProject()
})
</script>
