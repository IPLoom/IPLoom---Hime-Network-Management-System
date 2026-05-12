import { defineStore } from 'pinia'
import { DateTime } from 'luxon'
import { parseUTC } from '@/utils/date'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useNotificationStore = defineStore('notifications', () => {
  const events = ref([])
  const isLoading = ref(false)
  const lastViewed = ref(localStorage.getItem('hnms_notifications_last_viewed') || new Date(0).toISOString())

  const unreadCount = computed(() => {
    const lastViewedDate = parseUTC(lastViewed.value)
    return events.value.filter(event => parseUTC(event.changed_at) > lastViewedDate).length
  })

  const fetchNotifications = async () => {
    isLoading.value = true
    try {
      const response = await api.get('/events/', {
        params: { limit: 12 } // Fetch a few more
      })
      events.value = response.data
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      isLoading.value = false
    }
  }

  const markAllAsRead = () => {
    const now = DateTime.now().toUTC().toISO()
    lastViewed.value = now
    localStorage.setItem('hnms_notifications_last_viewed', now)
  }

  return {
    events,
    isLoading,
    unreadCount,
    lastViewed,
    fetchNotifications,
    markAllAsRead
  }
})
