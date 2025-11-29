import apiClient from './axios'

export const projectsAPI = {
  getAll(teamId) {
    return apiClient.get(`/api/teams/${teamId}/projects`)
  },
  
  create(teamId, data) {
    return apiClient.post(`/api/teams/${teamId}/projects`, data)
  },
  
  getById(id) {
    return apiClient.get(`/api/projects/${id}`)
  },
  
  update(id, data) {
    return apiClient.put(`/api/projects/${id}`, data)
  },
  
  delete(id) {
    return apiClient.delete(`/api/projects/${id}`)
  },
  
  archive(id, data) {
    return apiClient.put(`/api/projects/${id}/archive`, data)
  },
  
  toggleFavorite(id) {
    return apiClient.post(`/api/projects/${id}/favorite`)
  },
  
  getLabels(id) {
    return apiClient.get(`/api/projects/${id}/labels`)
  },
  
  createLabel(id, data) {
    return apiClient.post(`/api/projects/${id}/labels`, data)
  },
  
  deleteLabel(projectId, labelId) {
    return apiClient.delete(`/api/projects/${projectId}/labels/${labelId}`)
  },
}
