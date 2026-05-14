import { defineStore } from 'pinia'
import { DateTime } from 'luxon'
import { parseUTC } from '@/utils/date'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useNotificationStore = defineStore('notifications', () => {
  const events = ref([])
  const isLoading = ref(false)
  const unreadCount = ref(0)

  const fetchNotifications = async (unreadOnly = false) => {
    isLoading.value = true
    try {
      const response = await api.get('/notifications/', {
        params: { 
          limit: 12,
          unread_only: unreadOnly
        }
      })
      events.value = response.data
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      isLoading.value = false
    }
  }

  const fetchUnreadCount = async () => {
    try {
      const response = await api.get('/notifications/unread-count')
      unreadCount.value = response.data.count
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
    }
  }

  const markAsRead = async (notifIds) => {
    try {
      await api.post('/notifications/mark-read', { notif_ids: notifIds })
      // Update local state by setting read_at
      const now = DateTime.now().toISO()
      events.value = events.value.map(e => 
        notifIds.includes(e.id) ? { ...e, read_at: now } : e
      )
      // Recalculate unread count
      await fetchUnreadCount()
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      await api.post('/notifications/mark-read', { all: true })
      // Update local state immediately
      const now = DateTime.now().toISO()
      events.value = events.value.map(e => ({ ...e, read_at: now }))
      unreadCount.value = 0
    } catch (error) {
      console.error('Failed to mark notifications as read:', error)
    }
  }

  return {
    events,
    isLoading,
    unreadCount,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead
  }
})
