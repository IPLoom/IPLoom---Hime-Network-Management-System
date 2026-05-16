<script setup>
import { ref, onMounted, computed } from 'vue'
import { 
  Database, 
  RefreshCw, 
  Save, 
  Trash2, 
  AlertTriangle,
  Zap,
  Clock,
  CheckCircle2,
  Loader2,
  ShieldCheck
} from 'lucide-vue-next'

import api from '@/utils/api'
import ConfirmationModal from '@/components/ConfirmationModal.vue'

const props = defineProps({
  deviceId: {
    type: String,
    required: true
  }
})

const quota = ref(null)
const status = ref(null)
const loading = ref(true)
const saving = ref(false)
const error = ref(null)

const isDeleteModalOpen = ref(false)
const isResetModalOpen = ref(false)
const isUnblockModalOpen = ref(false)
const processingAction = ref(false)

const form = ref({
  limit_mb: 100,
  period_hours: 24,
  enabled: true
})

const fetchQuota = async () => {
  loading.value = true
  try {
    const [qRes, sRes] = await Promise.all([
      api.get(`/internet-quotas/devices/${props.deviceId}`),
      api.get(`/internet-quotas/devices/${props.deviceId}/status`)
    ])
    
    if (qRes.data) {
      const data = qRes.data
      quota.value = data
      form.value.limit_mb = Math.round(data.limit_bytes / (1024 * 1024))
      form.value.period_hours = data.period_hours
      form.value.enabled = data.enabled
    } else {
      quota.value = null
    }
    
    if (sRes.data) {
      status.value = sRes.data
    }
  } catch (err) {
    error.value = "Failed to load quota settings"
  } finally {
    loading.value = false
  }
}

const saveQuota = async () => {
  saving.value = true
  error.value = null
  try {
    await api.post(`/internet-quotas/devices/${props.deviceId}`, {
      device_id: props.deviceId,
      limit_bytes: form.value.limit_mb * 1024 * 1024,
      period_hours: form.value.period_hours,
      enabled: form.value.enabled
    })
    
    await fetchQuota()
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to save quota"
  } finally {
    saving.value = false
  }
}

const confirmDelete = async () => {
  processingAction.value = true
  try {
    await api.delete(`/internet-quotas/devices/${props.deviceId}`)
    quota.value = null
    status.value = null
    isDeleteModalOpen.value = false
  } catch (err) {
    error.value = "Failed to delete quota"
  } finally {
    processingAction.value = false
  }
}

const confirmReset = async () => {
  processingAction.value = true
  try {
    await api.post(`/internet-quotas/devices/${props.deviceId}/reset`)
    await fetchQuota()
    isResetModalOpen.value = false
  } catch (err) {
    error.value = "Failed to reset usage"
  } finally {
    processingAction.value = false
  }
}

const confirmUnblock = async () => {
  processingAction.value = true
  try {
    // Manually unblock by setting is_manual_unblock to true
    await api.patch(`/devices/${props.deviceId}`, {
      is_manual_unblock: true
    })
    await fetchQuota()
    isUnblockModalOpen.value = false
  } catch (err) {
    error.value = "Failed to apply manual unblock"
  } finally {
    processingAction.value = false
  }
}

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleString()
}

onMounted(fetchQuota)
</script>

<template>
  <div class="space-y-8">
    <div class="premium-card overflow-hidden relative !p-0">
      <!-- Hero Background Effect -->
      <div class="absolute -top-12 -right-12 w-64 h-64 bg-indigo-500/10 dark:bg-indigo-400/5 rounded-full blur-3xl pointer-events-none"></div>
      
      <!-- Top Section: Title & Header -->
      <div class="p-8 pb-4 relative z-10">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-500 shrink-0">
              <Zap class="w-6 h-6" />
            </div>
            <div>
              <h2 class="text-xl font-black text-slate-900 dark:text-white">Internet Data Quota</h2>
              <p class="text-sm text-slate-500 mt-1 font-medium">Control total bandwidth consumption over time.</p>
            </div>
          </div>
          
          <div v-if="quota" class="flex items-center gap-2">
            <button 
              type="button"
              @click.stop="isResetModalOpen = true"
              class="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-xl transition-all font-bold text-xs uppercase tracking-wider"
              title="Reset Consumption Counter"
            >
              <RefreshCw class="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
            <button 
              type="button"
              @click.stop="isDeleteModalOpen = true"
              class="p-2 bg-rose-50 dark:bg-rose-900/20 hover:bg-rose-100 dark:hover:bg-rose-900/40 text-rose-600 dark:text-rose-400 rounded-xl transition-all"
              title="Remove Policy"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- Center Section: Real-time Stats & Progress -->
      <div v-if="status" class="px-8 pb-8 space-y-8 relative z-10">
        <!-- Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-100 dark:border-slate-800/50">
            <div class="text-[10px] font-black uppercase text-slate-400 mb-1.5 tracking-widest">Usage</div>
            <div class="flex items-baseline gap-2">
              <span class="text-2xl font-black text-slate-900 dark:text-white">{{ formatBytes(status.current_usage) }}</span>
              <span class="text-[10px] font-bold text-slate-500 uppercase">/ {{ formatBytes(status.limit_bytes) }}</span>
            </div>
          </div>

          <div class="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-100 dark:border-slate-800/50">
            <div class="text-[10px] font-black uppercase text-slate-400 mb-1.5 tracking-widest">Status</div>
            <div class="flex items-center gap-2">
              <div :class="status.is_exceeded ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500'" class="w-2.5 h-2.5 rounded-full shadow-lg"></div>
              <div class="text-sm font-black text-slate-900 dark:text-white uppercase">
                {{ status.is_exceeded ? 'Quota Exceeded' : 'Under Limit' }}
              </div>
            </div>
          </div>

          <div class="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-100 dark:border-slate-800/50">
            <div class="text-[10px] font-black uppercase text-slate-400 mb-1.5 tracking-widest">Resets</div>
            <div class="text-sm font-black text-slate-700 dark:text-slate-300 truncate">
               {{ formatDate(status.next_reset_at) }}
            </div>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Consumption Percentage</h3>
            <span class="text-xl font-black" :class="status.is_exceeded ? 'text-rose-500' : 'text-indigo-500'">
              {{ Math.round(status.percent_used) }}%
            </span>
          </div>
          
          <div class="h-4 bg-slate-100 dark:bg-slate-950 rounded-full border border-slate-200 dark:border-slate-800 p-0.5 relative overflow-hidden">
            <div 
              class="h-full rounded-full transition-all duration-1000 ease-out shadow-sm relative overflow-hidden"
              :class="[
                status.is_exceeded ? 'bg-gradient-to-r from-rose-600 to-rose-400' : (status.percent_used > 85 ? 'bg-gradient-to-r from-amber-500 to-amber-300' : 'bg-gradient-to-r from-indigo-600 to-cyan-400')
              ]"
              :style="{ width: Math.min(status.percent_used, 100) + '%' }"
            >
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-[shimmer_2s_infinite]"></div>
            </div>
          </div>
        </div>

        <!-- Warning Area & Manual Override -->
        <div v-if="status.is_exceeded || status.is_manual_block || status.is_scheduled_block" class="p-6 rounded-2xl bg-amber-500/5 border border-amber-500/10">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex items-start gap-3">
              <AlertTriangle class="w-5 h-5 text-amber-500 mt-0.5" />
              <div class="text-xs">
                <span class="font-black text-amber-600 dark:text-amber-400 uppercase tracking-widest mr-3">Active Blocks:</span>
                <div class="flex flex-wrap gap-2 mt-2">
                  <span v-if="status.is_exceeded" class="px-2 py-1 bg-rose-500/10 text-rose-500 rounded font-black text-[9px]">QUOTA EXCEEDED</span>
                  <span v-if="status.is_manual_block" class="px-2 py-1 bg-amber-500/10 text-amber-500 rounded font-black text-[9px]">MANUAL BLOCK</span>
                  <span v-if="status.is_scheduled_block" class="px-2 py-1 bg-amber-500/10 text-amber-500 rounded font-black text-[9px]">SCHEDULED DOWNTIME</span>
                </div>
              </div>
            </div>

            <!-- Manual Unblock Button (Administrator Override) -->
            <button 
              type="button"
              v-if="(status.is_exceeded || status.is_scheduled_block) && !status.is_manual_unblock"
              @click.stop="isUnblockModalOpen = true"
              class="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-all font-black text-[10px] uppercase tracking-wider shadow-lg shadow-emerald-900/20"
            >
              <ShieldCheck class="w-4 h-4" />
              <span>Manually Restore Access</span>
            </button>
            <div v-else-if="status.is_manual_unblock" class="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 text-emerald-500 rounded-xl font-black text-[10px] uppercase tracking-wider">
               <ShieldCheck class="w-4 h-4" />
               <span>Override Active</span>
            </div>
          </div>
        </div>
      </div>

    <!-- Modals -->
    <ConfirmationModal 
      :isOpen="isDeleteModalOpen"
      title="Remove Quota Policy"
      message="Are you sure you want to permanently remove the internet data quota for this device? All usage history and limits will be deleted."
      confirmText="Remove Policy"
      type="danger"
      :loading="processingAction"
      @close="isDeleteModalOpen = false"
      @confirm="confirmDelete"
    />

    <ConfirmationModal 
      :isOpen="isResetModalOpen"
      title="Reset Data Usage"
      message="This will reset the current consumption counter to zero. If the device was blocked due to quota, access will be restored until the limit is reached again."
      confirmText="Reset Now"
      :loading="processingAction"
      @close="isResetModalOpen = false"
      @confirm="confirmReset"
    />

    <ConfirmationModal 
      :isOpen="isUnblockModalOpen"
      title="Administrator Override"
      message="You are about to manually restore internet access for this device. This bypasses both active quotas and schedules. This override is of the HIGHEST PRIORITY but will automatically expire on the next quota reset period."
      confirmText="Apply Override"
      :loading="processingAction"
      @close="isUnblockModalOpen = false"
      @confirm="confirmUnblock"
    />

      <!-- Divider -->
      <div class="px-8">
        <div class="h-px bg-slate-100 dark:bg-slate-800"></div>
      </div>

      <!-- Configuration Form Section -->
      <div class="p-8">
        <div class="flex items-center gap-3 mb-6">
           <h3 class="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">Quota Configuration</h3>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="space-y-2">
            <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Limit (MB)</label>
            <div class="relative">
              <input 
                v-model.number="form.limit_mb" 
                type="number" 
                class="w-full bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700 rounded-2xl px-5 py-3 text-sm font-black focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500/50 transition-all dark:text-white"
                placeholder="e.g. 500"
              />
              <div class="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-black text-slate-400">MB</div>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Reset Window</label>
            <select 
              v-model.number="form.period_hours"
              class="w-full bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700 rounded-2xl px-5 py-3 text-sm font-black focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500/50 transition-all dark:text-white appearance-none"
            >
              <option :value="1">Hourly</option>
              <option :value="12">12 Hours</option>
              <option :value="24">Daily (24h)</option>
              <option :value="168">Weekly (7d)</option>
              <option :value="720">Monthly (30d)</option>
            </select>
          </div>

          <div class="flex flex-col justify-end pb-1">
            <label class="flex items-center gap-3 cursor-pointer group">
              <div class="relative">
                <input type="checkbox" v-model="form.enabled" class="sr-only" />
                <div class="w-11 h-6 bg-slate-200 dark:bg-slate-800 rounded-full transition-all" :class="form.enabled ? 'bg-indigo-600' : ''"></div>
                <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200" :class="form.enabled ? 'translate-x-5' : ''"></div>
              </div>
              <span class="text-[10px] font-black uppercase tracking-widest" :class="form.enabled ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'">
                {{ form.enabled ? 'Enabled' : 'Paused' }}
              </span>
            </label>
          </div>
        </div>

        <div class="flex justify-end pt-6 border-t border-slate-50 dark:border-slate-800/50">
          <button 
            @click="saveQuota"
            :disabled="saving"
            class="flex items-center gap-3 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-2xl font-black uppercase tracking-widest text-[11px] transition-all shadow-xl shadow-indigo-500/20"
          >
            <Save v-if="!saving" class="w-4 h-4" />
            <Loader2 v-else class="w-4 h-4 animate-spin" />
            {{ quota ? 'Update Policy' : 'Enable Quota' }}
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="error" class="mt-6 p-5 bg-rose-50 dark:bg-rose-900/20 border border-rose-100 dark:border-rose-800/50 rounded-2xl text-rose-600 dark:text-rose-400 text-xs font-bold flex items-center gap-3">
      <div class="p-2 bg-rose-500/20 rounded-lg"><AlertTriangle class="w-4 h-4" /></div>
      {{ error }}
    </div>
  </div>
</template>
