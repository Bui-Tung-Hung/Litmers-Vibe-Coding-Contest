import apiClient from './axios'

export const commentsAPI = {
  getAll(issueId) {
    return apiClient.get(`/api/issues/${issueId}/comments`)
  },
  
  create(issueId, data) {
    return apiClient.post(`/api/issues/${issueId}/comments`, data)
  },
  
  update(id, data) {
    return apiClient.put(`/api/comments/${id}`, data)
  },
  
  delete(id) {
    return apiClient.delete(`/api/comments/${id}`)
  },
}
