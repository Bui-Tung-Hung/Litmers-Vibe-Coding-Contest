<template>
  <div>
    <NH1>Dashboard</NH1>
    
    <NSpin :show="loading">
      <div v-if="dashboardData" style="display: grid; gap: 32px;">
        <!-- Stats Cards -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;">
          <NCard title="My Issues">
            <NStatistic :value="dashboardData.total_assigned_issues || 0" />
          </NCard>
          <NCard title="Due Today">
            <NStatistic :value="dashboardData.due_today?.length || 0" />
          </NCard>
          <NCard title="Due Soon">
            <NStatistic :value="dashboardData.due_soon?.length || 0" />
          </NCard>
        </div>

        <!-- My Teams -->
        <NCard title="My Teams">
          <div v-if="dashboardData.teams?.length > 0" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 24px;">
            <NCard
              v-for="team in dashboardData.teams"
              :key="team.id"
              hoverable
              style="cursor: pointer;"
              @click="$router.push(`/teams/${team.id}`)"
            >
              <h3 style="margin: 0 0 8px 0;">{{ team.name }}</h3>
              <div style="font-size: 14px; color: #999;">
                {{ team.member_count || 0 }} members · {{ team.project_count || 0 }} projects
              </div>
            </NCard>
          </div>
          <NEmpty v-else description="No teams yet">
            <template #extra>
              <NButton @click="$router.push('/teams')">Create Team</NButton>
            </template>
          </NEmpty>
        </NCard>

        <!-- My Assigned Issues -->
        <NCard title="My Assigned Issues">
          <div v-if="dashboardData.assigned_issues_by_status">
            <div v-for="(issues, status) in dashboardData.assigned_issues_by_status" :key="status" style="margin-bottom: 24px;">
              <h4 style="margin-bottom: 12px;">{{ status }} ({{ issues.length }})</h4>
              <div style="display: flex; flex-direction: column; gap: 8px;">
                <NCard
                  v-for="issue in issues.slice(0, 5)"
                  :key="issue.id"
                  size="small"
                  hoverable
                  style="cursor: pointer;"
                  @click="$router.push(`/projects/${issue.project_id}/issues/${issue.id}`)"
                >
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <div style="font-weight: 500;">{{ issue.title }}</div>
                      <div style="font-size: 12px; color: #999; margin-top: 4px;">
                        {{ issue.project_name }}
                      </div>
                    </div>
                    <NTag v-if="issue.priority" :type="getPriorityType(issue.priority)" size="small">
                      {{ issue.priority }}
                    </NTag>
                  </div>
                </NCard>
              </div>
            </div>
          </div>
          <NEmpty v-else description="No assigned issues" />
        </NCard>
      </div>
    </NSpin>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { NH1, NCard, NSpin, NStatistic, NButton, NEmpty, NTag } from 'naive-ui'
import { dashboardAPI } from '../api/dashboard'
import { useTeamStore } from '../stores/team'

const loading = ref(true)
const dashboardData = ref(null)
const teamStore = useTeamStore()

const getPriorityType = (priority) => {
  const types = { HIGH: 'error', MEDIUM: 'warning', LOW: 'success' }
  return types[priority] || 'default'
}

onMounted(async () => {
  try {
    loading.value = true
    const [dashRes, teamsRes] = await Promise.all([
      dashboardAPI.getPersonal(),
      teamStore.fetchTeams(),
    ])
    dashboardData.value = { ...dashRes.data, teams: teamStore.teams }
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  } finally {
    loading.value = false
  }
})
</script>
