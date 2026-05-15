import { defineStore } from 'pinia'
import api from '@/utils/api'

export const useSystemStore = defineStore('system', {
  state: () => ({
    deviceTypes: [],
    iconMap: {},
    brandRegistry: [],
    availableIcons: [],
    loaded: false,
    loading: false
  }),
  
  actions: {
    async fetchConstants() {
      if (this.loaded || this.loading) return
      this.loading = true
      try {
        const res = await api.get('/system/constants')
        this.deviceTypes = res.data.device_types
        this.iconMap = res.data.type_to_icon_map
        this.brandRegistry = res.data.brand_registry
        this.availableIcons = res.data.available_icons
        this.loaded = true
      } catch (e) {
        console.error('Failed to fetch system constants:', e)
      } finally {
        this.loading = false
      }
    },
    
    getIcon(type) {
      if (!type) return 'help-circle'
      const lower = type.toLowerCase()
      // Check direct map first
      if (this.iconMap[lower]) return this.iconMap[lower]
      // Try fuzzy match in keys
      for (const [key, val] of Object.entries(this.iconMap)) {
        if (lower.includes(key) || key.includes(lower)) return val
      }
      return 'help-circle'
    }
  }
})
