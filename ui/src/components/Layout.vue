<template>
  <div class="flex flex-col h-screen w-full bg-slate-50 dark:bg-slate-900 overflow-hidden">
    <!-- Full Width Top Bar -->
    <TopBar @toggle-mobile-menu="mobileMenuOpen = !mobileMenuOpen" />

    <div class="flex flex-1 overflow-hidden">
      <!-- Desktop Sidebar (Now below TopBar) -->
      <aside :class="[
        'hidden md:flex flex-col bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-56'
      ]">
        <!-- Navigation -->
        <nav class="flex-1 overflow-y-auto py-4 px-2">
          <ul class="space-y-1">
            <li v-for="item in navItems" :key="item.name">
              <router-link :to="item.path" class="nav-item" :class="[
                $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                  ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              ]" v-tooltip:right="sidebarCollapsed ? item.name : null">
                <component :is="item.icon" class="h-5 w-5 flex-shrink-0" :class="sidebarCollapsed ? '' : 'mr-3'" />
                <span v-if="!sidebarCollapsed">{{ item.name }}</span>
              </router-link>
            </li>
          </ul>
        </nav>

        <!-- Version & Toggle -->
        <div class="p-2 border-t border-slate-200 dark:border-slate-700 space-y-2">
          <div v-if="!sidebarCollapsed"
            class="text-[10px] uppercase font-bold tracking-widest text-slate-400 dark:text-slate-600 text-center py-2">
            {{ version }}
          </div>
          <button @click="sidebarCollapsed = !sidebarCollapsed"
            class="w-full flex items-center p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-all duration-300"
            :class="sidebarCollapsed ? 'justify-center' : 'px-3 space-x-3'"
            v-tooltip:right="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
            <component :is="sidebarCollapsed ? ChevronRightIcon : ChevronLeftIcon" class="h-5 w-5 flex-shrink-0" />
            <span v-if="!sidebarCollapsed" class="text-sm font-medium">Collapse</span>
          </button>
        </div>
      </aside>

      <!-- Mobile Menu -->
      <Transition enter-active-class="transition-transform duration-300" enter-from-class="translate-x-full"
        enter-to-class="translate-x-0" leave-active-class="transition-transform duration-300"
        leave-from-class="translate-x-0" leave-to-class="translate-x-full">
        <div v-if="mobileMenuOpen" class="md:hidden fixed inset-0 z-40 bg-white dark:bg-slate-800 pt-0">
          <div class="h-16 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-700">
            <AppLogo class="scale-90 origin-left" />
            <button @click="mobileMenuOpen = false"
              class="p-2 -mr-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300">
              <XMarkIcon class="h-6 w-6" />
            </button>
          </div>
          <nav class="p-4">
            <ul class="space-y-1">
              <li v-for="item in navItems" :key="item.name">
                <router-link :to="item.path" @click="mobileMenuOpen = false" class="nav-item !px-4 !py-3" :class="[
                  $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                    ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                ]">
                  <component :is="item.icon" class="h-5 w-5 mr-3 flex-shrink-0" />
                  {{ item.name }}
                </router-link>
              </li>
            </ul>
          </nav>
        </div>
      </Transition>

      <!-- Main Content Area -->
      <main class="flex-1 overflow-y-auto">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          <router-view />
        </div>
      </main>
    </div>

    <!-- Global Notifications -->
    <NotificationToast />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import AppLogo from './AppLogo.vue'
import TopBar from './TopBar.vue'
import NotificationToast from './NotificationToast.vue'
import { useWebSockets } from '@/composables/useWebSockets'
import { useNotifications } from '@/composables/useNotifications'

const { connect, lastNotification } = useWebSockets()
const { notifyInfo, notifyError, notifySuccess } = useNotifications()

import { useNotificationStore } from '@/stores/notifications'
const notificationStore = useNotificationStore()

onMounted(() => {
  connect()
})

import {
  HomeIcon,
  ComputerDesktopIcon,
  TableCellsIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  ListBulletIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  BellIcon,
  ChartBarIcon,
  CommandLineIcon,
  ShareIcon
} from '@heroicons/vue/24/outline'

const sidebarCollapsed = ref(true)
const mobileMenuOpen = ref(false)
const version = import.meta.env.VITE_APP_VERSION || 'v0.3.1'

const navItems = [
  { name: 'Dashboard', path: '/', icon: HomeIcon },
  { name: 'Devices', path: '/devices', icon: ComputerDesktopIcon },
  { name: 'Topology', path: '/topology', icon: ShareIcon },
  { name: 'Events', path: '/events', icon: BellIcon },
  { name: 'Analytics', path: '/analytics', icon: ChartBarIcon },
  { name: 'IP Occupancy', path: '/occupancy', icon: TableCellsIcon },
  { name: 'Logs & Activity', path: '/logs', icon: CommandLineIcon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
]
</script>
