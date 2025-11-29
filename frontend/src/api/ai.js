import apiClient from './axios'

export const aiAPI = {
  generateSummary(issueId) {
    return apiClient.post('/api/ai/summary', { issue_id: issueId })
  },
  
  generateSuggestion(issueId) {
    return apiClient.post('/api/ai/suggestion', { issue_id: issueId })
  },
  
  recommendLabels(issueId) {
    return apiClient.post('/api/ai/labels', { issue_id: issueId })
  },
  
  detectDuplicates(issueId) {
    return apiClient.post('/api/ai/duplicates', { issue_id: issueId })
  },
  
  summarizeComments(issueId) {
    return apiClient.post('/api/ai/comment-summary', { issue_id: issueId })
  },
}
