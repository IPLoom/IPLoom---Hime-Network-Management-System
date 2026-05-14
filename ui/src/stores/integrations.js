import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useIntegrationStore = defineStore('integrations', () => {
  const mqttStatus = ref({ status: 'unknown', reachable: false, loading: false })
  const openwrtStatus = ref({ verified: false, loading: false })
  const adguardStatus = ref({ verified: false, loading: false })

  const fetchStatuses = async () => {
    // MQTT Status
    mqttStatus.value.loading = true
    try {
      const response = await api.get('/mqtt/status')
      mqttStatus.value = { ...response.data, loading: false }
    } catch (error) {
      console.error('Failed to fetch MQTT status:', error)
      mqttStatus.value.loading = false
      mqttStatus.value.status = 'error'
    }

    // OpenWrt Status
    openwrtStatus.value.loading = true
    try {
      const response = await api.get('/integrations/openwrt/config')
      openwrtStatus.value = { verified: response.data?.verified || false, loading: false }
    } catch (error) {
      console.error('Failed to fetch OpenWrt status:', error)
      openwrtStatus.value.loading = false
      openwrtStatus.value.verified = false
    }

    // AdGuard Status
    adguardStatus.value.loading = true
    try {
      const response = await api.get('/integrations/adguard/config')
      adguardStatus.value = { verified: response.data?.verified || false, loading: false }
    } catch (error) {
      console.error('Failed to fetch AdGuard status:', error)
      adguardStatus.value.loading = false
      adguardStatus.value.verified = false
    }
  }

  return {
    mqttStatus,
    openwrtStatus,
    adguardStatus,
    fetchStatuses
  }
})
