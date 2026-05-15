<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] overflow-y-auto" @click.self="close">
    <div class="flex min-h-screen items-center justify-center p-4">
      <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"></div>
      
      <div class="relative bg-white dark:bg-slate-900 w-full max-w-4xl rounded-[2rem] shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col max-h-[90vh]">
        
        <!-- Header -->
        <div class="px-8 py-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
          <div>
            <h2 class="text-xl font-black text-slate-900 dark:text-white flex items-center gap-3">
              <Radar class="w-6 h-6 text-blue-500 animate-pulse" />
              New Device Radar
            </h2>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">Scanning entire subnet for active devices...</p>
          </div>
          <button @click="close" class="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-colors">
            <X class="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <!-- Scan Progress / State -->
        <div v-if="scanning" class="p-12 flex flex-col items-center justify-center text-center space-y-6">
          <div class="relative w-48 h-48">
            <div class="absolute inset-0 rounded-full border-4 border-blue-500/10"></div>
            <div class="absolute inset-0 rounded-full border-t-4 border-blue-500 animate-spin"></div>
            <div class="absolute inset-4 rounded-full bg-blue-500/5 flex items-center justify-center">
              <div class="text-2xl font-black text-blue-500">{{ progress }}%</div>
            </div>
          </div>
          <div class="space-y-2">
            <h3 class="text-lg font-bold text-slate-900 dark:text-white">Pinging every IP...</h3>
            <p class="text-sm text-slate-500 max-w-xs mx-auto">Identifying devices, resolving hostnames, and checking status. This usually takes 5-10 seconds.</p>
          </div>
        </div>

        <!-- Results -->
        <div v-else class="flex-1 overflow-hidden flex flex-col">
          <!-- Stats Summary -->
          <div class="px-8 py-4 bg-blue-50/50 dark:bg-blue-900/10 border-b border-blue-100 dark:border-blue-900/30 flex items-center gap-6">
             <div class="flex items-center gap-2">
                <span class="text-lg font-black text-blue-600 dark:text-blue-400">{{ results.filter(r => r.is_new).length }}</span>
                <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">New Devices</span>
             </div>
             <div class="flex items-center gap-2">
                <span class="text-lg font-black text-slate-900 dark:text-white">{{ results.filter(r => r.status === 'MOVED').length }}</span>
                <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Moved IP</span>
             </div>
             <div class="flex items-center gap-2">
                <span class="text-lg font-black text-slate-400">{{ results.filter(r => r.status === 'KNOWN').length }}</span>
                <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Known</span>
             </div>
          </div>

          <!-- List -->
          <div class="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar">
            <div v-for="device in results" :key="device.ip" 
                 class="group p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-2xl flex items-center justify-between transition-all hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-700"
                 :class="{ '!bg-blue-50/50 dark:!bg-blue-900/20 !border-blue-200 dark:!border-blue-800': device.is_new }">
              
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-xl shadow-sm transition-colors"
                     :class="device.is_new ? 'bg-blue-500 text-white shadow-blue-500/20' : 'bg-slate-200 dark:bg-slate-700 text-slate-500'">
                  <img v-if="device.icon && device.icon.startsWith('/static/')" :src="device.icon" class="w-5 h-5 object-contain" />
                  <component v-else :is="getIcon(device.icon || 'monitor')" class="w-5 h-5" />
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <img v-if="device.brand_icon" :src="device.brand_icon" class="w-4 h-4 object-contain" />
                    <h4 class="text-sm font-black text-slate-900 dark:text-white truncate max-w-[200px]">
                      {{ device.hostname || 'Unknown Device' }}
                    </h4>
                    <span v-if="device.status === 'NEW'" class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 text-[8px] font-black uppercase tracking-widest rounded-md">New Found</span>
                    <span v-if="device.status === 'MOVED'" class="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/50 text-amber-600 dark:text-amber-400 text-[8px] font-black uppercase tracking-widest rounded-md">IP Moved</span>
                  </div>
                  <div class="flex items-center gap-3 mt-1">
                    <span class="text-[10px] font-mono text-slate-500">{{ device.ip }}</span>
                    <span class="text-[10px] text-slate-400 font-medium">{{ device.vendor }}</span>
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button v-if="device.is_new" 
                        @click="addToInventory(device)"
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-black uppercase tracking-widest rounded-xl transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2">
                  <Plus class="w-3.5 h-3.5" /> Add to Map
                </button>
                <div v-else class="text-[9px] font-black uppercase tracking-widest text-slate-400 px-4">
                  Already in Registry
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-6 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/30">
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            Scan completed in {{ scanTime }}s
          </p>
          <div class="flex gap-3">
            <button @click="close" class="px-5 py-2.5 text-[11px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
              Dismiss
            </button>
            <button @click="startScan" :disabled="scanning" class="px-5 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-[11px] font-black uppercase tracking-widest rounded-xl hover:opacity-90 transition-all flex items-center gap-2">
              <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': scanning }" />
              {{ scanning ? 'Scanning...' : 'Rescan' }}
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Radar, X, Loader2, RefreshCw, Plus, Monitor, CheckCircle2 } from 'lucide-vue-next'
import api from '@/utils/api'
import { getIcon } from '@/utils/icons'
import { useNotifications } from '@/composables/useNotifications'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'onboarded'])
const { notifySuccess, notifyError } = useNotifications()

const scanning = ref(false)
const progress = ref(0)
const results = ref([])
const scanTime = ref(0)

const close = () => {
  if (scanning.value) return
  emit('close')
}

const startScan = async () => {
  scanning.value = true
  progress.value = 0
  results.value = []
  const startTime = Date.now()

  // Fake progress increments
  const interval = setInterval(() => {
    if (progress.value < 90) progress.value += Math.floor(Math.random() * 15)
  }, 800)

  try {
    const res = await api.post('/discovery/scan')
    results.value = res.data
    progress.value = 100
    scanTime.value = ((Date.now() - startTime) / 1000).toFixed(1)
  } catch (e) {
    notifyError('Discovery scan failed')
  } finally {
    clearInterval(interval)
    setTimeout(() => {
      scanning.value = false
    }, 500)
  }
}

const addToInventory = async (device) => {
  try {
    // This will trigger a full port scan and add to main DB via the backend
    // We reuse the existing upsert logic if possible, or a dedicated onboarding endpoint
    await api.post('/devices/onboard', {
       ip: device.ip,
       mac: device.mac,
       hostname: device.hostname,
       vendor: device.vendor
    })
    notifySuccess(`Device ${device.ip} added to inventory`)
    device.is_new = false
    device.status = 'KNOWN'
    emit('onboarded')
  } catch (e) {
    notifyError('Failed to add device')
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) startScan()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}
</style>
