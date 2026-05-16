<template>
  <div class="space-y-6">
    <!-- Header/Summary Card -->
    <div class="premium-card overflow-hidden relative">
      <div class="absolute -top-12 -right-12 w-64 h-64 bg-rose-500/10 dark:bg-rose-400/5 rounded-full blur-3xl"></div>
      
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
        <div>
          <h2 class="text-xl font-black text-slate-900 dark:text-white flex items-center gap-3">
            <div class="w-1.5 h-8 bg-rose-500 rounded-full"></div>
            Internet Access Schedule
          </h2>
          <p class="text-sm text-slate-500 mt-1 font-medium">Automatically block internet access during specific time windows.</p>
        </div>
        
        <button @click="openAddModal" 
          class="flex items-center gap-2 px-6 py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-2xl shadow-xl shadow-rose-500/20 transition-all font-black uppercase tracking-widest text-[11px]">
          <Plus class="w-4 h-4" />
          <span>Add New Window</span>
        </button>
      </div>

      <!-- Quick Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 relative z-10">
        <div class="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-100 dark:border-slate-800">
          <div class="text-[10px] font-black uppercase text-slate-400 mb-1">Active Schedules</div>
          <div class="text-2xl font-black text-slate-900 dark:text-white">{{ activeSchedulesCount }}</div>
        </div>
        <div class="p-4 bg-rose-50 dark:bg-rose-900/20 rounded-2xl border border-rose-100 dark:border-rose-800/30">
          <div class="text-[10px] font-black uppercase text-rose-600 dark:text-rose-400 mb-1">Current Status</div>
          <div class="flex items-center gap-2">
            <div :class="isCurrentlyBlockedBySchedule ? 'bg-rose-500' : 'bg-emerald-500'" class="w-2.5 h-2.5 rounded-full"></div>
            <div class="text-lg font-bold text-slate-900 dark:text-white">
              {{ isCurrentlyBlockedBySchedule ? 'Blocked by Schedule' : 'Allowed' }}
            </div>
          </div>
        </div>
        <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-100 dark:border-blue-800/30">
          <div class="text-[10px] font-black uppercase text-blue-600 dark:text-blue-400 mb-1">Next Transition</div>
          <div class="text-lg font-bold text-slate-900 dark:text-white">{{ nextTransitionTime || 'None' }}</div>
        </div>
      </div>
    </div>

    <!-- 7-Day Heatmap Visualization -->
    <div class="premium-card">
      <div class="flex items-center justify-between mb-8">
        <h3 class="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 ml-1">Weekly Access Heatmap</h3>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1.5">
            <div class="w-3 h-3 bg-emerald-500 rounded-sm"></div>
            <span class="text-[10px] font-bold text-slate-400">Allowed</span>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-3 h-3 bg-rose-500 rounded-sm"></div>
            <span class="text-[10px] font-bold text-slate-400">Blocked</span>
          </div>
        </div>
      </div>

      <div class="overflow-x-auto pb-2 custom-scrollbar">
        <div class="min-w-[800px]">
          <!-- Time Header (00:00 - 23:00) -->
          <div class="grid grid-cols-[80px_repeat(24,1fr)] mb-3">
            <div></div>
            <div v-for="h in 24" :key="h-1" class="text-[8px] font-black text-slate-400 text-center uppercase">
              {{ String(h-1).padStart(2, '0') }}
            </div>
          </div>

          <div class="space-y-1.5" @mouseleave="isDragging && finishSelection()">
            <div v-for="day in 7" :key="day-1" class="grid grid-cols-[80px_repeat(24,1fr)] items-center">
              <div class="text-[10px] font-black uppercase tracking-widest text-slate-500">{{ dayNames[day-1] }}</div>
              <div v-for="hour in 24" :key="hour-1" 
                class="h-8 border-[0.5px] border-slate-100 dark:border-slate-800/50 transition-all cursor-crosshair relative"
                :class="[
                  getHourStatusClass(day-1, hour-1),
                  isInSelection(day-1, hour-1) ? '!bg-rose-600/40 !border-rose-400 z-20 shadow-lg' : ''
                ]"
                @mousedown="startSelection(day-1, hour-1)"
                @mouseenter="updateSelection(day-1, hour-1)"
                @mouseup="finishSelection"
                v-tooltip="getHourTooltip(day-1, hour-1)">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Schedules List -->
    <div class="space-y-4">
      <h3 class="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 ml-1">Active Rules</h3>
      
      <div v-if="schedules.length === 0" class="premium-card !py-12 flex flex-col items-center justify-center text-center">
        <div class="p-6 bg-slate-50 dark:bg-slate-900/50 rounded-full mb-4">
          <Clock class="w-12 h-12 text-slate-300 dark:text-slate-600" />
        </div>
        <h4 class="text-slate-900 dark:text-white font-bold">No Schedules Defined</h4>
        <p class="text-xs text-slate-500 mt-1 max-w-[280px]">Automate your network policy by adding your first internet access schedule.</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="s in schedules" :key="s.id" 
          class="premium-card group hover:border-rose-500/30 transition-all !p-5">
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-rose-500/10 text-rose-600 dark:text-rose-400 rounded-xl">
                <Clock class="w-4 h-4" />
              </div>
              <div>
                <h4 class="text-sm font-bold text-slate-900 dark:text-white">{{ s.name || 'Untitled Schedule' }}</h4>
                <div class="flex items-center gap-1.5 mt-0.5">
                  <div class="w-1.5 h-1.5 rounded-full" :class="s.enabled ? 'bg-emerald-500' : 'bg-slate-300'"></div>
                  <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">{{ s.enabled ? 'Active' : 'Disabled' }}</span>
                </div>
              </div>
            </div>
            
            <div class="flex items-center gap-1">
              <button @click="editSchedule(s)" class="p-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-slate-400 hover:text-blue-500 rounded-lg transition-all">
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button @click="confirmDelete(s.id)" class="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-400 hover:text-red-500 rounded-lg transition-all">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div class="flex flex-wrap gap-2 mb-4">
            <div v-for="day in 7" :key="day-1" 
              class="w-7 h-7 flex items-center justify-center rounded-lg text-[10px] font-black border transition-all"
              :class="s.days.split(',').includes(String(day-1)) 
                ? 'bg-rose-500 text-white border-rose-500 shadow-sm' 
                : 'bg-slate-50 dark:bg-slate-900/50 text-slate-400 border-slate-100 dark:border-slate-800'">
              {{ dayNamesShort[day-1] }}
            </div>
          </div>

          <div class="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-100 dark:border-slate-800">
            <div class="flex items-center gap-4">
              <div>
                <span class="text-[9px] font-black uppercase tracking-widest text-slate-400 block mb-0.5">Start</span>
                <span class="text-sm font-black text-slate-700 dark:text-slate-200">{{ s.start_time }}</span>
              </div>
              <ArrowRight class="w-3.5 h-3.5 text-slate-300" />
              <div>
                <span class="text-[9px] font-black uppercase tracking-widest text-slate-400 block mb-0.5">End</span>
                <span class="text-sm font-black text-slate-700 dark:text-slate-200">{{ s.end_time }}</span>
              </div>
            </div>
            <div class="text-right">
              <Switch v-model="s.enabled" @change="toggleSchedule(s)"
                :class="s.enabled ? 'bg-rose-500' : 'bg-slate-200 dark:bg-slate-700'"
                class="relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75">
                <span aria-hidden="true" :class="s.enabled ? 'translate-x-5' : 'translate-x-0'"
                  class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out" />
              </Switch>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <TransitionRoot appear :show="isModalOpen" as="template">
      <Dialog as="div" @close="closeModal" class="relative z-[100]">
        <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0" enter-to="opacity-100" leave="duration-200 ease-in" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4 text-center">
            <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100" leave="duration-200 ease-in" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-md transform overflow-hidden rounded-3xl bg-white dark:bg-slate-900 p-8 text-left align-middle shadow-2xl transition-all border border-slate-200 dark:border-slate-800">
                <DialogTitle as="h3" class="text-lg font-black text-slate-900 dark:text-white flex items-center gap-3 mb-6">
                  <div class="p-2 bg-rose-500/10 text-rose-500 rounded-xl">
                    <Clock class="w-5 h-5" />
                  </div>
                  {{ editingSchedule ? 'Edit Schedule Window' : 'New Schedule Window' }}
                </DialogTitle>

                <div class="space-y-6">
                  <!-- Name -->
                  <div class="space-y-2">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Schedule Name</label>
                    <input v-model="form.name" type="text" placeholder="e.g. Night Time Block"
                      class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl px-5 py-3.5 text-sm font-bold focus:ring-4 focus:ring-rose-500/10 focus:border-rose-500/50 transition-all dark:text-white" />
                  </div>

                  <!-- Time Range -->
                  <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Start Time</label>
                      <input v-model="form.start_time" type="time"
                        class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl px-5 py-3.5 text-sm font-black focus:ring-4 focus:ring-rose-500/10 focus:border-rose-500/50 transition-all dark:text-white" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">End Time</label>
                      <input v-model="form.end_time" type="time"
                        class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl px-5 py-3.5 text-sm font-black focus:ring-4 focus:ring-rose-500/10 focus:border-rose-500/50 transition-all dark:text-white" />
                    </div>
                  </div>

                  <!-- Days Selection -->
                  <div class="space-y-3">
                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Repeat On</label>
                    <div class="flex justify-between gap-1">
                      <button v-for="day in 7" :key="day-1" 
                        @click="toggleDay(day-1)"
                        class="w-10 h-10 flex items-center justify-center rounded-xl text-[10px] font-black border transition-all"
                        :class="form.days.includes(day-1) 
                          ? 'bg-rose-500 text-white border-rose-500 shadow-lg shadow-rose-500/20' 
                          : 'bg-slate-50 dark:bg-slate-800 text-slate-400 border-slate-100 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'">
                        {{ dayNamesShort[day-1] }}
                      </button>
                    </div>
                  </div>
                </div>

                <div class="mt-10 flex gap-3">
                  <button @click="closeModal" class="flex-1 px-6 py-3.5 rounded-2xl text-sm font-bold text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all">
                    Cancel
                  </button>
                  <button @click="saveSchedule" :disabled="isSaving"
                    class="flex-2 px-8 py-3.5 bg-rose-600 hover:bg-rose-700 text-white rounded-2xl shadow-xl shadow-rose-500/20 transition-all font-black uppercase tracking-widest text-xs flex items-center justify-center gap-2">
                    <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" />
                    {{ editingSchedule ? 'Update Schedule' : 'Create Schedule' }}
                  </button>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { 
  Plus, Clock, Pencil, Trash2, ArrowRight, Loader2, Calendar
} from 'lucide-vue-next'
import { 
  Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot, Switch 
} from '@headlessui/vue'
import api from '@/utils/api'
import { useNotifications } from '@/composables/useNotifications'
import { DateTime } from 'luxon'

const props = defineProps({
  deviceId: {
    type: String,
    required: true
  }
})

const { notifySuccess, notifyError } = useNotifications()

const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const dayNamesShort = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

const schedules = ref([])
const isModalOpen = ref(false)
const isSaving = ref(false)
const editingSchedule = ref(null)

// Drag selection state
const isDragging = ref(false)
const selectionStart = reactive({ day: null, hour: null })
const selectionEnd = reactive({ day: null, hour: null })

const form = reactive({
  name: '',
  start_time: '22:00',
  end_time: '07:00',
  days: [0, 1, 2, 3, 4, 5, 6],
  enabled: true
})

const fetchSchedules = async () => {
  try {
    const res = await api.get(`/internet-schedules/devices/${props.deviceId}/schedules`)
    schedules.value = res.data
  } catch (e) {
    console.error('Failed to fetch schedules:', e)
  }
}

const activeSchedulesCount = computed(() => schedules.value.filter(s => s.enabled).length)

const isCurrentlyBlockedBySchedule = computed(() => {
  const now = DateTime.now()
  const currentTime = now.toFormat('HH:mm')
  const currentDay = String(now.weekday - 1) // 0=Mon in back, 1=Mon in Luxon

  return schedules.value.some(s => {
    if (!s.enabled) return false
    if (!s.days.split(',').includes(currentDay)) return false
    
    const start = s.start_time
    const end = s.end_time
    
    if (start <= end) {
      return currentTime >= start && currentTime < end
    } else {
      return currentTime >= start || currentTime < end
    }
  })
})

const nextTransitionTime = computed(() => {
  // Simple implementation for now: find the next start/end time for today
  const now = DateTime.now()
  const currentTime = now.toFormat('HH:mm')
  const currentDay = String(now.weekday - 1)
  
  const transitions = []
  schedules.value.forEach(s => {
    if (!s.enabled || !s.days.split(',').includes(currentDay)) return
    if (s.start_time > currentTime) transitions.push(s.start_time)
    if (s.end_time > currentTime) transitions.push(s.end_time)
  })
  
  if (transitions.length === 0) return null
  transitions.sort()
  return transitions[0]
})

// Drag Selection Logic
const startSelection = (day, hour) => {
  isDragging.value = true
  selectionStart.day = day
  selectionStart.hour = hour
  selectionEnd.day = day
  selectionEnd.hour = hour
}

const updateSelection = (day, hour) => {
  if (!isDragging.value) return
  selectionEnd.day = day
  selectionEnd.hour = hour
}

const isInSelection = (day, hour) => {
  if (!isDragging.value || selectionStart.day === null) return false
  
  const minDay = Math.min(selectionStart.day, selectionEnd.day)
  const maxDay = Math.max(selectionStart.day, selectionEnd.day)
  const minHour = Math.min(selectionStart.hour, selectionEnd.hour)
  const maxHour = Math.max(selectionStart.hour, selectionEnd.hour)
  
  return day >= minDay && day <= maxDay && hour >= minHour && hour <= maxHour
}

const finishSelection = () => {
  if (!isDragging.value) return
  isDragging.value = false
  
  const minDay = Math.min(selectionStart.day, selectionEnd.day)
  const maxDay = Math.max(selectionStart.day, selectionEnd.day)
  const minHour = Math.min(selectionStart.hour, selectionEnd.hour)
  const maxHour = Math.max(selectionStart.hour, selectionEnd.hour)
  
  // Fill form and open modal
  editingSchedule.value = null
  Object.assign(form, {
    name: '',
    start_time: `${String(minHour).padStart(2, '0')}:00`,
    end_time: `${String(maxHour + 1).padStart(2, '0')}:00`,
    days: Array.from({ length: maxDay - minDay + 1 }, (_, i) => minDay + i),
    enabled: true
  })
  
  // Handle midnight wrap-around
  if (maxHour === 23) form.end_time = '00:00'

  isModalOpen.value = true
  
  // Reset selection coordinates
  selectionStart.day = null
  selectionEnd.day = null
}

const openAddModal = () => {
  editingSchedule.value = null
  Object.assign(form, {
    name: '',
    start_time: '22:00',
    end_time: '07:00',
    days: [0, 1, 2, 3, 4, 5, 6],
    enabled: true
  })
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}

const toggleDay = (day) => {
  const idx = form.days.indexOf(day)
  if (idx === -1) form.days.push(day)
  else form.days.splice(idx, 1)
}

const saveSchedule = async () => {
  if (form.days.length === 0) {
    notifyError('Please select at least one day')
    return
  }

  isSaving.value = true
  try {
    const payload = {
      ...form,
      device_id: props.deviceId,
      days: form.days.sort().join(',')
    }

    if (editingSchedule.value) {
      await api.patch(`/internet-schedules/schedules/${editingSchedule.value.id}`, payload)
      notifySuccess('Schedule updated')
    } else {
      await api.post(`/internet-schedules/devices/${props.deviceId}/schedules`, payload)
      notifySuccess('Schedule created')
    }
    
    await fetchSchedules()
    closeModal()
  } catch (e) {
    notifyError('Failed to save schedule')
  } finally {
    isSaving.value = false
  }
}

const editSchedule = (s) => {
  editingSchedule.value = s
  Object.assign(form, {
    name: s.name,
    start_time: s.start_time,
    end_time: s.end_time,
    days: s.days.split(',').map(Number),
    enabled: s.enabled
  })
  isModalOpen.value = true
}

const toggleSchedule = async (s) => {
  try {
    await api.patch(`/internet-schedules/schedules/${s.id}`, { enabled: s.enabled })
    notifySuccess(`Schedule ${s.enabled ? 'enabled' : 'disabled'}`)
  } catch (e) {
    s.enabled = !s.enabled // Revert
    notifyError('Failed to toggle schedule')
  }
}

const confirmDelete = async (id) => {
  if (!confirm('Are you sure you want to delete this schedule?')) return
  try {
    await api.delete(`/internet-schedules/schedules/${id}`)
    notifySuccess('Schedule deleted')
    await fetchSchedules()
  } catch (e) {
    notifyError('Failed to delete schedule')
  }
}

// Heatmap Helpers
const getHourStatusClass = (day, hour) => {
  const timeStr = String(hour).padStart(2, '0') + ':00'
  const dayStr = String(day)
  
  const isBlocked = schedules.value.some(s => {
    if (!s.enabled) return false
    if (!s.days.split(',').includes(dayStr)) return false
    
    const start = s.start_time
    const end = s.end_time
    
    // Check if the START of this hour is within the block window
    if (start <= end) {
      return timeStr >= start && timeStr < end
    } else {
      return timeStr >= start || timeStr < end
    }
  })
  
  return isBlocked 
    ? 'bg-rose-500 hover:bg-rose-600 shadow-[inset_0_0_10px_rgba(0,0,0,0.1)]' 
    : 'bg-emerald-500/10 dark:bg-emerald-500/5 hover:bg-emerald-500/20'
}

const getHourTooltip = (day, hour) => {
  const timeStr = String(hour).padStart(2, '0') + ':00'
  const dayName = dayNames[day]
  
  const activeScheds = schedules.value.filter(s => {
    if (!s.enabled) return false
    if (!s.days.split(',').includes(String(day))) return false
    const start = s.start_time
    const end = s.end_time
    if (start <= end) return timeStr >= start && timeStr < end
    else return timeStr >= start || timeStr < end
  })

  if (activeScheds.length > 0) {
    return `${dayName} ${timeStr}: Blocked by "${activeScheds[0].name || 'Unnamed'}"`
  }
  return `${dayName} ${timeStr}: Access Allowed`
}

onMounted(fetchSchedules)
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  height: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.4);
}
</style>
