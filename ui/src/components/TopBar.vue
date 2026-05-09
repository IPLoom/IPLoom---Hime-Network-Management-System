<template>
    <header
        class="sticky top-0 z-30 w-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div class="px-4 sm:px-6 lg:px-8">
            <div class="flex h-16 items-center justify-between gap-4">
                <!-- Left: Branding & Mobile Menu Trigger -->
                <div class="flex items-center gap-4">
                    <div class="flex items-center gap-2 md:hidden">
                        <button @click="$emit('toggle-mobile-menu')"
                            class="p-2 -ml-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300">
                            <MenuIcon class="h-6 w-6" />
                        </button>
                    </div>
                    <AppLogo class="scale-90 origin-left" />
                    <!-- Vertical Divider for Desktop -->
                    <div class="hidden md:block h-6 w-px bg-slate-200 dark:bg-slate-700 mx-2"></div>
                </div>

                <!-- Center: Search Bar (Responsive) -->
                <div class="flex-1 max-w-lg relative group order-last md:order-none w-full md:w-auto mt-0"
                    v-click-outside="closeResults">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <SearchIcon class="h-4 w-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                    </div>
                    <input v-model="searchStore.searchQuery" type="text" placeholder="Search devices..."
                        class="search-input-pill" @input="handleInput" @focus="showResults = true"
                        @keyup.enter="goToDevices" />
                    <div v-if="searchStore.searchQuery" class="absolute inset-y-0 right-0 pr-3 flex items-center">
                        <button @click="clearSearch"
                            class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                            <XIcon class="h-4 w-4" />
                        </button>
                    </div>

                    <!-- Search Results Dropdown -->
                    <transition enter-active-class="transition duration-200 ease-out"
                        enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
                        leave-active-class="transition duration-150 ease-in"
                        leave-from-class="transform scale-100 opacity-100"
                        leave-to-class="transform scale-95 opacity-0">
                        <div v-if="showResults && (searchStore.results.length > 0 || searchStore.isLoading || (searchStore.searchQuery.length >= 2 && !searchStore.isLoading))"
                            class="absolute mt-2 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">

                            <div v-if="searchStore.isLoading" class="p-4 flex items-center justify-center">
                                <Loader2Icon class="h-5 w-5 text-blue-500 animate-spin" />
                            </div>

                            <div v-else-if="searchStore.results.length > 0" class="py-2">
                                <button v-for="device in searchStore.results" :key="device.id"
                                    @click="goToDevice(device)"
                                    class="w-full flex items-center gap-3 px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-left">
                                    <div class="relative">
                                        <div class="p-1.5 bg-slate-100 dark:bg-slate-600 rounded-lg">
                                            <component :is="getIcon(device.icon || 'help-circle')"
                                                class="h-4 w-4 text-slate-600 dark:text-slate-400" />
                                        </div>
                                        <span
                                            class="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full border border-white dark:border-slate-800"
                                            :class="device.status === 'online' ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                                    </div>
                                    <div class="min-w-0">
                                        <div class="text-sm font-medium text-slate-900 dark:text-white truncate">
                                            {{ device.display_name || 'Unnamed Device' }}
                                        </div>
                                        <div class="text-[11px] text-slate-500 font-mono">{{ device.ip }}</div>
                                    </div>
                                </button>

                                <div class="px-2 pt-2 border-t border-slate-100 dark:border-slate-700">
                                    <button @click="goToDevices"
                                        class="w-full py-2 px-4 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-lg transition-colors flex items-center justify-between">
                                        <span>View all results</span>
                                        <ArrowRightIcon class="h-3 w-3" />
                                    </button>
                                </div>
                            </div>

                            <div v-else-if="searchStore.searchQuery.length >= 2"
                                class="p-8 text-center bg-slate-50/50 dark:bg-slate-800/50">
                                <div class="icon-box-lg">
                                    <SearchIcon class="h-6 w-6 text-slate-400" />
                                </div>
                                <p class="text-sm text-slate-900 dark:text-slate-100 font-medium">No matching devices
                                    found</p>
                                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Try searching with a
                                    different name or IP</p>
                            </div>
                        </div>
                    </transition>
                </div>

                <!-- Right: Actions -->
                <div class="flex items-center gap-2">
                    <!-- Quick Status (Hidden on Mobile) -->
                    <div class="hidden lg:flex badge-live-label">
                        <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                        <span>Live</span>
                    </div>

                    <div class="relative" v-click-outside="() => showNotifications = false">
                        <button @click="toggleNotifications"
                            class="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors relative">
                            <BellIcon class="h-5 w-5" />
                            <span v-if="notificationStore.unreadCount > 0" class="absolute top-2 right-2 flex h-2 w-2">
                                <span
                                    class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                <span
                                    class="relative inline-flex rounded-full h-2 w-2 bg-blue-500 border border-white dark:border-slate-900"></span>
                            </span>
                        </button>

                        <!-- Notifications Dropdown -->
                        <transition enter-active-class="transition duration-200 ease-out"
                            enter-from-class="transform scale-95 opacity-0"
                            enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-150 ease-in"
                            leave-from-class="transform scale-100 opacity-100"
                            leave-to-class="transform scale-95 opacity-0">
                            <div v-if="showNotifications"
                                class="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">
                                <div
                                    class="px-4 py-3 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
                                    <h3 class="text-sm font-bold text-slate-900 dark:text-white">Recent Activity</h3>
                                    <button @click="markAllAsRead"
                                        class="text-[10px] font-bold text-blue-600 dark:text-blue-400 hover:underline">
                                        Mark all as read
                                    </button>
                                </div>

                                <div class="max-h-96 overflow-y-auto">
                                    <div v-if="notificationStore.isLoading && notificationStore.events.length === 0"
                                        class="p-8 flex justify-center">
                                        <Loader2Icon class="h-6 w-6 text-blue-500 animate-spin" />
                                    </div>
                                    <div v-else-if="notificationStore.events.length === 0"
                                        class="p-8 text-center text-slate-500 dark:text-slate-400 text-xs">
                                        No recent activity
                                    </div>
                                    <div v-else>
                                        <button v-for="event in notificationStore.events" :key="event.id"
                                            @click="goToEvent(event)" class="notif-item">
                                            <div v-if="new Date(event.changed_at) > new Date(notificationStore.lastViewed)"
                                                class="notif-indicator">
                                            </div>
                                            <div class="flex-shrink-0">
                                                <div :class="event.status === 'online' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'"
                                                    class="p-2 rounded-lg">
                                                    <component :is="event.status === 'online' ? WifiIcon : WifiOffIcon"
                                                        class="h-4 w-4" />
                                                </div>
                                            </div>
                                            <div class="min-w-0">
                                                <p
                                                    class="text-[11px] font-medium text-slate-900 dark:text-white leading-tight">
                                                    <span class="font-bold">{{ event.display_name || event.ip }}</span>
                                                    {{ event.status === 'online' ? 'joined the network' : 'disconnected'
                                                    }}
                                                </p>
                                                <p class="text-[9px] text-slate-500 mt-1">{{
                                                    formatRelativeTime(event.changed_at) }}</p>
                                            </div>
                                        </button>
                                    </div>
                                </div>

                                <div class="px-2 py-2 border-t border-slate-100 dark:border-slate-700">
                                    <router-link to="/events" @click="showNotifications = false"
                                        class="w-full py-2 px-4 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-lg transition-colors flex items-center justify-center gap-2">
                                        <span>View all events</span>
                                        <ArrowRightIcon class="h-3 w-3" />
                                    </router-link>
                                </div>
                            </div>
                        </transition>
                    </div>

                    <!-- User Profile Dropdown -->
                    <div class="relative ml-1" v-click-outside="() => showUserMenu = false">
                        <button @click="showUserMenu = !showUserMenu"
                            class="flex items-center gap-2 p-1 pl-1 pr-3 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-all border border-transparent hover:border-slate-200 dark:hover:border-slate-700">
                            <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
                                {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
                            </div>
                            <span class="hidden sm:block text-xs font-semibold text-slate-700 dark:text-slate-300">
                                {{ authStore.user?.username || 'User' }}
                            </span>
                            <ChevronDownIcon class="h-3 w-3 text-slate-400 transition-transform duration-200" :class="showUserMenu ? 'rotate-180' : ''" />
                        </button>

                        <!-- User Menu Dropdown -->
                        <transition enter-active-class="transition duration-200 ease-out"
                            enter-from-class="transform scale-95 opacity-0"
                            enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-150 ease-in"
                            leave-from-class="transform scale-100 opacity-100"
                            leave-to-class="transform scale-95 opacity-0">
                            <div v-if="showUserMenu"
                                class="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">
                                <div class="px-4 py-4 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-700">
                                    <p class="text-sm font-bold text-slate-900 dark:text-white truncate">{{ authStore.user?.full_name || authStore.user?.username }}</p>
                                    <p class="text-[10px] text-slate-500 truncate mt-0.5">{{ authStore.user?.region ? 'Region: ' + authStore.user.region : 'Administrator' }}</p>
                                </div>
                                
                                <div class="py-1">
                                    <router-link to="/settings" @click="showUserMenu = false" class="user-menu-item">
                                        <UserIcon class="h-4 w-4" />
                                        <span>Profile Settings</span>
                                    </router-link>
                                    <button @click="handleLogout" class="user-menu-item text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 w-full text-left">
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
    ChevronDown as ChevronDownIcon
} from 'lucide-vue-next'
import { ref, onMounted, onUnmounted } from 'vue'
import AppLogo from './AppLogo.vue'
import { useSearchStore } from '@/stores/search'
import { useNotificationStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/authStore'
import { useRouter } from 'vue-router'
import { formatRelativeTime } from '@/utils/date'

defineEmits(['toggle-mobile-menu'])

const searchStore = useSearchStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const router = useRouter()
const showResults = ref(false)
const showNotifications = ref(false)
const showUserMenu = ref(false)

let notificationTimer = null

onMounted(() => {
    notificationStore.fetchNotifications()
    // Poll for new notifications every 30 seconds
    notificationTimer = setInterval(() => {
        notificationStore.fetchNotifications()
    }, 30000)
})

onUnmounted(() => {
    if (notificationTimer) clearInterval(notificationTimer)
})

const toggleNotifications = () => {
    showNotifications.value = !showNotifications.value
    if (showNotifications.value) {
        showResults.value = false
        showUserMenu.value = false
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

const markAllAsRead = () => {
    notificationStore.markAllAsRead()
}

const goToEvent = (event) => {
    showNotifications.value = false
    router.push({ name: 'DeviceDetails', params: { id: event.device_id } })
}

// Custom directive for clicking outside dropdowns
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

    // Basic normalization
    const key = name.toLowerCase().replace('device-', '')
    return iconMap[key] || HelpCircle
}
</script>
