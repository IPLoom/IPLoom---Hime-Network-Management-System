import { ref } from 'vue'

const notifications = ref([])

export function useNotifications() {
  const notify = (message, type = 'info', duration = 3000) => {
    const id = Date.now()
    notifications.value.push({
      id,
      message,
      type,
      duration
    })

    setTimeout(() => {
      removeNotification(id)
    }, duration)
  }

  const removeNotification = (id) => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  const notifySuccess = (message, duration = 3000) => {
    notify(message, 'success', duration)
  }

  const notifyError = (message, duration = 4000) => {
    notify(message, 'error', duration)
  }

  const notifyInfo = (message, duration = 3000) => {
    notify(message, 'info', duration)
  }

  return {
    notifications,
    notify,
    notifySuccess,
    notifyError,
    notifyInfo,
    removeNotification
  }
}
