<template>
    <TransitionRoot appear :show="isOpen" as="template">
        <Dialog as="div" @close="closeModal" class="relative z-50">
            <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0" enter-to="opacity-100"
                leave="duration-200 ease-in" leave-from="opacity-100" leave-to="opacity-0">
                <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" />
            </TransitionChild>

            <div class="fixed inset-0 overflow-y-auto">
                <div class="flex min-h-full items-center justify-center p-4 text-center">
                    <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0 scale-95"
                        enter-to="opacity-100 scale-100" leave="duration-200 ease-in" leave-from="opacity-100 scale-100"
                        leave-to="opacity-0 scale-95">
                        <DialogPanel
                            class="w-full max-w-md transform rounded-2xl bg-white dark:bg-slate-800 p-6 text-left align-middle shadow-xl transition-all border border-slate-200 dark:border-slate-700">
                            <div class="flex flex-col items-center mb-6">
                                <Popover class="relative group">
                                    <PopoverButton
                                        class="h-20 w-20 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-lg flex items-center justify-center hover:border-blue-500 transition-all group focus:outline-none overflow-hidden relative">
                                        <img v-if="form.icon && form.icon.startsWith('/static/')" :src="form.icon" class="h-12 w-12 object-contain" />
                                        <component v-else :is="getIcon(form.icon || 'help-circle')" class="h-10 w-10 text-slate-500 group-hover:text-blue-500 transition-colors" />
                                        
                                        <div class="absolute -bottom-2 -right-2 bg-blue-600 text-white p-1.5 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Pencil class="w-3 h-3" />
                                        </div>
                                    </PopoverButton>

                                    <transition enter-active-class="transition duration-200 ease-out"
                                        enter-from-class="translate-y-1 opacity-0"
                                        enter-to-class="translate-y-0 opacity-100"
                                        leave-active-class="transition duration-150 ease-in"
                                        leave-from-class="translate-y-0 opacity-100"
                                        leave-to-class="translate-y-1 opacity-0">
                                        <PopoverPanel
                                            class="absolute z-50 mt-4 -left-1/2 translate-x-1/2 w-[320px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl p-4 focus:outline-none overflow-x-hidden">
                                            <div class="mb-3 px-1">
                                                <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                                    <Search class="w-3.5 h-3.5 text-slate-400" />
                                                    <input v-model="iconSearch" type="text" placeholder="Search icons or categories..."
                                                        class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                                                </div>
                                            </div>
                                            <div class="max-h-[360px] overflow-y-auto overflow-x-hidden pr-1 custom-scrollbar">
                                                <div v-for="(icons, category) in groupedIcons" :key="category" class="mb-5">
                                                    <h4 class="text-[9px] font-black uppercase tracking-[0.15em] text-slate-400 mb-2.5 px-1">{{ category }}</h4>
                                                    <div class="grid grid-cols-4 gap-2">
                                                        <button v-for="icon in icons" :key="icon.name" type="button"
                                                            @click="form.icon = icon.name"
                                                            class="group/item relative flex flex-col items-center gap-1.5 p-2 rounded-xl transition-all"
                                                            :class="form.icon === icon.name ? 'bg-blue-600 text-white shadow-lg' : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500'">
                                                            <div class="h-8 w-8 flex items-center justify-center">
                                                                <img v-if="icon.name.startsWith('/static/')" :src="icon.name" class="h-6 w-6 object-contain" />
                                                                <component v-else :is="getIcon(icon.name)" class="h-6 w-6" />
                                                            </div>
                                                            <span class="text-[8px] font-bold truncate w-full text-center px-0.5 opacity-80 group-hover/item:opacity-100">
                                                                {{ icon.label }}
                                                            </span>
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </PopoverPanel>
                                    </transition>
                                </Popover>

                                <!-- Brand Logo in Header -->
                                <Popover class="relative -ml-4 -mt-4 z-10">
                                    <PopoverButton
                                        class="h-10 w-10 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-lg flex items-center justify-center hover:scale-110 transition-transform group focus:outline-none overflow-hidden">
                                        <img v-if="form.brand_icon" :src="form.brand_icon" class="h-6 w-6 object-contain" />
                                        <div v-else class="flex flex-col items-center">
                                            <component :is="getIcon('shield-question')" class="h-4 w-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
                                        </div>
                                        <div class="absolute inset-0 bg-blue-600/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                            <Pencil class="w-3 h-3 text-blue-600" />
                                        </div>
                                    </PopoverButton>

                                    <transition enter-active-class="transition duration-200 ease-out"
                                        enter-from-class="translate-y-1 opacity-0"
                                        enter-to-class="translate-y-0 opacity-100"
                                        leave-active-class="transition duration-150 ease-in"
                                        leave-from-class="translate-y-0 opacity-100"
                                        leave-to-class="translate-y-1 opacity-0">
                                        <PopoverPanel
                                            class="absolute z-[60] mt-4 left-0 w-[280px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl p-4 focus:outline-none">
                                            <div class="mb-3 px-1">
                                                <p class="text-[9px] font-black uppercase tracking-[0.15em] text-slate-400 mb-2 px-1">Assign Brand</p>
                                                <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                                    <Search class="w-3.5 h-3.5 text-slate-400" />
                                                    <input v-model="brandSearch" type="text" placeholder="Search brands..."
                                                        class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                                                </div>
                                            </div>
                                            <div class="max-h-[280px] overflow-y-auto pr-1 custom-scrollbar">
                                                <div class="grid grid-cols-2 gap-2">
                                                    <button type="button" @click="form.brand = ''; form.brand_icon = ''"
                                                        class="flex items-center gap-2 p-2 rounded-xl border border-dashed border-slate-200 dark:border-slate-700 hover:border-blue-500 transition-all text-left">
                                                        <div class="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
                                                            <X class="w-4 h-4 text-slate-400" />
                                                        </div>
                                                        <span class="text-[10px] font-bold text-slate-500">None</span>
                                                    </button>
                                                    <button v-for="brand in filteredBrands" :key="brand.id" type="button"
                                                        @click="form.brand = brand.name; form.brand_icon = brand.path"
                                                        class="flex items-center gap-2 p-2 rounded-xl border transition-all text-left"
                                                        :class="form.brand === brand.name ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-transparent hover:bg-slate-50 dark:hover:bg-slate-900/50'">
                                                        <img :src="brand.path" class="w-8 h-8 object-contain rounded-lg bg-white p-1" />
                                                        <span class="text-[10px] font-black truncate text-slate-700 dark:text-slate-200">{{ brand.name }}</span>
                                                    </button>
                                                </div>
                                            </div>
                                        </PopoverPanel>
                                    </transition>
                                </Popover>
                                
                                <div class="w-full px-8 text-center mt-4">
                                    <input v-model="form.display_name" type="text"
                                        class="w-full bg-transparent border-none text-xl font-black text-slate-900 dark:text-white text-center focus:ring-0 placeholder:text-slate-300"
                                        placeholder="Enter device name..." />
                                    <p class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mt-1">Device Configuration</p>
                                </div>
                            </div>

                            <form @submit.prevent="saveDevice" class="space-y-6">
                                <!-- IP Address (Read Only) -->
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">IP
                                        Address</label>
                                    <p class="mt-1 text-sm text-slate-500 font-mono">{{ device.ip }}</p>
                                </div>

                                <!-- Device Category -->
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Device Category</label>
                                    <Popover class="relative" v-slot="{ open, close }">
                                        <PopoverButton
                                            class="w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group">
                                            <div class="flex items-center gap-3">
                                                <component :is="getIcon(form.device_type)" class="w-5 h-5 text-blue-500" />
                                                <span class="text-sm font-medium">{{ form.device_type || 'Select Category' }}</span>
                                            </div>
                                            <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="{'rotate-180': open}" />
                                        </PopoverButton>

                                        <transition enter-active-class="transition duration-100 ease-out"
                                            enter-from-class="transform scale-95 opacity-0"
                                            enter-to-class="transform scale-100 opacity-100"
                                            leave-active-class="transition duration-75 ease-in"
                                            leave-from-class="transform scale-100 opacity-100"
                                            leave-to-class="transform scale-95 opacity-0">
                                            <PopoverPanel
                                                class="absolute z-50 mt-2 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden focus:outline-none">
                                                <div class="p-2 border-b border-slate-100 dark:border-slate-700/50">
                                                    <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                                        <Search class="w-3.5 h-3.5 text-slate-400" />
                                                        <input v-model="categorySearch" type="text" placeholder="Search categories..."
                                                            class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                                                    </div>
                                                </div>
                                                <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                                                    <button v-for="type in filteredDeviceTypes" :key="type"
                                                        type="button" @click="form.device_type = type; close()"
                                                        class="w-full flex items-center px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors"
                                                        :class="form.device_type === type ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                                        {{ type }}
                                                    </button>
                                                </div>
                                            </PopoverPanel>
                                        </transition>
                                    </Popover>
                                </div>

                                <!-- Brand Selection (New unified selector) -->
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Manufacturer / Brand</label>
                                    <Popover class="relative" v-slot="{ open, close }">
                                        <PopoverButton
                                            class="w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group">
                                            <div class="flex items-center gap-3">
                                                <div class="w-6 h-6 rounded-lg bg-white flex items-center justify-center border border-slate-100 overflow-hidden shrink-0">
                                                    <img v-if="form.brand_icon" :src="form.brand_icon" class="w-full h-full object-contain" />
                                                    <div v-else class="text-[8px] font-bold text-slate-300">N/A</div>
                                                </div>
                                                <span class="text-sm font-medium">{{ form.brand || 'Select or type brand...' }}</span>
                                            </div>
                                            <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="{'rotate-180': open}" />
                                        </PopoverButton>

                                        <transition enter-active-class="transition duration-100 ease-out"
                                            enter-from-class="transform scale-95 opacity-0"
                                            enter-to-class="transform scale-100 opacity-100"
                                            leave-active-class="transition duration-75 ease-in"
                                            leave-from-class="transform scale-100 opacity-100"
                                            leave-to-class="transform scale-95 opacity-0">
                                            <PopoverPanel
                                                class="absolute z-50 mt-2 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden focus:outline-none">
                                                <div class="p-2 border-b border-slate-100 dark:border-slate-700/50">
                                                    <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                                        <Search class="w-3.5 h-3.5 text-slate-400" />
                                                        <input v-model="brandSearch" type="text" placeholder="Search brand or type new..."
                                                            class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                                                    </div>
                                                </div>
                                                <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                                                    <button v-for="brand in filteredBrands" :key="brand.id"
                                                        type="button" @click="form.brand = brand.name; form.brand_icon = brand.path; close()"
                                                        class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors"
                                                        :class="form.brand === brand.name ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                                        <img :src="brand.path" class="w-6 h-6 object-contain rounded bg-white p-0.5" />
                                                        {{ brand.name }}
                                                    </button>
                                                    <div v-if="brandSearch && !filteredBrands.length" class="p-4 text-center">
                                                        <p class="text-xs text-slate-500 mb-2">No matching brand found.</p>
                                                        <button type="button" @click="form.brand = brandSearch; close()"
                                                            class="text-xs font-bold text-blue-600 hover:underline">
                                                            Use "{{ brandSearch }}" as custom name
                                                        </button>
                                                    </div>
                                                </div>
                                            </PopoverPanel>
                                        </transition>
                                    </Popover>
                                </div>

                                <!-- Parent Device Selection -->
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Connected Via (Parent)</label>
                                    <Popover class="relative" v-slot="{ open, close }">
                                        <PopoverButton
                                            class="w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group">
                                            <span class="text-sm font-medium truncate">{{ getParentLabel }}</span>
                                            <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="{'rotate-180': open}" />
                                        </PopoverButton>

                                        <transition enter-active-class="transition duration-100 ease-out"
                                            enter-from-class="transform scale-95 opacity-0"
                                            enter-to-class="transform scale-100 opacity-100"
                                            leave-active-class="transition duration-75 ease-in"
                                            leave-from-class="transform scale-100 opacity-100"
                                            leave-to-class="transform scale-95 opacity-0">
                                            <PopoverPanel
                                                class="absolute z-50 mt-2 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden focus:outline-none">
                                                <div class="p-2 border-b border-slate-100 dark:border-slate-700/50">
                                                    <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                                        <Search class="w-3.5 h-3.5 text-slate-400" />
                                                        <input v-model="parentSearch" @click.stop type="text" placeholder="Search devices..."
                                                            class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                                                    </div>
                                                </div>
                                                <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                                                    <button type="button" @click="form.parent_id = null; close()"
                                                        class="w-full flex items-center px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors"
                                                        :class="!form.parent_id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                                        Main Gateway (Default)
                                                    </button>
                                                    <button v-for="d in filteredPotentialParents" :key="d.id"
                                                        type="button" @click="form.parent_id = d.id; close()"
                                                        class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors"
                                                        :class="form.parent_id === d.id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                                        <component :is="getIcon(d.icon)" class="w-4 h-4 mr-3 opacity-70" />
                                                        <span class="truncate">{{ d.display_name || d.name || d.ip }}</span>
                                                    </button>
                                                </div>
                                            </PopoverPanel>
                                        </transition>
                                    </Popover>
                                </div>

                                <div class="mt-6 flex justify-end gap-3">
                                    <button type="button"
                                        class="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-slate-700 dark:text-slate-200 dark:border-slate-600 dark:hover:bg-slate-600"
                                        @click="closeModal">
                                        Cancel
                                    </button>
                                    <button type="submit" :disabled="isSaving"
                                        class="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed">
                                        <Loader2 v-if="isSaving" class="mr-2 h-4 w-4 animate-spin" />
                                        {{ isSaving ? 'Saving...' : 'Save Changes' }}
                                    </button>
                                </div>
                            </form>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import {
    TransitionRoot,
    TransitionChild,
    Dialog,
    DialogPanel,
    DialogTitle,
    Popover,
    PopoverButton,
    PopoverPanel
} from '@headlessui/vue'
import {
    Search,
    ChevronDown,
    Loader2,
    Pencil,
    X
} from 'lucide-vue-next'
import api from '@/utils/api'
import { getIcon } from '@/utils/icons'
import { useNotifications } from '@/composables/useNotifications'
import { useSystemStore } from '@/stores/system'
const systemStore = useSystemStore()

const deviceTypes = computed(() => systemStore.deviceTypes)
const availableIcons = computed(() => systemStore.availableIcons)

const props = defineProps({
    isOpen: Boolean,
    device: Object
})

const emit = defineEmits(['close', 'save'])

const isSaving = ref(false)
const allDevices = ref([])
const parentSearch = ref('')

const { notifySuccess, notifyError } = useNotifications()

const form = ref({
    display_name: '',
    device_type: '',
    icon: '',
    brand: '',
    brand_icon: '',
    parent_id: null
})

const categorySearch = ref('')
const iconSearch = ref('')
const brandSearch = ref('')

const filteredDeviceTypes = computed(() => {
    if (!categorySearch.value) return deviceTypes.value
    return deviceTypes.value.filter(t => t.toLowerCase().includes(categorySearch.value.toLowerCase()))
})

const filteredIcons = computed(() => {
    if (!iconSearch.value) return availableIcons.value
    const s = iconSearch.value.toLowerCase()
    return availableIcons.value.filter(icon => 
        (icon.label || '').toLowerCase().includes(s) || 
        (icon.category || '').toLowerCase().includes(s) ||
        (icon.name || '').toLowerCase().includes(s)
    )
})

const groupedIcons = computed(() => {
    const groups = {}
    filteredIcons.value.forEach(icon => {
        const cat = icon.category || 'Other'
        if (!groups[cat]) groups[cat] = []
        groups[cat].push(icon)
    })
    return groups
})

const filteredBrands = computed(() => {
    const registry = systemStore.brandRegistry || []
    if (!brandSearch.value) return registry
    const s = brandSearch.value.toLowerCase()
    return registry.filter(b => b.name.toLowerCase().includes(s))
})

const filteredPotentialParents = computed(() => {
    const others = allDevices.value.filter(d => d.id !== props.device?.id)
    if (!parentSearch.value) return others
    const s = parentSearch.value.toLowerCase()
    return others.filter(d =>
        (d.display_name || '').toLowerCase().includes(s) ||
        (d.name || '').toLowerCase().includes(s) ||
        (d.ip || '').includes(s)
    )
})

const getParentLabel = computed(() => {
    if (!form.value.parent_id) return 'Main Gateway (Default)'
    const p = allDevices.value.find(d => d.id === form.value.parent_id)
    return p ? (p.display_name || p.name || p.ip) : 'Unknown Device'
})

watch(() => form.value.device_type, (newType) => {
    if (newType && systemStore.iconMap[newType]) {
        form.value.icon = systemStore.iconMap[newType]
    }
})

// getIcon is now imported from @/utils/icons

const fetchAllDevices = async () => {
    try {
        const res = await api.get('/devices/?limit=-1')
        allDevices.value = res.data.items || []
    } catch (e) {
        console.error('Failed to fetch devices:', e)
    }
}

onMounted(() => {
    fetchAllDevices()
})

watch(() => props.device, (newVal) => {
    if (newVal) {
        form.value = {
            display_name: newVal.display_name || newVal.name || '',
            device_type: newVal.device_type || 'unknown',
            icon: newVal.icon || 'help-circle',
            brand: newVal.brand || '',
            brand_icon: newVal.brand_icon || '',
            parent_id: newVal.parent_id || null
        }
    }
}, { immediate: true })

const closeModal = () => {
    emit('close')
}

const saveDevice = async () => {
    if (!props.device) return
    isSaving.value = true
    try {
        const response = await api.patch(`/devices/${props.device.id}`, form.value)
        notifySuccess('Device updated successfully')
        emit('save', response.data)
        closeModal()
    } catch (error) {
        console.error('Failed to update device', error)
        notifyError('Failed to update device')
    } finally {
        isSaving.value = false
    }
}
</script>
