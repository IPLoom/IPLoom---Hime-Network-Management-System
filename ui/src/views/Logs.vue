<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">System Logs</h1>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    View backend system events and monitoring. Found {{ displayTotal }} records.
                </p>
            </div>
            <div class="flex items-center gap-3">
                <!-- Tab Switcher -->
                <div class="flex p-0.5 bg-slate-100 dark:bg-slate-700/50 rounded-lg">
                    <button @click="currentTab = 'all'"
                        class="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-2"
                        :class="currentTab === 'all' ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'">
                        <Activity class="w-3.5 h-3.5" />
                        System Logs
                    </button>
                    <button @click="currentTab = 'tasks'"
                        class="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-2"
                        :class="currentTab === 'tasks' ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'">
                        <Cog class="w-3.5 h-3.5" />
                        Task Activity
                    </button>
                </div>
                <button @click="fetchLogs" class="btn-action" v-tooltip="'Refresh Logs'">
                    <RefreshCw class="w-5 h-5" :class="{ 'animate-spin': loading }" />
                </button>
                <button @click.stop="promptClearLogs"
                    class="btn-action hover:!text-red-500 hover:!bg-red-50 dark:hover:!bg-red-900/20"
                    v-tooltip="'Clear All Logs'">
                    <Trash2 class="w-5 h-5" />
                </button>
            </div>
        </div>

        <!-- Filters & Search -->
        <div class="glass-panel flex flex-col gap-4">
            <div class="flex flex-col md:flex-row gap-4 items-center">
                <div class="relative flex-1 w-full">
                    <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input v-model="search" @input="debounceSearch" type="text" placeholder="Search logs..."
                        class="input-base" />
                </div>
                <div class="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
                    <!-- Task Type Filter (Visible only for Task Activity) -->
                    <div v-if="currentTab === 'tasks'" class="relative flex-1 md:w-44 group"
                        v-click-outside="() => isTaskTypeOpen = false">
                        <button @click="isTaskTypeOpen = !isTaskTypeOpen"
                            class="w-full flex items-center justify-between pl-4 pr-3.5 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none hover:ring-2 hover:ring-blue-500/10 transition-all text-sm font-medium text-slate-700 dark:text-slate-300">
                            <div class="flex items-center gap-2.5">
                                <Filter class="h-3.5 w-3.5"
                                    :class="taskTypeFilter ? 'text-blue-500' : 'text-slate-400'" />
                                <span>{{ getTaskLabel(taskTypeFilter) || 'All Types' }}</span>
                            </div>
                            <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                                :class="{ 'rotate-180': isTaskTypeOpen }" />
                        </button>

                        <transition enter-active-class="transition duration-100 ease-out"
                            enter-from-class="transform scale-95 opacity-0"
                            enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-75 ease-in"
                            leave-from-class="transform scale-100 opacity-100"
                            leave-to-class="transform scale-95 opacity-0">
                            <div v-if="isTaskTypeOpen"
                                class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5 overflow-hidden">
                                <button @click="taskTypeFilter = ''; isTaskTypeOpen = false; fetchLogs()"
                                    class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                                    :class="taskTypeFilter === '' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                    All Types
                                </button>
                                <button v-for="type in taskTypes" :key="type.value"
                                    @click="taskTypeFilter = type.value; isTaskTypeOpen = false; fetchLogs()"
                                    class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                                    :class="taskTypeFilter === type.value ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                    <component :is="type.icon" class="w-3.5 h-3.5 opacity-70" />
                                    {{ type.label }}
                                </button>
                            </div>
                        </transition>
                    </div>

                    <!-- Level Filter (Visible only for System Logs) -->
                    <div v-else class="relative flex-1 md:w-44 group" v-click-outside="() => isLevelOpen = false">
                        <button @click="isLevelOpen = !isLevelOpen"
                            class="w-full flex items-center justify-between pl-4 pr-3.5 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none hover:ring-2 hover:ring-blue-500/10 transition-all text-sm font-medium text-slate-700 dark:text-slate-300">
                            <div class="flex items-center gap-2.5">
                                <Filter class="h-3.5 w-3.5" :class="levelFilter ? 'text-blue-500' : 'text-slate-400'" />
                                <span>{{ levelFilter || 'All Levels' }}</span>
                            </div>
                            <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                                :class="{ 'rotate-180': isLevelOpen }" />
                        </button>

                        <transition enter-active-class="transition duration-100 ease-out"
                            enter-from-class="transform scale-95 opacity-0"
                            enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-75 ease-in"
                            leave-from-class="transform scale-100 opacity-100"
                            leave-to-class="transform scale-95 opacity-0">
                            <div v-if="isLevelOpen"
                                class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5 overflow-hidden">
                                <button @click="levelFilter = ''; isLevelOpen = false; fetchLogs()"
                                    class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                                    :class="levelFilter === '' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                    All Levels
                                </button>
                                <button v-for="lvl in levels" :key="lvl"
                                    @click="levelFilter = lvl; isLevelOpen = false; fetchLogs()"
                                    class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                                    :class="levelFilter === lvl ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                    {{ lvl }}
                                </button>
                            </div>
                        </transition>
                    </div>

                    <!-- Rows Limit Filter -->
                    <div class="relative flex-1 md:w-32 group" v-click-outside="() => isRowsOpen = false">
                        <button @click="isRowsOpen = !isRowsOpen"
                            class="w-full flex items-center justify-between pl-4 pr-3.5 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none hover:ring-2 hover:ring-blue-500/10 transition-all text-sm font-medium text-slate-700 dark:text-slate-300">
                            <div class="flex items-center gap-2.5">
                                <span class="text-[10px] uppercase font-bold text-slate-400">Rows</span>
                                <span class="font-bold">{{ limit }}</span>
                            </div>
                            <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                                :class="{ 'rotate-180': isRowsOpen }" />
                        </button>

                        <transition enter-active-class="transition duration-100 ease-out"
                            enter-from-class="transform scale-95 opacity-0"
                            enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-75 ease-in"
                            leave-from-class="transform scale-100 opacity-100"
                            leave-to-class="transform scale-95 opacity-0">
                            <div v-if="isRowsOpen"
                                class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5 overflow-hidden">
                                <button v-for="opt in [20, 50, 100, 200]" :key="opt"
                                    @click="limit = opt; isRowsOpen = false; fetchLogs()"
                                    class="w-full px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                                    :class="limit === opt ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                    {{ opt }}
                                </button>
                            </div>
                        </transition>
                    </div>
                </div>
            </div>
            <!-- Display Info Line -->
            <div
                class="px-2 flex items-center justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400">
                <div class="flex items-center gap-2">
                    <Activity class="h-3.5 w-3.5 text-blue-500" />
                    <span>Showing <b>{{ displayedLogs.length }}</b> of <b>{{ displayTotal }}</b> logs matching current
                        filters</span>
                </div>
                <div v-if="currentTab === 'tasks'" class="flex items-center gap-2">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" v-model="autoRefresh"
                            class="rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-0">
                        <span class="text-xs font-medium">Auto-refresh (5s)</span>
                    </label>
                </div>
            </div>
        </div>

        <!-- Logs Table -->
        <div class="content-panel">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead class="bg-slate-50 dark:bg-slate-900/50">
                        <tr>
                            <th scope="col" class="table-header-cell w-48">Timestamp</th>
                            <th scope="col" class="table-header-cell w-24">
                                {{ currentTab === 'tasks' ? 'Type' : 'Level' }}
                            </th>
                            <th scope="col" class="table-header-cell w-48">
                                {{ currentTab === 'tasks' ? 'Target' : 'Module' }}
                            </th>
                            <th scope="col" class="table-header-cell">Message</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
                        <tr v-if="loading && logs.length === 0">
                            <td colspan="4" class="px-6 py-20 text-center">
                                <RefreshCw class="h-8 w-8 mx-auto animate-spin mb-2 text-slate-400" />
                                <p class="text-slate-500 dark:text-slate-400">Loading logs...</p>
                            </td>
                        </tr>
                        <tr v-else-if="logs.length === 0">
                            <td colspan="4" class="px-6 py-20 text-center">
                                <p class="text-slate-500 dark:text-slate-400 italic">No logs found matching your
                                    criteria.</p>
                            </td>
                        </tr>
                        <tr v-for="(log, idx) in displayedLogs" :key="idx" class="hover-row">
                            <td class="table-data-cell font-mono text-xs opacity-70">
                                {{ formatTime(log.timestamp) }}
                            </td>

                            <!-- Task Type or Level -->
                            <td class="table-data-cell">
                                <span v-if="currentTab === 'tasks'" :class="[
                                    'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider',
                                    getTaskColor(log.task_type)
                                ]">
                                    <component :is="getTaskIcon(log.task_type)" class="w-3 h-3" />
                                    {{ getTaskLabel(log.task_type) }}
                                </span>
                                <span v-else :class="[
                                    'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider',
                                    levelColors[log.level] || 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
                                ]">
                                    {{ log.level }}
                                </span>
                            </td>

                            <!-- Target or Module -->
                            <td class="table-data-cell font-mono text-xs opacity-70">
                                <div v-if="currentTab === 'tasks'" class="flex flex-col">
                                    <span class="font-bold text-slate-700 dark:text-slate-300">{{ log.target || '-'
                                    }}</span>
                                    <span v-if="log.event_type" class="text-[10px] uppercase tracking-wide"
                                        :class="{ 'text-green-600': log.event_type === 'completed', 'text-blue-600': log.event_type === 'started', 'text-red-600': log.event_type === 'failed' }">
                                        {{ log.event_type }}
                                    </span>
                                </div>
                                <span v-else :title="log.path">{{ log.module }}:{{ log.line }}</span>
                            </td>

                            <!-- Message and Details -->
                            <td class="table-data-cell font-mono text-sm break-all">
                                {{ log.message }}

                                <!-- Task Duration Badge -->
                                <span v-if="log.duration_ms"
                                    class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                                    ⏱ {{ log.duration_ms }}ms
                                </span>

                                <!-- Task Details JSON -->
                                <div v-if="log.details" class="mt-2 text-xs text-slate-500 font-mono">
                                    <span v-for="(val, key) in log.details" :key="key" class="mr-3 inline-block">
                                        <span class="opacity-70">{{ key }}:</span> <span class="font-medium">{{ val
                                        }}</span>
                                    </span>
                                </div>

                                <div v-if="log.exception"
                                    class="mt-2 p-3 bg-red-50/50 dark:bg-red-900/10 rounded-lg border border-red-100 dark:border-red-900/30 text-xs text-red-600 dark:text-red-400 whitespace-pre-wrap font-mono overflow-x-auto">
                                    {{ log.exception }}
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div v-if="totalPages > 1"
                class="flex justify-center items-center gap-2 p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/30">
                <button @click="changePage(page - 1)" :disabled="page <= 1" class="pagination-btn">
                    Previous
                </button>
                <div
                    class="px-4 py-2 bg-slate-900 dark:bg-white rounded-lg text-sm font-medium text-white dark:text-slate-900">
                    {{ page }} / {{ totalPages }}
                </div>
                <button @click="changePage(page + 1)" :disabled="page >= totalPages" class="pagination-btn">
                    Next
                </button>
            </div>
        </div>
    </div>

    <ConfirmationModal :isOpen="showClearConfirm" title="Clear All Logs"
        message="Are you sure you want to delete all system logs? This action cannot be undone and you will lose all historical event data."
        confirmText="Yes, Clear Logs" type="danger" :loading="isClearing" @close="showClearConfirm = false"
        @confirm="confirmClearLogs" />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import api from '@/utils/api'
import * as LucideIcons from 'lucide-vue-next'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
const { RefreshCw, Search, Filter, ChevronDown, Activity, Trash2, Cog, ShieldCheck, Router, Network } = LucideIcons
import { useNotifications } from '@/composables/useNotifications'

const { notifySuccess, notifyError } = useNotifications()

interface LogRecord {
    timestamp: string
    level: string
    message: string
    module: string
    funcName: string
    line: number
    path: string
    exception?: string
    // Task Event Fields
    task_type?: string
    event_type?: string
    target?: string
    duration_ms?: number
    details?: Record<string, any>
}

const logs = ref<LogRecord[]>([])
const loading = ref(false)
const limit = ref(20)
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const search = ref('')
const levelFilter = ref('WARNING')
const taskTypeFilter = ref('')
const isRowsOpen = ref(false)
const isLevelOpen = ref(false)
const isTaskTypeOpen = ref(false)
const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

const taskTypes = [
    { value: 'scan', label: 'Network Scan', icon: Network },
    { value: 'adguard_sync', label: 'AdGuard Sync', icon: ShieldCheck },
    { value: 'openwrt_sync', label: 'OpenWRT Sync', icon: Router },
]

// Tab and Auto-refresh State
const currentTab = ref('all')
const autoRefresh = ref(false)
let autoRefreshInterval = null

// Confirmation Modal State
const showClearConfirm = ref(false)
const isClearing = ref(false)

const levelColors: Record<string, string> = {
    'INFO': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    'WARNING': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    'ERROR': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    'CRITICAL': 'bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-100 animate-pulse',
    'DEBUG': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
}

// Task Helper Functions
const getTaskColor = (type?: string) => {
    switch (type) {
        case 'scan': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300'
        case 'adguard_sync': return 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
        case 'openwrt_sync': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300'
        default: return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300'
    }
}

const getTaskIcon = (type?: string) => {
    switch (type) {
        case 'scan': return Network
        case 'adguard_sync': return ShieldCheck
        case 'openwrt_sync': return Router
        default: return Activity
    }
}

const getTaskLabel = (type?: string) => {
    switch (type) {
        case 'scan': return 'Network Scan'
        case 'adguard_sync': return 'AdGuard Sync'
        case 'openwrt_sync': return 'OpenWRT Sync'
        default: return type || 'Unknown'
    }
}

const formatTime = (ts: string) => {
    try {
        return new Date(ts).toLocaleString()
    } catch {
        return ts
    }
}

let debounceTimer: any = null
const debounceSearch = () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
        page.value = 1
        fetchLogs()
    }, 400)
}

const changePage = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages.value) return
    page.value = newPage
    fetchLogs()
    window.scrollTo({ top: 0, behavior: 'smooth' })
}

const fetchLogs = async () => {
    loading.value = true
    try {
        const endpoint = currentTab.value === 'tasks' ? '/task-events/' : '/logs/'
        const params: any = {
            limit: limit.value,
            page: page.value
        }

        if (currentTab.value === 'all') {
            if (search.value) params.search = search.value
            if (levelFilter.value) params.level = levelFilter.value
        } else {
            // Task filtering
            if (taskTypeFilter.value) params.task_type = taskTypeFilter.value
        }

        const res = await api.get(endpoint, { params })

        logs.value = res.data.items
        total.value = res.data.total
        totalPages.value = res.data.total_pages
        page.value = res.data.page
    } catch (e) {
        notifyError('Failed to fetch logs')
        console.error('Error fetching logs:', e)
    } finally {
        loading.value = false
    }
}

const promptClearLogs = () => {
    showClearConfirm.value = true
}

const confirmClearLogs = async () => {
    isClearing.value = true
    try {
        await api.delete('/logs/')
        notifySuccess('All logs cleared successfully')
        logs.value = []
        total.value = 0
        totalPages.value = 1
        page.value = 1
        showClearConfirm.value = false
        // Refresh to ensure empty state
        await fetchLogs()
    } catch (e) {
        notifyError('Failed to clear logs')
        console.error('Error clearing logs:', e)
    } finally {
        isClearing.value = false
    }
}

onMounted(() => {
    fetchLogs()
})

// Computed property for filtered logs based on current tab
// Since API handles filtering, we just return logs
const displayedLogs = computed(() => logs.value)

const displayTotal = computed(() => total.value)

// Auto-refresh watcher
watch(autoRefresh, (enabled) => {
    if (enabled) {
        // Start auto-refresh
        autoRefreshInterval = setInterval(() => {
            if (currentTab.value === 'tasks') {
                fetchLogs()
            }
        }, 5000)
    } else {
        // Stop auto-refresh
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval)
            autoRefreshInterval = null
        }
    }
})

// Stop auto-refresh when switching away from tasks tab
watch(currentTab, (newTab, oldTab) => {
    if (newTab !== 'tasks' && autoRefresh.value) {
        autoRefresh.value = false
    }

    // Reset page and filters when switching tabs
    page.value = 1
    if (newTab === 'tasks') {
        taskTypeFilter.value = ''
    } else {
        levelFilter.value = 'WARNING'
    }

    fetchLogs()
})
</script>
