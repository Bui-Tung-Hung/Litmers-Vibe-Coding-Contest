<template>
  <div>
    <NSpin :show="loading">
      <div v-if="issue" style="display: grid; grid-template-columns: 1fr 300px; gap: 24px;">
        <!-- Main Content -->
        <div>
          <NButton text @click="$router.back()" style="margin-bottom: 16px;">← Back</NButton>

          <!-- Title -->
          <NH1 style="margin-bottom: 24px;">{{ issue.title }}</NH1>

          <!-- Description -->
          <NCard title="Description" style="margin-bottom: 24px;">
            <p style="white-space: pre-wrap;">{{ issue.description || 'No description provided' }}</p>
          </NCard>

          <!-- AI Features -->
          <NCard title="AI Features" style="margin-bottom: 24px;">
            <NSpace vertical>
              <div>
                <NButton :loading="aiLoading.summary" @click="handleAISummary" :disabled="!canUseAI">
                  <template #icon>✨</template>
                  Generate AI Summary
                </NButton>
                <NAlert v-if="aiResults.summary" type="info" style="margin-top: 12px;" closable @close="aiResults.summary = null">
                  <strong>AI Summary:</strong>
                  <p style="margin-top: 8px;">{{ aiResults.summary }}</p>
                </NAlert>
              </div>

              <div>
                <NButton :loading="aiLoading.suggestion" @click="handleAISuggestion" :disabled="!canUseAI">
                  <template #icon>💡</template>
                  Get AI Suggestion
                </NButton>
                <NAlert v-if="aiResults.suggestion" type="success" style="margin-top: 12px;" closable @close="aiResults.suggestion = null">
                  <strong>AI Suggestion:</strong>
                  <p style="margin-top: 8px;">{{ aiResults.suggestion }}</p>
                </NAlert>
              </div>

              <div>
                <NButton :loading="aiLoading.labels" @click="handleAILabels" :disabled="!canUseAI">
                  <template #icon>🏷️</template>
                  Recommend Labels
                </NButton>
                <div v-if="aiResults.labels" style="margin-top: 12px;">
                  <NSpace>
                    <NTag v-for="label in aiResults.labels" :key="label" size="small">{{ label }}</NTag>
                  </NSpace>
                </div>
              </div>

              <div>
                <NButton :loading="aiLoading.duplicates" @click="handleAIDuplicates" :disabled="!canUseAI">
                  <template #icon>🔍</template>
                  Detect Duplicates
                </NButton>
                <div v-if="aiResults.duplicates && aiResults.duplicates.length > 0" style="margin-top: 12px;">
                  <NAlert type="warning">
                    <strong>Similar Issues Found:</strong>
                    <ul style="margin-top: 8px; padding-left: 20px;">
                      <li v-for="dup in aiResults.duplicates" :key="dup.id">
                        <a href="#" @click.prevent="$router.push(`/projects/${issue.project_id}/issues/${dup.id}`)">
                          {{ dup.title }} ({{ (dup.similarity * 100).toFixed(0) }}% similar)
                        </a>
                      </li>
                    </ul>
                  </NAlert>
                </div>
              </div>

              <div v-if="comments.length >= 5">
                <NButton :loading="aiLoading.commentsSummary" @click="handleAICommentsSummary">
                  <template #icon>📝</template>
                  Summarize Discussion
                </NButton>
                <NAlert v-if="aiResults.commentsSummary" type="info" style="margin-top: 12px;" closable @close="aiResults.commentsSummary = null">
                  <strong>Discussion Summary:</strong>
                  <p style="margin-top: 8px;">{{ aiResults.commentsSummary }}</p>
                </NAlert>
              </div>

              <NAlert v-if="aiError" type="error" closable @close="aiError = null">
                {{ aiError }}
              </NAlert>
            </NSpace>
          </NCard>

          <!-- Comments & History -->
          <NTabs type="line" animated>
            <NTabPane name="comments" tab="Comments">
              <div style="margin-bottom: 16px;">
                <NInput
                  v-model:value="newComment"
                  type="textarea"
                  :rows="3"
                  placeholder="Add a comment..."
                  :maxlength="1000"
                  show-count
                />
                <NButton type="primary" style="margin-top: 8px;" :loading="addingComment" @click="handleAddComment">
                  Add Comment
                </NButton>
              </div>

              <NDivider />

              <div v-if="comments.length > 0" style="display: flex; flex-direction: column; gap: 16px;">
                <div v-for="comment in comments" :key="comment.id" style="padding: 12px; background: #f9f9f9; border-radius: 8px;">
                  <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <NAvatar round :size="32">{{ comment.author_name?.charAt(0).toUpperCase() }}</NAvatar>
                      <div>
                        <div style="font-weight: 500;">{{ comment.author_name }}</div>
                        <div style="font-size: 12px; color: #999;">{{ formatRelative(comment.created_at) }}</div>
                      </div>
                    </div>
                    <NSpace v-if="canDeleteComment(comment)">
                      <NButton v-if="editingCommentId !== comment.id" size="small" text @click="handleStartEditComment(comment)">
                        Edit
                      </NButton>
                      <NButton size="small" text @click="handleDeleteComment(comment.id)">
                        Delete
                      </NButton>
                    </NSpace>
                  </div>
                  <div v-if="editingCommentId === comment.id">
                    <NInput
                      v-model:value="editingCommentContent"
                      type="textarea"
                      :rows="3"
                      :maxlength="1000"
                      show-count
                      style="margin-bottom: 8px;"
                    />
                    <NSpace>
                      <NButton size="small" type="primary" @click="handleUpdateComment(comment.id)">
                        Save
                      </NButton>
                      <NButton size="small" @click="handleCancelEditComment">
                        Cancel
                      </NButton>
                    </NSpace>
                  </div>
                  <p v-else style="margin: 0; white-space: pre-wrap;">{{ comment.content }}</p>
                </div>
              </div>
              <NEmpty v-else description="No comments yet" />
            </NTabPane>

            <NTabPane name="history" tab="History">
              <NTimeline>
                <NTimelineItem
                  v-for="history in histories"
                  :key="history.id"
                  :title="formatHistoryTitle(history)"
                  :time="formatRelative(history.created_at)"
                >
                  <template #icon>
                    <span style="font-size: 16px;">{{ getHistoryIcon(history.field) }}</span>
                  </template>
                  <div style="color: #666; font-size: 14px;">
                    <strong>{{ history.user.name }}</strong>
                    <div style="margin-top: 4px;">
                      <span v-if="history.old_value" style="text-decoration: line-through; color: #999;">{{ history.old_value }}</span>
                      <span v-if="history.old_value && history.new_value"> → </span>
                      <span v-if="history.new_value" style="color: #18a058;">{{ history.new_value }}</span>
                    </div>
                  </div>
                </NTimelineItem>
              </NTimeline>
              <NEmpty v-if="histories.length === 0" description="No changes yet" />
            </NTabPane>
          </NTabs>
        </div>

        <!-- Sidebar -->
        <div>
          <NCard title="Details">
            <NSpace vertical>
              <div>
                <div style="font-size: 12px; color: #999; margin-bottom: 4px;">Status</div>
                <NSelect v-model:value="issue.status" :options="statusOptions" @update:value="handleUpdate" />
              </div>

              <div>
                <div style="font-size: 12px; color: #999; margin-bottom: 4px;">Priority</div>
                <NSelect v-model:value="issue.priority" :options="priorityOptions" @update:value="handleUpdate" />
              </div>

              <div>
                <div style="font-size: 12px; color: #999; margin-bottom: 4px;">Assignee</div>
                <NSelect
                  v-model:value="issue.assignee_id"
                  :options="assigneeOptions"
                  clearable
                  filterable
                  @update:value="handleUpdate"
                />
              </div>

              <div>
                <div style="font-size: 12px; color: #999; margin-bottom: 4px;">Due Date</div>
                <NDatePicker
                  v-model:value="dueDateValue"
                  type="date"
                  clearable
                  style="width: 100%;"
                  @update:value="handleUpdateDueDate"
                />
              </div>

              <NDivider />

              <NButton type="error" block @click="handleDelete">Delete Issue</NButton>
            </NSpace>
          </NCard>
        </div>
      </div>
    </NSpin>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NH1, NCard, NButton, NSpin, NSpace, NInput, NSelect, NDatePicker, NTag, NAvatar, NAlert, NDivider, NEmpty, NTabs, NTabPane, NTimeline, NTimelineItem, useMessage, useDialog } from 'naive-ui'
import { issuesAPI } from '../api/issues'
import { commentsAPI } from '../api/comments'
import { aiAPI } from '../api/ai'
import { teamsAPI } from '../api/teams'
import { projectsAPI } from '../api/projects'
import { formatRelative } from '../utils/date'
import { PRIORITIES, DEFAULT_STATUSES } from '../utils/constants'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const loading = ref(false)
const addingComment = ref(false)
const issue = ref(null)
const comments = ref([])
const histories = ref([])
const members = ref([])
const newComment = ref('')
const editingCommentId = ref(null)
const editingCommentContent = ref('')

const aiLoading = reactive({
  summary: false,
  suggestion: false,
  labels: false,
  duplicates: false,
  commentsSummary: false,
})

const aiResults = reactive({
  summary: null,
  suggestion: null,
  labels: null,
  duplicates: null,
  commentsSummary: null,
})

const aiError = ref(null)

const statusOptions = DEFAULT_STATUSES.map(s => ({ label: s, value: s }))
const priorityOptions = Object.values(PRIORITIES).map(p => ({ label: p.label, value: p.value }))

const assigneeOptions = computed(() => 
  members.value.map(m => ({ label: m.user_name, value: m.user_id }))
)

const dueDateValue = computed({
  get: () => issue.value?.due_date ? new Date(issue.value.due_date).getTime() : null,
  set: () => {},
})

const canUseAI = computed(() => {
  // Allow AI if description exists (even if short for testing)
  return !!issue.value?.description
})

const canDeleteComment = (comment) => {
  return comment.author_id === authStore.user?.id
}

const loadIssue = async () => {
  loading.value = true
  try {
    const [issueRes, commentsRes] = await Promise.all([
      issuesAPI.getById(route.params.issueId),
      commentsAPI.getAll(route.params.issueId),
    ])

    issue.value = issueRes.data
    comments.value = commentsRes.data

    // Load project and members
    const projectRes = await projectsAPI.getById(issue.value.project_id)
    const membersRes = await teamsAPI.getMembers(projectRes.data.team_id)
    members.value = membersRes.data
    
    // Load history
    await loadHistory()
  } catch (error) {
    message.error('Failed to load issue')
    router.back()
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  try {
    const res = await issuesAPI.getHistory(issue.value.id)
    histories.value = res.data
  } catch (error) {
    message.error('Failed to load history')
  }
}

const getHistoryIcon = (field) => {
  const icons = {
    status: '📊',
    priority: '⚡',
    assignee: '👤',
    title: '✏️',
    due_date: '📅'
  }
  return icons[field] || '📌'
}

const formatHistoryTitle = (history) => {
  const fieldNames = {
    status: 'Status',
    priority: 'Priority',
    assignee: 'Assignee',
    title: 'Title',
    due_date: 'Due Date'
  }
  return `${fieldNames[history.field] || history.field} changed`
}

const handleUpdate = async () => {
  try {
    await issuesAPI.update(issue.value.id, {
      status: issue.value.status,
      priority: issue.value.priority,
      assignee_id: issue.value.assignee_id,
    })
    message.success('Issue updated')
    await loadHistory()
  } catch (error) {
    message.error('Failed to update issue')
  }
}

const handleUpdateDueDate = async (value) => {
  try {
    const dueDate = value ? new Date(value).toISOString().split('T')[0] : null
    await issuesAPI.update(issue.value.id, { due_date: dueDate })
    issue.value.due_date = dueDate
    message.success('Due date updated')
    await loadHistory()
  } catch (error) {
    message.error('Failed to update due date')
  }
}

const handleDelete = () => {
  dialog.warning({
    title: 'Delete Issue',
    content: 'Are you sure you want to delete this issue?',
    positiveText: 'Delete',
    negativeText: 'Cancel',
    onPositiveClick: async () => {
      try {
        await issuesAPI.delete(issue.value.id)
        message.success('Issue deleted')
        router.back()
      } catch (error) {
        message.error('Failed to delete issue')
      }
    },
  })
}

const handleAddComment = async () => {
  if (!newComment.value.trim()) return

  try {
    addingComment.value = true
    await commentsAPI.create(issue.value.id, { content: newComment.value })
    newComment.value = ''
    const res = await commentsAPI.getAll(issue.value.id)
    comments.value = res.data
    message.success('Comment added')
  } catch (error) {
    message.error('Failed to add comment')
  } finally {
    addingComment.value = false
  }
}

const handleDeleteComment = async (commentId) => {
  try {
    await commentsAPI.delete(commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
    message.success('Comment deleted')
  } catch (error) {
    message.error('Failed to delete comment')
  }
}

const handleStartEditComment = (comment) => {
  editingCommentId.value = comment.id
  editingCommentContent.value = comment.content
}

const handleCancelEditComment = () => {
  editingCommentId.value = null
  editingCommentContent.value = ''
}

const handleUpdateComment = async (commentId) => {
  if (!editingCommentContent.value.trim()) return

  try {
    await commentsAPI.update(commentId, { content: editingCommentContent.value })
    const res = await commentsAPI.getAll(issue.value.id)
    comments.value = res.data
    message.success('Comment updated')
    editingCommentId.value = null
    editingCommentContent.value = ''
  } catch (error) {
    message.error('Failed to update comment')
  }
}

// AI Features
const handleAISummary = async () => {
  aiLoading.summary = true
  aiError.value = null
  try {
    const res = await aiAPI.generateSummary(issue.value.id)
    aiResults.summary = res.data.summary
  } catch (error) {
    aiError.value = error.response?.data?.detail || 'AI request failed. Rate limit may be exceeded.'
  } finally {
    aiLoading.summary = false
  }
}

const handleAISuggestion = async () => {
  aiLoading.suggestion = true
  aiError.value = null
  try {
    const res = await aiAPI.generateSuggestion(issue.value.id)
    aiResults.suggestion = res.data.suggestion
  } catch (error) {
    aiError.value = error.response?.data?.detail || 'AI request failed'
  } finally {
    aiLoading.suggestion = false
  }
}

const handleAILabels = async () => {
  aiLoading.labels = true
  aiError.value = null
  try {
    const res = await aiAPI.recommendLabels(issue.value.id)
    aiResults.labels = res.data.recommended_labels
  } catch (error) {
    aiError.value = error.response?.data?.detail || 'AI request failed'
  } finally {
    aiLoading.labels = false
  }
}

const handleAIDuplicates = async () => {
  aiLoading.duplicates = true
  aiError.value = null
  try {
    const res = await aiAPI.detectDuplicates(issue.value.id)
    aiResults.duplicates = res.data.similar_issues
  } catch (error) {
    aiError.value = error.response?.data?.detail || 'AI request failed'
  } finally {
    aiLoading.duplicates = false
  }
}

const handleAICommentsSummary = async () => {
  aiLoading.commentsSummary = true
  aiError.value = null
  try {
    const res = await aiAPI.summarizeComments(issue.value.id)
    aiResults.commentsSummary = res.data.summary
  } catch (error) {
    aiError.value = error.response?.data?.detail || 'AI request failed'
  } finally {
    aiLoading.commentsSummary = false
  }
}

onMounted(() => {
  loadIssue()
})
</script>
