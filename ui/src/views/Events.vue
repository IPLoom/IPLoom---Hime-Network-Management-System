<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Events Log</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Track device connectivity and network trends</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="badge-live-label hidden sm:flex">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span>{{ onlineNowCount }} Online Now</span>
        </div>
        <button @click="fetchData" class="btn-action" v-tooltip="'Refresh All'">
          <RefreshCw :class="{ 'animate-spin': loading }" class="h-5 w-5" />
        </button>
      </div>
    </div>

    <!-- Trend Chart Card -->
    <div class="grid grid-cols-1 gap-6">
      <div class="glass-panel">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div class="flex items-center gap-3">
            <div class="p-2.5 bg-blue-500/10 rounded-xl">
              <Activity class="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <h3 class="heading-lg !mb-0">Network Activity Trend</h3>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Hourly aggregation of
                connectivity events</p>
            </div>
          </div>
          <div
            class="flex bg-slate-100/50 dark:bg-slate-900/50 backdrop-blur-sm rounded-xl p-1 border border-slate-200/50 dark:border-slate-700/50 self-start sm:self-auto">
            <button v-for="opt in timeOptions" :key="opt.value" @click="statsTimeRange = opt.value; fetchStats()"
              class="px-3 py-1.5 text-xs font-bold rounded-lg transition-all"
              :class="statsTimeRange === opt.value ? 'bg-white dark:bg-slate-800 shadow-md text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-700'">
              {{ opt.label }}
            </button>
          </div>
        </div>
        <div class="h-64">
          <apexchart v-if="chartSeries[0].data.length > 0" type="line" height="100%" :options="chartOptions"
            :series="chartSeries"></apexchart>
          <div v-else-if="!loadingStats"
            class="h-full flex flex-col items-center justify-center text-slate-400 italic gap-2">
            <ZapOff class="h-8 w-8 text-slate-300" />
            <span>No trend data for this period</span>
          </div>
          <div v-else class="h-full flex items-center justify-center">
            <Loader2 class="h-8 w-8 animate-spin text-blue-500/50" />
          </div>
        </div>
      </div>
    </div>

    <!-- Filters & List -->
    <div class="glass-panel flex flex-col gap-4">
      <div class="flex flex-col md:flex-row gap-4 items-center">
        <div class="relative flex-1 w-full">
          <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input v-model="search" @input="debounceFetch" type="text" placeholder="Search IP, Mac or Name..."
            class="input-base" />
        </div>
        <div class="flex items-center gap-3 w-full md:w-auto">
          <!-- Status Filter -->
          <div class="relative flex-1 md:w-44 group" v-click-outside="() => isStatusOpen = false">
            <button @click="isStatusOpen = !isStatusOpen"
              class="w-full flex items-center justify-between pl-4 pr-3.5 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none hover:ring-2 hover:ring-blue-500/10 transition-all text-sm font-medium text-slate-700 dark:text-slate-300">
              <div class="flex items-center gap-2.5">
                <Filter class="h-3.5 w-3.5" :class="statusFilter ? 'text-blue-500' : 'text-slate-400'" />
                <span>{{ statusFilter ? (statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)) : 'All Statuses'
                }}</span>
              </div>
              <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                :class="{ 'rotate-180': isStatusOpen }" />
            </button>

            <transition enter-active-class="transition duration-100 ease-out"
              enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0">
              <div v-if="isStatusOpen"
                class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5 overflow-hidden">
                <button v-for="opt in ['', 'online', 'offline']" :key="opt"
                  @click="statusFilter = opt; isStatusOpen = false; fetchData()"
                  class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                  :class="statusFilter === opt ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                  <div class="w-2 h-2 rounded-full"
                    :class="opt === 'online' ? 'bg-emerald-500' : opt === 'offline' ? 'bg-slate-400' : 'bg-transparent border border-slate-300'">
                  </div>
                  {{ opt === '' ? 'All Statuses' : opt.charAt(0).toUpperCase() + opt.slice(1) }}
                </button>
              </div>
            </transition>
          </div>
        </div>
      </div>
      <!-- Display Info Line -->
      <div class="px-2 flex items-center justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400">
        <div class="flex items-center gap-2">
          <Activity class="h-3.5 w-3.5 text-blue-500" />
          <span>Showing <b>{{ events.length }}</b> of <b>{{ totalEvents }}</b> events matching current filters</span>
        </div>
      </div>
    </div>

    <!-- Events List -->
    <div class="content-panel">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
          <thead class="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              <th scope="col" class="table-header-cell w-1/4">Device</th>
              <th scope="col" class="table-header-cell hidden md:table-cell">Status</th>
              <th scope="col" class="table-header-cell hidden md:table-cell">Activity</th>
              <th scope="col" class="table-header-cell hidden md:table-cell">Time</th>
              <th scope="col" class="table-header-cell text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
            <template v-for="event in events" :key="event.id">
              <tr class="hover-row group">
                <td class="table-data-cell">
                  <div class="flex items-center gap-4">
                    <div
                      class="p-2.5 bg-slate-100 dark:bg-slate-700 rounded-xl group-hover:bg-white dark:group-hover:bg-slate-600 transition-colors shadow-sm">
                      <component :is="getIcon(event.icon || event.device_type)"
                        class="h-5 w-5 text-slate-600 dark:text-slate-400" />
                    </div>
                    <div class="min-w-0">
                      <div class="text-sm font-semibold text-slate-900 dark:text-white truncate">{{ event.display_name
                      }}</div>
                      <div class="text-[10px] text-slate-500 font-mono tracking-wider">{{ event.ip }}</div>
                    </div>
                  </div>
                </td>
                <td class="table-data-cell hidden md:table-cell">
                  <span v-if="event.status === 'online'" class="badge badge-success">ONLINE</span>
                  <span v-else class="badge badge-danger">OFFLINE</span>
                </td>
                <td class="table-data-cell hidden md:table-cell">
                  <p class="text-xs text-slate-600 dark:text-slate-400">
                    {{ event.status === 'online' ? 'Device joined the network' : 'Device disconnected from network' }}
                  </p>
                </td>
                <td class="table-data-cell hidden md:table-cell whitespace-nowrap">
                  <div class="text-xs text-slate-900 dark:text-slate-200 font-medium">
                    {{ formatRelativeTime(event.changed_at) }}
                  </div>
                  <div class="text-[9px] text-slate-400 tracking-tight">
                    {{ formatDate(event.changed_at) }}
                  </div>
                </td>
                <td class="table-data-cell text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button @click="toggleById(event.id)"
                      class="md:hidden p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-all"
                      v-tooltip="expandedRowIds.has(event.id) ? 'Collapse' : 'Expand'">
                      <component :is="expandedRowIds.has(event.id) ? ChevronUp : ChevronDown" class="h-5 w-5" />
                    </button>
                    <button @click="showDeviceDetail(event)" class="btn-action !p-2" v-tooltip="'View Details'">
                      <ArrowRightCircle class="h-5 w-5" />
                    </button>
                  </div>
                </td>
              </tr>
              <!-- Mobile Expanded Row -->
              <tr v-if="expandedRowIds.has(event.id)" class="md:hidden bg-slate-50/50 dark:bg-slate-800/30">
                <td colspan="5" class="px-8 py-4 border-t border-slate-100 dark:border-slate-800">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <span v-if="event.status === 'online'" class="badge badge-success">ONLINE</span>
                      <span v-else class="badge badge-danger">OFFLINE</span>
                      <div class="text-right">
                        <div class="text-xs text-slate-900 dark:text-slate-200 font-medium">
                          {{ formatRelativeTime(event.changed_at) }}
                        </div>
                      </div>
                    </div>
                    <div>
                      <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Activity</p>
                      <p class="text-xs text-slate-600 dark:text-slate-400">
                        {{ event.status === 'online' ? 'Device joined the network' : 'Device disconnected from network'
                        }}
                      </p>
                    </div>
                    <div>
                      <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Timestamp</p>
                      <p class="text-xs text-slate-500 font-mono">{{ formatDate(event.changed_at) }}</p>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-if="events.length === 0 && !loading">
              <td colspan="5" class="px-8 py-20 text-center">
                <div class="flex flex-col items-center gap-2 text-slate-400">
                  <Inbox class="h-10 w-10 text-slate-200 opacity-20" />
                  <p class="text-sm italic">No events found matching your criteria</p>
                </div>
              </td>
            </tr>
            <tr v-if="loading">
              <td colspan="5" class="px-8 py-20 text-center">
                <Loader2 class="h-8 w-8 animate-spin text-blue-500/30 mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Main Pagination -->
      <div v-if="totalPages > 1"
        class="px-8 py-6 border-t border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-900/30 flex items-center justify-center gap-4">
        <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1" class="pagination-btn">
          Previous
        </button>
        <div
          class="px-5 py-2 bg-slate-900 dark:bg-white rounded-xl text-xs font-black text-white dark:text-slate-900 shadow-md">
          {{ currentPage }} / {{ totalPages }}
        </div>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages" class="pagination-btn">
          Next
        </button>
      </div>
    </div>

    <!-- Device History Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="selectedDevice" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 md:p-8"
          @click.self="closeModal">
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-md"></div>

          <!-- Modal Content -->
          <div class="modal-container">
            <!-- Premium Border Shimmer -->
            <div
              class="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-400/50 to-transparent z-10">
            </div>

            <!-- Modal Header -->
            <div class="p-8 pb-6 flex items-start justify-between">
              <div class="flex items-center gap-6">
                <div class="relative">
                  <div
                    class="p-5 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-[1.5rem] shadow-xl shadow-blue-500/20 text-white">
                    <component :is="getIcon(selectedDevice.icon || selectedDevice.device_type)" class="h-8 w-8" />
                  </div>
                  <div :class="selectedDevice.status === 'online' ? 'bg-emerald-500' : 'bg-red-500'"
                    class="absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-4 border-white dark:border-slate-900 shadow-sm">
                  </div>
                </div>
                <div>
                  <h3 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">{{
                    selectedDevice.display_name }}</h3>
                  <div class="flex items-center gap-3 mt-1">
                    <span
                      class="text-xs font-mono text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">{{
                        selectedDevice.ip }}</span>
                    <span class="text-xs text-slate-400 capitalize">{{ selectedDevice.device_type || 'Unknown Device'
                    }}</span>
                  </div>
                </div>
              </div>
              <button @click="closeModal"
                class="btn-action !p-3 rounded-2xl hover:rotate-90 transition-all duration-300">
                <X class="h-6 w-6" />
              </button>
            </div>

            <!-- Modal Body (Scrollable) -->
            <div class="flex-1 overflow-y-auto p-8 pt-0 custom-scrollbar">
              <!-- Mini Chart -->
              <div
                class="bg-slate-50/50 dark:bg-slate-800/50 rounded-[1.5rem] border border-slate-100 dark:border-slate-700/50 p-6 mb-8">
                <div class="flex items-center justify-between mb-4">
                  <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Connectivity Timeline
                  </h4>
                  <div class="flex items-center gap-4 text-[10px] font-bold">
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                      <span class="text-emerald-600 dark:text-emerald-400">ONLINE</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>
                      <span class="text-red-600 dark:text-red-400">OFFLINE</span>
                    </div>
                  </div>
                </div>
                <div class="h-32">
                  <apexchart v-if="deviceHistory.length > 0" type="line" height="100%" :options="deviceChartOptions"
                    :series="deviceChartSeries"></apexchart>
                  <div v-else class="h-full flex items-center justify-center text-slate-400 italic text-xs">Generating
                    heatmap...</div>
                </div>
              </div>

              <!-- History List -->
              <div class="space-y-4">
                <div class="flex items-center justify-between px-2">
                  <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Detailed Logs</h4>
                  <p class="text-[10px] font-bold text-slate-400">{{ historyTotal }} Events Found</p>
                </div>

                <div class="grid grid-cols-1 gap-3">
                  <div v-for="h in deviceHistory" :key="h.id"
                    class="flex items-center justify-between p-4 rounded-2xl bg-white dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700/50 hover:border-blue-500/30 hover:shadow-lg transition-all">
                    <div class="flex items-center gap-4">
                      <div
                        :class="h.status === 'online' ? 'bg-emerald-500 text-emerald-100' : 'bg-red-500 text-red-100'"
                        class="w-10 h-10 rounded-xl flex items-center justify-center shadow-inner">
                        <component :is="h.status === 'online' ? Wifi : WifiOff" class="h-5 w-5" />
                      </div>
                      <div>
                        <span class="text-xs font-black uppercase tracking-widest"
                          :class="h.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">
                          {{ h.status }}
                        </span>
                        <p class="text-[10px] text-slate-500 mt-0.5 leading-none">
                          {{ h.status === 'online' ? 'Connected successfully' : 'Connection dropped' }}
                        </p>
                      </div>
                    </div>
                    <div class="text-right">
                      <div class="text-[11px] font-bold text-slate-900 dark:text-slate-200">
                        {{ formatDate(h.changed_at) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- History Load More -->
                <div v-if="deviceHistory.length < historyTotal" class="pt-4 pb-8">
                  <button @click="loadMoreHistory" :disabled="loadingHistory"
                    class="btn-outline !py-4 !rounded-2xl font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2">
                    <Loader2 v-if="loadingHistory" class="h-4 w-4 animate-spin text-blue-500" />
                    <span v-else>Load Older Events</span>
                  </button>
                </div>

                <div v-else-if="deviceHistory.length > 0" class="py-10 text-center">
                  <div class="w-1.5 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-full mx-auto mb-2 opacity-50"></div>
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">End of History</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '@/utils/api'
import { formatRelativeTime, formatDate, parseUTC } from '@/utils/date'
import * as LucideIcons from 'lucide-vue-next'
const { RefreshCw, Search, Activity, ArrowRightCircle, X, Loader2, ZapOff, Inbox, ChevronDown, ChevronUp, Wifi, WifiOff, Filter } = LucideIcons
import { getIcon } from '@/utils/icons'
import { useNotifications } from '@/composables/useNotifications'
import { useWebSockets } from '@/composables/useWebSockets'

const { notifyError } = useNotifications()
const { lastNotification } = useWebSockets()

watch(lastNotification, (notif) => {
  if (notif && (notif.event_type === 'new_device' || notif.event_type === 'status_changed' || notif.event_type === 'completed')) {
    fetchData()
    fetchStats()
  }
})

// State
const events = ref([])
const expandedRowIds = ref(new Set())
const stats = ref([])
const loading = ref(false)
const loadingStats = ref(false)
const onlineNowCount = ref(0)
const statsTimeRange = ref(24) // Default to 24 hours
const timeOptions = [
  { label: '24h', value: 24 },
  { label: '7d', value: 168 }, // 7 * 24
  { label: '30d', value: 720 } // 30 * 24
]

// Main Pagination & Filtering
const currentPage = ref(1)
const totalEvents = ref(0)
const itemsPerPage = 20
const search = ref('')
const statusFilter = ref('')
const isStatusOpen = ref(false)

// Modal / Device History
const selectedDevice = ref(null)
const deviceHistory = ref([])
const historyPage = ref(0)
const historyTotal = ref(0)
const loadingHistory = ref(false)

const totalPages = computed(() => Math.ceil(totalEvents.value / itemsPerPage) || 1)

// Data Fetching
const fetchCount = async () => {
  try {
    const params = { status: statusFilter.value || undefined, search: search.value || undefined }
    const res = await api.get('/events/count', { params })
    totalEvents.value = res.data.total
  } catch (err) { console.error('Count failed', err) }
}

const fetchData = async () => {
  loading.value = true
  try {
    await fetchCount()
    const offset = (currentPage.value - 1) * itemsPerPage
    const params = {
      limit: itemsPerPage,
      offset: offset,
      status: statusFilter.value || undefined,
      search: search.value || undefined
    }
    const response = await api.get('/events/', { params })
    events.value = response.data

    const devRes = await api.get('/devices/', { params: { limit: -1 } })
    const allDevices = devRes.data.items || []
    onlineNowCount.value = allDevices.filter(d => d.status === 'online').length
  } catch (err) {
    console.error('Failed to fetch events', err)
    notifyError('Failed to refresh event log')
  } finally {
    loading.value = false
  }
}

let debounceTimer = null
const debounceFetch = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchData()
  }, 400)
}

const changePage = (p) => {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  fetchData()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const fetchStats = async () => {
  loadingStats.value = true
  try {
    const response = await api.get(`/events/stats?hours=${statsTimeRange.value}`)
    stats.value = response.data
  } catch (err) {
    console.error('Failed to fetch stats', err)
  } finally {
    loadingStats.value = false
  }
}

const toggleById = (id) => {
  if (expandedRowIds.value.has(id)) expandedRowIds.value.delete(id)
  else expandedRowIds.value.add(id)
}

const showDeviceDetail = async (device) => {
  selectedDevice.value = device
  deviceHistory.value = []
  historyPage.value = 0
  await fetchDeviceHistoryCount(device.device_id)
  await loadMoreHistory()
}

const fetchDeviceHistoryCount = async (id) => {
  try {
    const res = await api.get(`/events/device/${id}/count`)
    historyTotal.value = res.data.total
  } catch (err) { console.error(err) }
}

const loadMoreHistory = async () => {
  if (!selectedDevice.value) return
  loadingHistory.value = true
  try {
    const limit = 20
    const offset = historyPage.value * limit
    const response = await api.get(`/events/device/${selectedDevice.value.device_id}`, {
      params: { limit, offset }
    })
    deviceHistory.value = [...deviceHistory.value, ...response.data]
    historyPage.value++
  } catch (err) {
    console.error('Failed to fetch device history', err)
  } finally {
    loadingHistory.value = false
  }
}

const closeModal = () => {
  selectedDevice.value = null
}

// Charts Config
const chartOptions = computed(() => ({
  chart: {
    id: 'network-trend',
    type: 'line',
    stacked: false,
    toolbar: { show: false },
    animations: { enabled: true, easing: 'easeinout', speed: 800 },
    background: 'transparent',
    fontFamily: 'inherit'
  },
  colors: ['#10b981', '#ef4444'],
  stroke: { curve: 'smooth', width: 3 },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 },
      formatter: function (val, timestamp) {
        const date = parseUTC(timestamp).toLocal()
        if (statsTimeRange.value <= 24) {
          return date.toFormat('HH:mm')
        }
        return date.toFormat('MMM d')
      }
    },
    axisBorder: { show: false }, axisTicks: { show: false }
  },
  yaxis: {
    min: 0, forceNiceScale: true,
    labels: { style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 } }
  },
  grid: { borderColor: 'rgba(148, 163, 184, 0.1)', strokeDashArray: 6, padding: { left: 10, right: 10 } },
  tooltip: { theme: 'dark', x: { format: 'HH:mm' } },
  dataLabels: { enabled: false },
  legend: { position: 'top', horizontalAlign: 'right', fontSize: '10px', fontWeight: 700, labels: { colors: '#94a3b8' }, markers: { radius: 12 } }
}))

const chartSeries = computed(() => {
  const buckets = {}

  stats.value.forEach(s => {
    const dt = parseUTC(s.timestamp).toLocal()
    const key = dt.startOf(statsTimeRange.value <= 24 ? 'hour' : 'day').toMillis()
    if (!buckets[key]) buckets[key] = { online: 0, offline: 0 }
    buckets[key].online += s.online_count
    buckets[key].offline += s.offline_count
  })

  const sortedKeys = Object.keys(buckets).sort()

  return [
    { name: 'Online', data: sortedKeys.map(k => ({ x: parseInt(k), y: buckets[k].online })) },
    { name: 'Offline', data: sortedKeys.map(k => ({ x: parseInt(k), y: buckets[k].offline })) }
  ]
})

const deviceChartOptions = computed(() => ({
  chart: { toolbar: { show: false }, background: 'transparent', animations: { enabled: true } },
  xaxis: { type: 'datetime', labels: { show: false }, axisBorder: { show: false }, axisTicks: { show: false } },
  yaxis: { labels: { show: false }, min: 0, max: 1.2 },
  grid: { show: false, padding: { left: -10, right: -10 } },
  tooltip: { theme: 'dark', x: { format: 'HH:mm' } },
  colors: ['#3b82f6'],
  stroke: { curve: 'stepline', width: 3 },
  markers: {
    size: 4,
    colors: ['#3b82f6'],
    strokeColors: '#fff',
    strokeWidth: 2,
    hover: { size: 6 }
  },
  dataLabels: { enabled: false }
}))

const deviceChartSeries = computed(() => [{
  name: 'State',
  data: deviceHistory.value.slice().reverse().map(h => ({
    x: parseUTC(h.changed_at).toMillis(),
    y: h.status === 'online' ? 1 : 0.2
  }))
}])

onMounted(() => {
  fetchData()
  fetchStats()
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  backdrop-filter: blur(0px);
  transform: scale(0.95);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.1);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.3);
}
</style>
