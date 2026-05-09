import { defineStore } from 'pinia'
import axios from 'axios'

// Set base URL for axios if not already set globally
const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    setupStatus: {
      needs_setup: false,
      setup_completed: false,
      user_exists: false
    },
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user
  },

  actions: {
    async checkSetupStatus() {
      try {
        const res = await axios.get(`${API_BASE}/auth/setup-status`)
        this.setupStatus = res.data
        return res.data
      } catch (err) {
        console.error('Failed to check setup status', err)
      }
    },

    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const params = new URLSearchParams()
        params.append('username', username)
        params.append('password', password)

        const res = await axios.post(`${API_BASE}/auth/login`, params)
        this.token = res.data.access_token
        localStorage.setItem('token', this.token)
        
        // Set default auth header for future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        
        await this.fetchMe()
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },

    async register(userData) {
      this.loading = true
      this.error = null
      try {
        await axios.post(`${API_BASE}/auth/register`, userData)
        // After registration, log in
        return await this.login(userData.username, userData.password)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Registration failed'
        return false
      } finally {
        this.loading = false
      }
    },

    async fetchMe() {
      if (!this.token) return
      try {
        const res = await axios.get(`${API_BASE}/auth/me`)
        this.user = res.data
        localStorage.setItem('user', JSON.stringify(this.user))
      } catch (err) {
        this.logout()
      }
    },

    async completeOnboarding() {
      try {
        await axios.post(`${API_BASE}/auth/onboarding-complete`)
        this.setupStatus.setup_completed = true
        this.setupStatus.needs_setup = false
      } catch (err) {
        console.error('Failed to complete onboarding', err)
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('user')
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    },

    init() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        this.fetchMe()
      }
      this.checkSetupStatus()
    }
  }
})
