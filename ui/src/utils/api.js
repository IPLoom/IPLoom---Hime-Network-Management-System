import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // Increased for long-running scans
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add Auth Interceptor
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

export default api
