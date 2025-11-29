import { defineStore } from 'pinia'
import { teamsAPI } from '../api/teams'

export const useTeamStore = defineStore('team', {
  state: () => ({
    currentTeam: null,
    teams: [],
    loading: false,
  }),
  
  getters: {
    hasCurrentTeam: (state) => !!state.currentTeam,
  },
  
  actions: {
    async fetchTeams() {
      try {
        this.loading = true
        const response = await teamsAPI.getAll()
        this.teams = response.data
        
        // Set first team as current if none selected
        if (!this.currentTeam && this.teams.length > 0) {
          this.currentTeam = this.teams[0]
        }
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchTeamDetail(id) {
      try {
        const response = await teamsAPI.getById(id)
        this.currentTeam = response.data
        return response.data
      } catch (error) {
        throw error
      }
    },
    
    setCurrentTeam(team) {
      this.currentTeam = team
    },
  },
})
