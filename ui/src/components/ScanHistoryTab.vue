<template>
    <div class="space-y-6">
        <!-- Quick Stats -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div v-for="stat in historyStats" :key="stat.label" class="card-stat group">
                <!-- Sparkline Background -->
                <Sparkline :data="stat.trend" :color="stat.color" class="opacity-15" />

                <!-- Header Row -->
                <div class="relative z-10 flex items-center justify-between w-full">
                    <div :class="[stat.bgClass, 'p-1.5 rounded-lg shadow-sm border border-white/10']">
                        <component :is="stat.icon" class="h-4 w-4" />
                    </div>
                    <div v-if="stat.change" class="badge-pill">
                        <span
                            :class="[stat.changeType === 'down' ? 'text-rose-500' : 'text-emerald-600', 'text-[10px] font-bold']">
                            {{ stat.change }}
                        </span>
                    </div>
                </div>

                <!-- Center Content -->
                <div class="relative z-10 flex flex-col items-center text-center -mt-1">
                    <p class="heading-xl">
                        {{ stat.value }}
                    </p>
                    <p :class="stat.textColor" class="subtext-caps">
                        {{ stat.label }}
                    </p>
                </div>
            </div>
        </div>

        <!-- Scans Table -->
        <div class="content-panel">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead class="bg-slate-50 dark:bg-slate-900/50">
                        <tr>
                            <th class="table-header-cell">Status</th>
                            <th class="table-header-cell">Target</th>
                            <th class="hidden md:table-cell table-header-cell">Type</th>
                            <th class="hidden md:table-cell table-header-cell">Started</th>
                            <th class="hidden md:table-cell table-header-cell text-center">Devices</th>
                            <th class="table-header-cell text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-200 dark:border-slate-700">
                        <template v-for="scan in scans" :key="scan.id">
                            <tr class="hover-row">
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-2">
                                        <component :is="getStatusIcon(scan.status)"
                                            :class="[statusClass(scan.status), 'w-5 h-5']" />
                                    </div>
                                </td>
                                <td class="px-6 py-4">
                                    <div class="text-sm font-medium text-slate-900 dark:text-white truncate max-w-[200px]">
                                        {{ scan.target }}</div>
                                    <div class="text-xs text-slate-500 font-mono">{{ scan.id.split('-')[0] }}...</div>
                                </td>
                                <td class="hidden md:table-cell table-data-cell">{{ scan.scan_type }}</td>
                                <td class="hidden md:table-cell table-data-cell text-center font-mono">
                                    <div class="text-sm text-slate-600 dark:text-slate-400">{{ formatDate(scan.started_at ||
                                        scan.created_at) }}</div>
                                    <div v-if="scan.finished_at" class="text-xs text-slate-500">{{ getDuration(scan) }}</div>
                                </td>
                                <td class="hidden md:table-cell px-6 py-4 text-center">
                                    <span class="text-sm font-medium text-slate-900 dark:text-white">{{
                                        resultsCount[scan.id] !== undefined ? resultsCount[scan.id] : '...' }}</span>
                                </td>
                                <td class="table-data-cell text-right">
                                    <div class="flex items-center justify-end gap-1">
                                        <button v-if="['queued', 'running'].includes(scan.status)"
                                            @click="cancelScan(scan.id)"
                                            class="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                                            v-tooltip="'Cancel Scan'">
                                            <X class="w-4 h-4" />
                                        </button>
                                        <button @click="toggleExpand(scan.id)"
                                            class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all"
                                            v-tooltip="expandedIds.has(scan.id) ? 'Collapse Details' : 'View Details'">
                                            <component :is="expandedIds.has(scan.id) ? ChevronUp : ChevronDown"
                                                class="w-4 h-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            <!-- Expanded Area -->
                            <tr v-if="expandedIds.has(scan.id)">
                                <td colspan="6" class="px-6 py-4 bg-slate-50 dark:bg-slate-900/20">
                                    <!-- Mobile Details Section -->
                                    <div
                                        class="md:hidden grid grid-cols-2 gap-4 mb-4 pb-4 border-b border-slate-200 dark:border-slate-700">
                                        <div class="space-y-1">
                                            <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Type</p>
                                            <p class="text-sm text-slate-700 dark:text-slate-300">{{ scan.scan_type }}</p>
                                        </div>
                                        <div class="space-y-1">
                                            <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Devices
                                                Found</p>
                                            <p class="text-sm font-medium text-slate-900 dark:text-white">{{
                                                resultsCount[scan.id] !== undefined ? resultsCount[scan.id] : '...' }}</p>
                                        </div>
                                        <div class="space-y-1">
                                            <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Started
                                            </p>
                                            <p class="text-sm text-slate-600 dark:text-slate-400">{{
                                                formatDate(scan.started_at || scan.created_at) }}</p>
                                        </div>
                                        <div class="space-y-1">
                                            <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Duration
                                            </p>
                                            <p class="text-sm text-slate-500">{{ getDuration(scan) || '-' }}</p>
                                        </div>
                                    </div>

                                    <div v-if="loadingResults[scan.id]"
                                        class="flex items-center justify-center py-8 text-slate-500">
                                        <div
                                            class="w-5 h-5 border-2 border-slate-300 border-t-blue-600 rounded-full animate-spin mr-3">
                                        </div>
                                        <span class="text-sm">Loading results...</span>
                                    </div>
                                    <div v-else-if="scanResults[scan.id]?.length > 0"
                                        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                        <div v-for="res in scanResults[scan.id]" :key="res.id"
                                            class="flex items-center gap-3 p-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 hover:shadow-sm transition-shadow cursor-pointer"
                                            @click="$router.push(`/devices/${res.id}`)">
                                            <div class="flex-1 min-w-0">
                                                <div class="text-sm font-medium text-slate-900 dark:text-white truncate">{{
                                                    res.hostname || res.ip }}</div>
                                                <div class="text-xs text-slate-500 font-mono truncate">{{ res.mac ||
                                                    'Unknown MAC' }}</div>
                                            </div>
                                            <div class="text-xs font-medium text-slate-500 dark:text-slate-400">{{
                                                res.open_ports?.length || 0 }}p</div>
                                        </div>
                                    </div>
                                    <div v-else class="py-8 text-center">
                                        <div class="text-sm text-slate-500">No devices found</div>
                                    </div>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex justify-center items-center gap-2">
            <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1" class="pagination-btn">
                Previous
            </button>
            <div class="px-4 py-2 bg-slate-900 dark:bg-white rounded-lg text-sm font-medium text-white dark:text-slate-900">
                {{ currentPage }} / {{ totalPages }}
            </div>
            <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages" class="pagination-btn">
                Next
            </button>
        </div>

        <!-- Confirmation Modal -->
        <div v-if="confirmModal.isOpen" class="fixed inset-0 z-[100] overflow-y-auto" @click.self="closeConfirmation">
            <div class="flex min-h-screen items-center justify-center p-4">
                <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="closeConfirmation">
                </div>
                <div class="modal-feedback-card max-w-sm w-full relative z-10">
                    <div class="flex flex-col items-center text-center">
                        <div class="h-12 w-12 rounded-full flex items-center justify-center mb-4"
                            :class="confirmModal.type === 'delete' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-blue-100 dark:bg-blue-900/30'">
                            <component :is="confirmModal.type === 'delete' ? Trash2 : AlertTriangle" class="h-6 w-6"
                                :class="confirmModal.type === 'delete' ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'" />
                        </div>
                        <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ confirmModal.title }}</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
                            {{ confirmModal.message }}
                        </p>
                        <div class="flex flex-col sm:flex-row gap-2 w-full">
                            <button @click="confirmAction"
                                class="flex-1 px-4 py-2.5 text-white rounded-lg text-sm font-bold shadow-lg transition-all active:scale-95"
                                :class="confirmModal.confirmClass">
                                {{ confirmModal.confirmText }}
                            </button>
                            <button @click="closeConfirmation"
                                class="flex-1 px-4 py-2.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg text-sm font-bold hover:bg-slate-200 dark:hover:bg-slate-600 transition-all active:scale-95">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive, computed, defineExpose } from 'vue'
import api from '@/utils/api'
import Sparkline from '@/components/Sparkline.vue'
import { Trash2, RefreshCw, CheckCircle, AlertTriangle, Clock, ChevronDown, ChevronUp, Activity, Smartphone, Server as ServerIcon, Scan, X, Search } from 'lucide-vue-next'
import { formatDate, formatRelativeTime, parseUTC } from '@/utils/date'
import { useNotifications } from '@/composables/useNotifications'

const { notifySuccess, notifyError } = useNotifications()

const scans = ref([])
const isRefreshing = ref(false)
const isScanning = ref(false)
const expandedIds = ref(new Set())
const scanResults = reactive({})
const loadingResults = reactive({})
const resultsCount = reactive({})
const currentPage = ref(1)
const totalPages = ref(1)
const limit = ref(10)
const pendingActionId = ref(null)

// Confirmation Modal State
const confirmModal = reactive({
    isOpen: false,
    type: '', // 'delete' or 'clear_queue'
    title: '',
    message: '',
    confirmText: '',
    confirmClass: ''
})

const runDiscovery = async () => {
    if (isScanning.value) return
    isScanning.value = true
    try {
        await api.post('/scans/discovery')
        notifySuccess('Discovery scan enqueued')
        await fetchScans()
    } catch (e) {
        notifyError('Failed to start discovery')
    } finally {
        isScanning.value = false
    }
}

const fetchScans = async () => {
    isRefreshing.value = true
    try {
        const res = await api.get('/scans/', {
            params: { page: currentPage.value, limit: limit.value }
        })
        scans.value = res.data.items || []
        totalPages.value = res.data.total_pages || 1
        currentPage.value = res.data.page || 1
        scans.value.forEach(scan => {
            if (scan.status === 'done' && resultsCount[scan.id] === undefined) {
                fetchCount(scan.id)
            }
        })
    } catch (e) {
        notifyError('Failed to load scan history')
    } finally {
        setTimeout(() => {
            isRefreshing.value = false
        }, 500)
    }
}

const changePage = (page) => {
    if (page < 1 || page > totalPages.value) return
    currentPage.value = page
    fetchScans()
}

const clearQueue = async () => {
    openConfirmation('clear_queue')
}

const cancelScan = async (id) => {
    try {
        await api.delete(`/scans/${id}`)
        await fetchScans()
        notifySuccess('Scan canceled')
    } catch (e) {
        notifyError('Failed to cancel scan')
    }
}

const openConfirmation = (type) => {
    confirmModal.type = type
    confirmModal.isOpen = true

    if (type === 'delete') {
        confirmModal.title = 'Cancel Scan?'
        confirmModal.message = 'Are you sure you want to cancel this scan? It will be marked as interrupted in your history.'
        confirmModal.confirmText = 'Yes, Cancel Scan'
        confirmModal.confirmClass = 'bg-red-600 hover:bg-red-700 focus:ring-red-500 shadow-red-500/20'
    } else if (type === 'clear_queue') {
        confirmModal.title = 'Cancel Pending?'
        confirmModal.message = 'This will mark all currently queued scans as cancelled.'
        confirmModal.confirmText = 'Cancel All Queued'
        confirmModal.confirmClass = 'bg-orange-600 hover:bg-orange-700 focus:ring-orange-500 shadow-orange-500/20'
    }
}

const closeConfirmation = () => {
    confirmModal.isOpen = false
    pendingActionId.value = null
}

const confirmAction = async () => {
    const type = confirmModal.type
    const id = pendingActionId.value
    closeConfirmation()

    try {
        if (type === 'delete') {
            await api.delete(`/scans/${id}`)
            notifySuccess('Record deleted')
        } else if (type === 'clear_queue') {
            await api.delete('/scans/queue')
            notifySuccess('Queue cleared')
        }
        await fetchScans()
    } catch (e) {
        notifyError(`Action failed: ${e.message}`)
    }
}

const fetchCount = async (id) => {
    try {
        const res = await api.get(`/scans/${id}/results`)
        resultsCount[id] = res.data.length
    } catch (e) {
        console.error(e)
    }
}

const toggleExpand = async (id) => {
    if (expandedIds.value.has(id)) {
        expandedIds.value.delete(id)
    } else {
        expandedIds.value.add(id)
        if (!scanResults[id]) {
            await fetchResults(id)
        }
    }
}

const historyStats = computed(() => {
    const total = scans.value.length
    const doneScans = scans.value.filter(s => s.status === 'done')
    const successRate = total > 0 ? Math.round((doneScans.length / total) * 100) : 0

    let totalDuration = 0
    let count = 0
    doneScans.forEach(s => {
        if (s.started_at && s.finished_at) {
            const start = parseUTC(s.started_at)
            const end = parseUTC(s.finished_at)
            totalDuration += end.diff(start).as('milliseconds')
            count++
        }
    })
    const avgDurationSeconds = count > 0 ? Math.round(totalDuration / count / 1000) : 0
    const avgDuration = avgDurationSeconds < 60 ? `${avgDurationSeconds}s` : `${Math.floor(avgDurationSeconds / 60)}m`

    return [
        {
            label: 'Total Scans',
            value: total > 0 ? total + '+' : 0,
            icon: Activity,
            color: '#3b82f6',
            textColor: 'text-blue-500',
            bgClass: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
            trend: [5, 4, 6, 5, 7, 6, 8, 7, 9, 8],
            change: 'All Time',
            changeType: 'up'
        },
        {
            label: 'Success Rate',
            value: `${successRate}%`,
            icon: CheckCircle,
            color: '#10b981',
            textColor: 'text-emerald-500',
            bgClass: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
            trend: [95, 98, 96, 99, 97, 100, 98, 99, 97, 100],
            change: 'Reliability',
            changeType: 'up'
        },
        {
            label: 'Avg Duration',
            value: avgDuration,
            icon: Clock,
            color: '#8b5cf6',
            textColor: 'text-violet-500',
            bgClass: 'bg-violet-100 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400',
            trend: [45, 42, 44, 40, 43, 41, 39, 40, 38, 35],
            change: 'Performance',
            changeType: 'down'
        }
    ]
})

const fetchResults = async (id) => {
    loadingResults[id] = true
    try {
        const res = await api.get(`/scans/${id}/results`)
        scanResults[id] = res.data
        resultsCount[id] = res.data.length
    } catch (e) {
        console.error(e)
    } finally {
        loadingResults[id] = false
    }
}

const getStatusIcon = (s) => {
    switch (s) {
        case 'done': return CheckCircle
        case 'running': return RefreshCw
        case 'queued': return Clock
        case 'interrupted': return X
        case 'error': return AlertTriangle
        default: return Clock
    }
}

const statusClass = (s) => {
    switch (s) {
        case 'done': return 'text-emerald-500 dark:text-emerald-400'
        case 'running': return 'text-blue-500 dark:text-blue-400 animate-spin'
        case 'queued': return 'text-slate-400 dark:text-slate-500'
        case 'interrupted': return 'text-orange-500 dark:text-orange-400'
        case 'error': return 'text-red-500 dark:text-red-400'
        default: return 'text-slate-400'
    }
}

const getDuration = (scan) => {
    if (!scan.started_at || !scan.finished_at) return ''
    const start = parseUTC(scan.started_at)
    const end = parseUTC(scan.finished_at)
    const diff = Math.round(end.diff(start, 'seconds').seconds)
    if (diff < 60) return `${diff}s`
    return `${Math.floor(diff / 60)}m ${diff % 60}s`
}

let pollInterval = null

onMounted(() => {
    fetchScans()
    pollInterval = setInterval(fetchScans, 10000)
})

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval)
})

defineExpose({
    runDiscovery,
    clearQueue,
    fetchScans,
    isRefreshing,
    isScanning
})
</script>
