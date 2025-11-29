import apiClient from './axios'

export const dashboardAPI = {
  getPersonal() {
    return apiClient.get('/api/dashboard/personal')
  },
  
  getProject(projectId) {
    return apiClient.get(`/api/dashboard/project/${projectId}`)
  },
}
