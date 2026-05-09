<template>
  <div class="min-h-screen flex bg-slate-50 font-sans overflow-hidden text-slate-900">
    <!-- Left Column: Branding & Visuals (Hidden on small screens) -->
    <div class="hidden lg:flex lg:w-1/2 relative flex-col justify-center items-center p-8 border-r border-slate-200 bg-white">
      <!-- Background Effects -->
      <div class="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] bg-blue-600/5 rounded-full blur-[80px] animate-pulse"></div>
      <div class="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-indigo-600/5 rounded-full blur-[80px] animate-pulse animation-delay-2000"></div>
      
      <!-- Content Container -->
      <div class="relative z-10 max-w-sm text-center">
        <AppLogo size="3xl" class="justify-center mb-16 mix-blend-multiply" />
        <p class="text-lg text-slate-500 font-medium leading-relaxed mt-3">
          The next generation of home network intelligence and security.
        </p>
        
        <!-- Feature Pills (Compact) -->
        <div class="flex flex-wrap justify-center gap-1.5 mt-8">
          <span v-for="tag in ['Real-time Scanning', 'Device Trust', 'DNS Protection', 'Traffic Analytics']" :key="tag"
                class="px-2 py-0.5 bg-slate-50 border border-slate-200 rounded-full text-[9px] font-black uppercase tracking-widest text-slate-400">
            {{ tag }}
          </span>
        </div>
      </div>

      <!-- Footer Info -->
      <div class="absolute bottom-8 left-1/2 -translate-x-1/2 text-center w-full">
        <p class="text-[9px] text-slate-300 uppercase font-black tracking-[0.4em]">Hardware Secured • v0.4.0</p>
      </div>
    </div>

    <!-- Right Column: Form (Center on mobile, right on desktop) -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8 relative">
      <!-- Background Blobs (Mobile only) -->
      <div class="lg:hidden absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute top-0 left-0 w-64 h-64 bg-blue-600/5 rounded-full blur-[80px]"></div>
        <div class="absolute bottom-0 right-0 w-64 h-64 bg-indigo-600/5 rounded-full blur-[80px]"></div>
      </div>

      <div class="w-full max-w-[340px] relative z-10">
        <!-- Logo for Mobile -->
        <div class="lg:hidden flex justify-center mb-6">
           <AppLogo size="3xl" class="mix-blend-multiply" />
        </div>

        <div class="bg-white/80 backdrop-blur-3xl border border-slate-200 rounded-[1.5rem] shadow-2xl shadow-slate-200/50 p-6 relative group">
          <!-- Glass effect accent -->
          <div class="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-3xl group-hover:bg-blue-500/10 transition-all duration-700"></div>

          <div class="mb-5">
            <h2 class="text-xl font-bold text-slate-900 tracking-tight">
              {{ isFirstRun ? 'Onboarding' : 'Authentication' }}
            </h2>
            <p class="text-slate-500 text-[12px] font-medium mt-0.5">
              {{ isFirstRun ? 'Set up your administrator credentials' : 'Access your secure dashboard' }}
            </p>
          </div>

          <!-- Initial Loading State -->
          <div v-if="!authStore.initialized" class="py-12 flex flex-col items-center justify-center space-y-4">
            <div class="relative w-12 h-12">
              <div class="absolute inset-0 border-4 border-blue-600/10 rounded-full"></div>
              <div class="absolute inset-0 border-4 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
            <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest animate-pulse">Initializing System</p>
          </div>

          <form v-else @submit.prevent="handleSubmit" class="space-y-3">
            <div v-if="authStore.error || localError" class="p-2.5 rounded-lg bg-red-50 border border-red-100 text-red-600 text-[10px] flex items-center gap-2.5 animate-shake font-bold">
               <ShieldAlert class="h-3.5 w-3.5" />
               <span>{{ authStore.error || localError }}</span>
            </div>

            <div class="space-y-1">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">Username</label>
              <div class="relative group/input">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within/input:text-blue-600 transition-colors">
                  <UserIcon class="h-3.5 w-3.5" />
                </div>
                <input 
                  v-model="form.username"
                  type="text" 
                  required
                  class="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-600 transition-all text-[13px]"
                  placeholder="admin"
                />
              </div>
            </div>

            <div v-if="isFirstRun" class="grid grid-cols-2 gap-2">
              <div class="space-y-1">
                <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">Name</label>
                <input 
                  v-model="form.full_name"
                  type="text" 
                  class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-600 transition-all text-[13px]"
                  placeholder="John Doe"
                />
              </div>
              <div class="space-y-1">
                <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">Region</label>
                <div class="relative">
                  <button 
                    @click="isRegionOpen = !isRegionOpen"
                    type="button"
                    class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 text-left flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-600 transition-all text-[13px]"
                  >
                    <span :class="form.region ? 'text-slate-900' : 'text-slate-400'">
                      {{ form.region || 'Select' }}
                    </span>
                    <ChevronDown class="h-3.5 w-3.5 text-slate-400 transition-transform duration-200" :class="{ 'rotate-180': isRegionOpen }" />
                  </button>

                  <!-- Custom Dropdown Container -->
                  <div v-if="isRegionOpen" class="absolute z-50 w-full mt-1.5 bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden py-1 animate-in fade-in zoom-in-95 duration-200">
                    <button 
                      v-for="reg in regions" 
                      :key="reg.val"
                      @click="selectRegion(reg.val)"
                      type="button"
                      class="w-full px-3 py-1.5 text-left text-[12px] text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                    >
                      {{ reg.label }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="space-y-1">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">Password</label>
              <div class="relative group/input">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within/input:text-blue-600 transition-colors">
                  <LockIcon class="h-3.5 w-3.5" />
                </div>
                <input 
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'" 
                  required
                  class="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-10 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-600 transition-all text-[13px]"
                  placeholder="••••••••"
                />
                <button 
                  type="button" 
                  @click="showPassword = !showPassword"
                  class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <Eye v-if="!showPassword" class="h-3.5 w-3.5" />
                  <EyeOff v-else class="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <!-- Confirm Password for Registration -->
            <div v-if="isFirstRun" class="space-y-1">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">Confirm Password</label>
              <div class="relative group/input">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within/input:text-blue-600 transition-colors">
                  <LockIcon class="h-3.5 w-3.5" />
                </div>
                <input 
                  v-model="form.confirm_password"
                  :type="showConfirmPassword ? 'text' : 'password'" 
                  required
                  class="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-10 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-600 transition-all text-[13px]"
                  placeholder="••••••••"
                />
                <button 
                  type="button" 
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <Eye v-if="!showConfirmPassword" class="h-3.5 w-3.5" />
                  <EyeOff v-else class="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div class="pt-1.5">
              <button 
                type="submit"
                :disabled="authStore.loading"
                class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-lg shadow-lg shadow-blue-600/20 transform transition-all active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-[12px] uppercase tracking-widest"
              >
                <Loader2 v-if="authStore.loading" class="animate-spin h-3.5 w-3.5" />
                {{ isFirstRun ? 'Register' : 'Login' }}
              </button>
            </div>
          </form>

          <!-- System Info Footer (Mobile) -->
          <div class="lg:hidden mt-6 text-center">
            <p class="text-[7px] text-slate-300 uppercase font-black tracking-[0.4em]">IPLoom Hardware Control</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AppLogo from '@/components/AppLogo.vue'
import { User as UserIcon, Lock as LockIcon, Loader2, ShieldAlert, Eye, EyeOff, ChevronDown } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isRegionOpen = ref(false)
const localError = ref('')

const regions = [
  { label: 'USA', val: 'US' },
  { label: 'Europe', val: 'EU' },
  { label: 'Asia', val: 'AS' },
  { label: 'Australia', val: 'AU' },
  { label: 'India', val: 'IN' }
]

const form = ref({
  username: '',
  password: '',
  confirm_password: '',
  full_name: '',
  region: ''
})

const selectRegion = (val) => {
  form.value.region = val
  isRegionOpen.value = false
}

const isFirstRun = computed(() => !authStore.setupStatus.user_exists)

// Clear local error when form changes
watch(form, () => {
  localError.value = ''
}, { deep: true })

onMounted(async () => {
  if (!authStore.initialized) {
    await authStore.checkSetupStatus()
  }
  if (authStore.isAuthenticated) {
    router.push('/')
  }
})

const handleSubmit = async () => {
  localError.value = ''
  
  if (isFirstRun.value) {
    if (form.value.password !== form.value.confirm_password) {
      localError.value = 'Passwords do not match'
      return
    }
  }

  let success = false
  if (isFirstRun.value) {
    const { confirm_password, ...registerData } = form.value
    success = await authStore.register(registerData)
  } else {
    success = await authStore.login(form.value.username, form.value.password)
  }

  if (success) {
    await authStore.checkSetupStatus()
    if (authStore.setupStatus.needs_setup) {
      router.push('/onboarding')
    } else {
      router.push('/')
    }
  }
}
</script>

<style scoped>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}
@keyframes fadeInZoom {
  from { opacity: 0; transform: scale(0.95) translateY(-10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.animate-shake {
  animation: shake 0.2s ease-in-out 0s 2;
}
.animate-in {
  animation: fadeInZoom 0.2s ease-out forwards;
}
.animation-delay-2000 {
  animation-delay: 2s;
}
</style>
