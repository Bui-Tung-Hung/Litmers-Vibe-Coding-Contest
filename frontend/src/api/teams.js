import apiClient from './axios'

export const teamsAPI = {
  getAll() {
    return apiClient.get('/api/teams')
  },
  
  create(data) {
    return apiClient.post('/api/teams', data)
  },
  
  getById(id) {
    return apiClient.get(`/api/teams/${id}`)
  },
  
  update(id, data) {
    return apiClient.put(`/api/teams/${id}`, data)
  },
  
  delete(id) {
    return apiClient.delete(`/api/teams/${id}`)
  },
  
  getMembers(id) {
    return apiClient.get(`/api/teams/${id}/members`)
  },
  
  inviteMember(id, data) {
    return apiClient.post(`/api/teams/${id}/invite`, data)
  },
  
  kickMember(teamId, userId) {
    return apiClient.delete(`/api/teams/${teamId}/members/${userId}`)
  },
  
  changeRole(teamId, userId, data) {
    return apiClient.put(`/api/teams/${teamId}/members/${userId}/role`, data)
  },
  
  leave(id) {
    return apiClient.post(`/api/teams/${id}/leave`)
  },
  
  getActivity(id, limit = 20, offset = 0) {
    return apiClient.get(`/api/teams/${id}/activity`, { params: { limit, offset } })
  },
}
