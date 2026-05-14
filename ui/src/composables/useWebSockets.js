import { ref } from 'vue'
import { useNotifications } from './useNotifications'
import { useIntegrationStore } from '@/stores/integrations'

// Shared state (Singleton)
const socket = ref(null)
const connected = ref(false)
const lastNotification = ref(null)
let reconnectTimer = null

export function useWebSockets() {
  const { notifySuccess, notifyError, notifyInfo } = useNotifications()
  const integrationStore = useIntegrationStore()

  const connect = () => {
    const token = localStorage.getItem('token')
    if (!token) return

    // If already connecting or connected, don't start another
    if (socket.value && (socket.value.readyState === WebSocket.OPEN || socket.value.readyState === WebSocket.CONNECTING)) {
        return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/notifications/ws?token=${token}`;

    socket.value = new WebSocket(wsUrl)

    socket.value.onopen = () => {
      console.log('WebSocket Connected')
      connected.value = true
      clearTimeout(reconnectTimer)
    }

    socket.value.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'notification') {
          handleNotification(payload.data)
        } else if (payload.type === 'integration_status') {
          handleIntegrationStatus(payload)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message', err)
      }
    }

    socket.value.onclose = () => {
      console.log('WebSocket Disconnected')
      connected.value = false
      // Attempt reconnect after 5 seconds
      reconnectTimer = setTimeout(connect, 5000)
    }

    socket.value.onerror = (err) => {
      console.error('WebSocket Error', err)
    }
  }

  const handleNotification = (data) => {
    lastNotification.value = data
    const { task_type, event_type, message, level } = data

    if (level === 'ERROR') {
      notifyError(message)
    } else if (level === 'WARNING') {
      notifyInfo(message)
    } else {
      if (event_type === 'new_device' || event_type === 'completed') {
        notifySuccess(message)
      } else {
        notifyInfo(message)
      }
    }
  }

  const handleIntegrationStatus = (payload) => {
    const { integration, data } = payload
    if (integration === 'mqtt') {
      integrationStore.mqttStatus = { ...integrationStore.mqttStatus, ...data }
    } else if (integration === 'openwrt') {
      integrationStore.openwrtStatus = { ...integrationStore.openwrtStatus, ...data }
    } else if (integration === 'adguard') {
      integrationStore.adguardStatus = { ...integrationStore.adguardStatus, ...data }
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    clearTimeout(reconnectTimer)
  }

  return {
    connected,
    lastNotification,
    connect,
    disconnect
  }
}
