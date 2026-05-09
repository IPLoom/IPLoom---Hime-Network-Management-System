import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'
import Dashboard from '@/views/Dashboard.vue'
import { useAuthStore } from '@/stores/authStore'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/views/Onboarding.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/DeviceList.vue')
      },
      {
        path: 'devices/:id',
        name: 'DeviceDetails',
        component: () => import('@/views/DeviceDetails.vue')
      },
      {
        path: 'occupancy',
        name: 'Occupancy',
        component: () => import('@/views/Occupancy.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue')
      },
      {
        path: 'scans',
        name: 'ScanHistory',
        component: () => import('@/views/ScanHistory.vue')
      },
      {
        path: 'events',
        name: 'Events',
        component: () => import('@/views/Events.vue')
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue')
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue')
      },
      {
        path: 'topology',
        name: 'Topology',
        component: () => import('@/views/Topology.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Wait for setup status on first load
  if (!authStore.setupStatus.checked) {
    await authStore.checkSetupStatus()
    authStore.setupStatus.checked = true
  }

  const isAuthenticated = authStore.isAuthenticated

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'Login' })
  } else if (isAuthenticated && authStore.setupStatus.needs_setup && to.name !== 'Onboarding') {
    next({ name: 'Onboarding' })
  } else if (to.name === 'Login' && isAuthenticated && !authStore.setupStatus.needs_setup) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
