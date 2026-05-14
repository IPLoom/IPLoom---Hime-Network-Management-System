import { ref, onUnmounted } from 'vue'
import { useNotifications } from './useNotifications'

export function useWebSockets() {
  const socket = ref(null)
  const connected = ref(false)
  const lastNotification = ref(null)
  const { notifySuccess, notifyError, notifyInfo } = useNotifications()
  let reconnectTimer = null

  const connect = () => {
    const token = localStorage.getItem('token')
    if (!token) return

    // Clear any existing connection
    if (socket.value) {
        socket.value.close()
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

    // Map levels to notification types
    if (level === 'ERROR') {
      notifyError(message)
    } else if (level === 'WARNING') {
      notifyInfo(message) // Or a specific warning toast if available
    } else {
      // For specific event types, we can use different styles
      if (event_type === 'new_device') {
        notifySuccess(message)
      } else if (event_type === 'status_changed') {
        notifyInfo(message)
      } else if (event_type === 'completed') {
        notifySuccess(message)
      } else {
        notifyInfo(message)
      }
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
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
