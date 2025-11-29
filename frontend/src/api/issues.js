import apiClient from './axios'

export const issuesAPI = {
  getAll(projectId, params = {}) {
    return apiClient.get(`/api/projects/${projectId}/issues`, { params })
  },
  
  create(projectId, data) {
    return apiClient.post(`/api/projects/${projectId}/issues`, data)
  },
  
  getById(id) {
    return apiClient.get(`/api/issues/${id}`)
  },
  
  update(id, data) {
    return apiClient.put(`/api/issues/${id}`, data)
  },
  
  delete(id) {
    return apiClient.delete(`/api/issues/${id}`)
  },
  
  updatePositions(data) {
    return apiClient.put('/api/issues/positions', data)
  },
  
  getHistory(id) {
    return apiClient.get(`/api/issues/${id}/history`)
  },
}
