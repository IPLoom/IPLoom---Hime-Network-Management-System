<template>
    <header class="sticky top-0 z-30 w-full bg-white/80 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-all">
        <div class="px-4 sm:px-6 lg:px-8">
            <div class="flex h-16 items-center justify-between gap-4">
                <!-- Left: Branding -->
                <div class="flex items-center gap-4">
                    <div class="flex items-center gap-2 md:hidden">
                        <button @click="$emit('toggle-mobile-menu')"
                            class="p-2 -ml-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-all">
                            <MenuIcon class="h-6 w-6" />
                        </button>
                    </div>
                    <AppLogo class="scale-100 origin-left" />
                    <div class="hidden lg:block h-6 w-px bg-slate-200 dark:bg-slate-700 mx-2"></div>
                </div>

                <!-- Center: Search Bar -->
                <div class="flex-1 max-w-lg relative group order-last md:order-none w-full md:w-auto"
                    v-click-outside="closeResults">
                    <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                        <SearchIcon class="h-4 w-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                    </div>
                    <input v-model="searchStore.searchQuery" type="text" placeholder="Search devices or activity..."
                        class="block w-full pl-10 pr-12 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-800 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all dark:text-slate-200" 
                        @input="handleInput" @focus="showResults = true"
                        @keyup.enter="goToDevices" />
                    
                    <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                        <kbd class="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 font-sans text-[10px] font-bold text-slate-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md shadow-sm">
                            <span class="text-[8px]">⌘</span>K
                        </kbd>
                    </div>

                    <div v-if="searchStore.searchQuery" class="absolute inset-y-0 right-10 pr-2 flex items-center">
                        <button @click="clearSearch" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
                            <XIcon class="h-4 w-4" />
                        </button>
                    </div>

                    <!-- Search Results -->
                    <transition enter-active-class="transition duration-200 ease-out"
                        enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
                        leave-active-class="transition duration-150 ease-in"
                        leave-from-class="transform scale-100 opacity-100"
                        leave-to-class="transform scale-95 opacity-0">
                        <div v-if="showResults && (searchStore.results.length > 0 || searchStore.isLoading || (searchStore.searchQuery.length >= 2 && !searchStore.isLoading))"
                            class="absolute mt-2 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden z-50">
                            <div v-if="searchStore.isLoading" class="p-6 flex items-center justify-center">
                                <Loader2Icon class="h-5 w-5 text-blue-500 animate-spin" />
                            </div>
                            <div v-else-if="searchStore.results.length > 0" class="py-2">
                                <button v-for="device in searchStore.results" :key="device.id"
                                    @click="goToDevice(device)"
                                    class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-left group/item">
                                    <div class="relative">
                                        <div class="p-2 bg-slate-100 dark:bg-slate-700 rounded-xl group-hover/item:bg-blue-100 dark:group-hover/item:bg-blue-900/40 transition-colors">
                                            <component :is="getIcon(device.icon || 'help-circle')" class="h-4 w-4 text-slate-600 dark:text-slate-400 group-hover/item:text-blue-600 dark:group-hover/item:text-blue-400" />
                                        </div>
                                        <span class="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white dark:border-slate-800" :class="device.status === 'online' ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                                    </div>
                                    <div class="min-w-0 flex-1">
                                        <div class="text-xs font-bold text-slate-900 dark:text-white truncate">{{ device.display_name || 'Unnamed Device' }}</div>
                                        <div class="text-[10px] text-slate-500 font-mono tracking-tight">{{ device.ip }}</div>
                                    </div>
                                </button>
                                <div class="px-2 pt-2 mt-1 border-t border-slate-100 dark:border-slate-700/50">
                                    <button @click="goToDevices" class="w-full py-2 px-4 text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-xl transition-all flex items-center justify-between">
                                        <span>Show all results</span>
                                        <ArrowRightIcon class="h-3 w-3" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </transition>
                </div>

                <!-- Right: Actions -->
                <div class="flex items-center gap-3">
                    <!-- Integrations Status -->
                    <div class="hidden lg:flex items-center gap-1.5 p-1 bg-slate-50/80 dark:bg-slate-800/50 rounded-xl border border-slate-200/50 dark:border-slate-700/30">
                        <div v-for="integration in ['mqtt', 'openwrt', 'adguard']" :key="integration" 
                            @click="router.push('/settings')"
                            class="group relative flex items-center h-9 w-9 justify-center cursor-pointer hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-all shadow-sm shadow-transparent hover:shadow-slate-200/50">
                            <component :is="integration === 'mqtt' ? Share2Icon : (integration === 'openwrt' ? RouterIcon : ShieldCheckIcon)" 
                                class="h-4 w-4 transition-colors" 
                                :class="getIntegrationStatus(integration) ? getIntegrationColor(integration) : 'text-slate-400'" />
                            <div v-if="getIntegrationStatus(integration)" 
                                class="absolute top-1.5 right-1.5 h-2 w-2 rounded-full border-2 border-white dark:border-slate-800"
                                :class="getIntegrationPulse(integration)"></div>
                            
                            <!-- Tooltip -->
                            <div class="pointer-events-none opacity-0 group-hover:opacity-100 transition-all duration-200 absolute -bottom-12 left-1/2 -translate-x-1/2 z-50 bg-slate-900 dark:bg-slate-800 text-white text-[10px] py-2 px-3 rounded-xl shadow-2xl border border-slate-700 flex flex-col gap-0.5">
                                <div class="flex items-center gap-1.5">
                                    <div class="w-1.5 h-1.5 rounded-full" :class="getIntegrationStatus(integration) ? 'bg-emerald-500' : 'bg-red-500'"></div>
                                    <span class="font-bold">{{ integration.toUpperCase() }} {{ getIntegrationStatus(integration) ? 'Active' : 'Offline' }}</span>
                                </div>
                                <span class="text-slate-400 italic whitespace-nowrap">Manage in Settings</span>
                            </div>
                        </div>
                    </div>

                    <!-- System Hub: Live & Notifications -->
                    <div class="flex items-center gap-1.5 p-1 bg-slate-50/80 dark:bg-slate-800/50 rounded-xl border border-slate-200/50 dark:border-slate-700/30">
                        <div class="hidden sm:flex items-center gap-1.5 px-3 h-9 rounded-lg border transition-colors duration-500"
                            :class="ws.connected.value ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-600 dark:text-red-400'">
                            <Zap class="w-3.5 h-3.5" :class="{ 'animate-pulse': ws.connected.value }" />
                            <span class="text-[10px] font-black uppercase tracking-widest">{{ ws.connected.value ? 'Live' : 'Offline' }}</span>
                        </div>

                        <div class="w-px h-4 bg-slate-200 dark:bg-slate-700 mx-0.5 hidden sm:block"></div>

                        <div class="relative" v-click-outside="() => showNotifications = false">
                            <button @click="toggleNotifications"
                                class="h-9 w-9 flex items-center justify-center text-slate-500 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-all relative shadow-sm shadow-transparent hover:shadow-slate-200/50">
                                <BellIcon class="h-5 w-5" />
                                <span v-if="notificationStore.unreadCount > 0" class="absolute top-2 right-2 flex h-2 w-2">
                                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                    <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500 border border-white dark:border-slate-900"></span>
                                </span>
                            </button>

                            <!-- Notifications Dropdown -->
                            <transition enter-active-class="transition duration-200 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-150 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                                <div v-if="showNotifications" class="absolute right-0 mt-3 w-80 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden z-50">
                                    <div class="px-4 py-3 border-b border-slate-100 dark:border-slate-700/50 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
                                        <h3 class="text-xs font-black uppercase tracking-widest text-slate-900 dark:text-white">Recent Activity</h3>
                                        <button @click="markAllAsRead" class="text-[10px] font-bold text-blue-600 dark:text-blue-400 hover:underline">Clear all</button>
                                    </div>
                                    <div class="max-h-96 overflow-y-auto custom-scrollbar">
                                        <div v-if="notificationStore.events.length === 0" class="p-10 text-center text-slate-500 text-[10px] font-medium">All caught up!</div>
                                        <button v-for="event in notificationStore.events" :key="event.id" @click="goToEvent(event)" class="notif-item group/notif">
                                            <div v-if="!event.read_at" class="notif-indicator"></div>
                                            <div class="p-2 rounded-xl" :class="getEventColor(event.level)"><component :is="getEventIcon(event)" class="h-4 w-4" /></div>
                                            <div class="flex-1 min-w-0">
                                                <div class="flex items-center justify-between gap-2">
                                                    <span class="text-[10px] font-black uppercase tracking-tighter text-slate-400">{{ event.task_type?.replace('_', ' ') || 'System' }}</span>
                                                    <span class="text-[9px] text-slate-400">{{ formatRelativeTime(parseUTC(event.created_at)) }}</span>
                                                </div>
                                                <p class="text-xs font-medium text-slate-900 dark:text-slate-100 line-clamp-2 mt-0.5 leading-snug">{{ event.message }}</p>
                                            </div>
                                        </button>
                                    </div>
                                    <div class="p-2 border-t border-slate-100 dark:border-slate-700/50">
                                        <router-link to="/logs" @click="showNotifications = false" class="w-full py-2 px-4 text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-xl transition-all flex items-center justify-between">
                                            <span>View all events</span>
                                            <ArrowRightIcon class="h-3 w-3" />
                                        </router-link>
                                    </div>
                                </div>
                            </transition>
                        </div>
                    </div>

                    <!-- User Profile -->
                    <div class="relative" v-click-outside="() => showUserMenu = false">
                        <button @click="showUserMenu = !showUserMenu" class="flex items-center gap-2 h-11 pl-1 pr-3 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all relative group">
                            <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white text-[11px] font-bold shadow-sm group-hover:scale-105 transition-transform">
                                {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
                            </div>
                            <span class="hidden sm:block text-xs font-bold text-slate-700 dark:text-slate-300">{{ authStore.user?.username || 'User' }}</span>
                            <ChevronDownIcon class="h-3 w-3 text-slate-400 transition-transform duration-200" :class="showUserMenu ? 'rotate-180' : ''" />
                        </button>
                        <transition enter-active-class="transition duration-200 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-150 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                            <div v-if="showUserMenu" class="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden z-50">
                                <div class="px-4 py-4 bg-slate-50 dark:bg-slate-800/30 border-b border-slate-100 dark:border-slate-700/50">
                                    <p class="text-xs font-black uppercase tracking-tight text-slate-900 dark:text-white">{{ authStore.user?.full_name || authStore.user?.username }}</p>
                                    <p class="text-[10px] text-slate-500 truncate mt-0.5">System Administrator</p>
                                </div>
                                <div class="p-1.5">
                                    <router-link to="/settings" @click="showUserMenu = false" class="user-menu-item rounded-xl">
                                        <UserIcon class="h-4 w-4" />
                                        <span>Profile Settings</span>
                                    </router-link>
                                    <button @click="handleLogout" class="user-menu-item rounded-xl text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 w-full text-left mt-1">
                                        <LogOutIcon class="h-4 w-4" />
                                        <span>Sign Out</span>
                                    </button>
                                </div>
                            </div>
                        </transition>
                    </div>
                </div>
            </div>
        </div>
    </header>
</template>

<script setup>
import {
    Search as SearchIcon,
    X as XIcon,
    Bell as BellIcon,
    Menu as MenuIcon,
    Loader2 as Loader2Icon,
    ArrowRight as ArrowRightIcon,
    HelpCircle,
    Smartphone,
    Tablet,
    Laptop,
    Monitor,
    Server,
    Router,
    Network,
    Wifi,
    WifiOff,
    User as UserIcon,
    LogOut as LogOutIcon,
    ChevronDown as ChevronDownIcon,
    Tv,
    Printer,
    Activity,
    CheckCircle,
    AlertTriangle,
    ShieldAlert,
    ScanSearch,
    Zap,
    Share2 as Share2Icon,
    Router as RouterIcon,
    ShieldCheck as ShieldCheckIcon
} from 'lucide-vue-next'
import { useNotifications } from '@/composables/useNotifications'
import { ref, onMounted } from 'vue'
import AppLogo from './AppLogo.vue'
import { useSearchStore } from '@/stores/search'
import { useNotificationStore } from '@/stores/notifications'
import { useIntegrationStore } from '@/stores/integrations'
import { useAuthStore } from '@/stores/authStore'
import { useRouter } from 'vue-router'
import { formatRelativeTime, parseUTC } from '@/utils/date'
import { useWebSockets } from '@/composables/useWebSockets'

defineEmits(['toggle-mobile-menu'])

const searchStore = useSearchStore()
const notificationStore = useNotificationStore()
const integrationStore = useIntegrationStore()
const authStore = useAuthStore()
const router = useRouter()
const ws = useWebSockets()

const showResults = ref(false)
const showNotifications = ref(false)
const showUserMenu = ref(false)

onMounted(() => {
    notificationStore.fetchNotifications(true)
    notificationStore.fetchUnreadCount()
    integrationStore.fetchStatuses()
})

const getIntegrationStatus = (key) => {
    if (key === 'mqtt') return integrationStore.mqttStatus.reachable
    if (key === 'openwrt') return integrationStore.openwrtStatus.verified
    if (key === 'adguard') return integrationStore.adguardStatus.verified
    return false
}

const getIntegrationColor = (key) => {
    if (key === 'mqtt') return 'text-emerald-500'
    if (key === 'openwrt') return 'text-blue-500'
    if (key === 'adguard') return 'text-indigo-500'
    return 'text-slate-400'
}

const getIntegrationPulse = (key) => {
    const base = 'absolute top-1.5 right-1.5 h-2 w-2 rounded-full border-2 border-white dark:border-slate-800 shadow-sm'
    if (key === 'mqtt') return `${base} bg-emerald-500 animate-pulse`
    if (key === 'openwrt') return `${base} bg-blue-500`
    if (key === 'adguard') return `${base} bg-indigo-500`
    return base
}

const getEventIcon = (event) => {
    if (event.level === 'ERROR' || event.event_type === 'failed') return AlertTriangle
    if (event.level === 'WARNING') return AlertTriangle
    if (event.task_type === 'audit') return ScanSearch
    if (event.event_type === 'completed') return CheckCircle
    if (event.event_type === 'security_alert') return ShieldAlert
    if (event.type === 'device') return event.event_type === 'status_changed' && event.message.includes('online') ? Wifi : WifiOff
    return Activity
}

const getEventColor = (level) => {
    if (level === 'ERROR') return 'bg-red-500/10 text-red-500'
    if (level === 'WARNING') return 'bg-amber-500/10 text-amber-500'
    return 'bg-blue-500/10 text-blue-500'
}

const toggleNotifications = () => {
    showNotifications.value = !showNotifications.value
    if (showNotifications.value) {
        showResults.value = false
        showUserMenu.value = false
        notificationStore.fetchNotifications(true)
        notificationStore.fetchUnreadCount()
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

const markAllAsRead = async () => {
    await notificationStore.markAllAsRead()
    const { notifySuccess } = useNotifications()
    notifySuccess('All notifications marked as read')
}

const goToEvent = async (event) => {
    showNotifications.value = false
    if (!event.read_at) {
        try {
            await notificationStore.markAsRead([event.id])
        } catch (error) {
            console.error('Failed to mark notification as read:', error)
        }
    }
    const deviceId = event.type === 'device' ? (event.target || event.details?.id) : null
    if (deviceId && deviceId.length > 10) {
        router.push({ name: 'DeviceDetails', params: { id: deviceId } })
    } else if (event.task_type === 'scan') {
        router.push('/logs')
    } else if (event.task_type === 'adguard_sync' || event.task_type === 'openwrt_sync') {
        router.push('/analytics')
    }
}

const vClickOutside = {
    mounted(el, binding) {
        el._clickOutside = (event) => {
            if (!(el === event.target || el.contains(event.target))) {
                binding.value(event)
            }
        }
        document.addEventListener('click', el._clickOutside)
    },
    unmounted(el) {
        document.removeEventListener('click', el._clickOutside)
    }
}

const handleInput = (event) => {
    const val = event.target.value
    searchStore.setSearchQuery(val)
    showResults.value = true
}

const closeResults = () => {
    showResults.value = false
}

const clearSearch = () => {
    searchStore.searchQuery = ''
    searchStore.results = []
}

const goToDevice = (device) => {
    showResults.value = false
    router.push({ name: 'DeviceDetails', params: { id: device.id } })
}

const goToDevices = () => {
    showResults.value = false
    router.push('/devices')
}

const getIcon = (name) => {
    const iconMap = {
        'smartphone': Smartphone,
        'tablet': Tablet,
        'laptop': Laptop,
        'monitor': Monitor,
        'server': Server,
        'router': Router,
        'network': Network,
        'tv': Tv,
        'printer': Printer,
        'help-circle': HelpCircle
    }
    const key = name.toLowerCase().replace('device-', '')
    return iconMap[key] || HelpCircle
}
</script>
