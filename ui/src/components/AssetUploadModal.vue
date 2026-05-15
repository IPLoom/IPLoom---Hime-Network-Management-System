<template>
  <TransitionRoot appear :show="isOpen" as="template">
    <Dialog as="div" @close="close" class="relative z-[100]">
      <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0" enter-to="opacity-100"
        leave="duration-200 ease-in" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0 bg-slate-900/40 dark:bg-slate-950/60 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100" leave="duration-200 ease-in" leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95">
            <DialogPanel
              class="w-full max-w-md transform rounded-[2.5rem] bg-white dark:bg-slate-900 p-8 text-left align-middle shadow-2xl transition-all border border-slate-200 dark:border-slate-800">
              
              <div class="flex items-center justify-between mb-8">
                <div>
                  <DialogTitle as="h3" class="text-xl font-black text-slate-900 dark:text-white leading-none">
                    Upload {{ type === 'brand' ? 'Brand' : 'Device' }} Asset
                  </DialogTitle>
                  <p class="text-xs text-slate-500 mt-2 font-medium">Add custom iconography to your network</p>
                </div>
                <button @click="close" class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors">
                  <X class="w-6 h-6" />
                </button>
              </div>

              <div class="space-y-6">
                <!-- File Picker / Dropzone -->
                <div 
                  @click="triggerFilePicker"
                  @dragover.prevent="isDragging = true"
                  @dragenter.prevent="isDragging = true"
                  @dragleave.prevent="isDragging = false"
                  @drop.prevent="handleDrop"
                  :class="[
                    'relative aspect-video rounded-3xl border-2 border-dashed flex flex-col items-center justify-center gap-4 transition-all cursor-pointer overflow-hidden',
                    isDragging ? 'border-blue-500 bg-blue-500/5' : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50'
                  ]"
                >
                  <template v-if="previewUrl">
                    <img :src="previewUrl" class="w-full h-full object-contain p-4" />
                    <div class="absolute inset-0 bg-slate-900/40 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center">
                       <p class="text-white text-xs font-bold uppercase tracking-widest">Change File</p>
                    </div>
                  </template>
                  <template v-else>
                    <div class="p-4 bg-white dark:bg-slate-800 rounded-2xl shadow-sm">
                      <Upload class="w-6 h-6 text-blue-500" />
                    </div>
                    <div class="text-center">
                      <p class="text-sm font-bold text-slate-900 dark:text-white">Click or drag image</p>
                      <p class="text-[10px] text-slate-500 font-medium mt-1">SVG, PNG, or JPG (Max 2MB)</p>
                    </div>
                  </template>
                  <input type="file" ref="fileInput" @change="handleFileSelect" accept="image/*" class="hidden" />
                </div>

                <!-- Asset Type Selector -->
                <div class="space-y-2">
                  <label class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 ml-1">Asset Type</label>
                  <div class="grid grid-cols-2 gap-2 p-1 bg-slate-100 dark:bg-slate-800 rounded-2xl">
                    <button 
                      @click="internalType = 'brand'"
                      :class="[
                        'px-4 py-2 text-xs font-bold rounded-xl transition-all',
                        internalType === 'brand' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                      ]"
                    >Brand Logo</button>
                    <button 
                      @click="internalType = 'device'"
                      :class="[
                        'px-4 py-2 text-xs font-bold rounded-xl transition-all',
                        internalType === 'device' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                      ]"
                    >Device Icon</button>
                  </div>
                </div>

                <!-- Asset Name -->
                <div class="space-y-2">
                  <label class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 ml-1">Asset Name</label>
                  <input 
                    v-model="name"
                    type="text" 
                    placeholder="e.g. Apple HomePod"
                    class="w-full bg-slate-100 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl px-5 py-4 text-sm font-bold text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>

                <!-- Action Buttons -->
                <div class="flex items-center gap-3 pt-2">
                  <button @click="close" class="flex-1 px-6 py-4 rounded-2xl text-sm font-black uppercase tracking-widest text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
                    Cancel
                  </button>
                  <button 
                    @click="upload" 
                    :disabled="!file || !name || loading"
                    class="flex-1 px-6 py-4 rounded-2xl text-sm font-black uppercase tracking-widest bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50 disabled:grayscale flex items-center justify-center gap-2"
                  >
                    <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
                    <span>{{ loading ? 'Uploading...' : 'Upload' }}</span>
                  </button>
                </div>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, watch } from 'vue'
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogPanel,
  DialogTitle,
} from '@headlessui/vue'
import { X, Upload, Loader2 } from 'lucide-vue-next'
import api from '@/utils/api'
import { useNotifications } from '@/composables/useNotifications'

const { notifySuccess, notifyError } = useNotifications()

const props = defineProps({
  isOpen: Boolean,
  type: String // 'brand' or 'device'
})

const emit = defineEmits(['close', 'uploaded'])

const fileInput = ref(null)
const file = ref(null)
const previewUrl = ref(null)
const name = ref('')
const loading = ref(false)
const isDragging = ref(false)
const internalType = ref('brand')

watch(() => props.isOpen, (val) => {
  if (val) {
    file.value = null
    previewUrl.value = null
    name.value = ''
    loading.value = false
    internalType.value = props.type || 'brand'
  }
})

const triggerFilePicker = () => {
  fileInput.value.click()
}

const handleFileSelect = (e) => {
  const selected = e.target.files[0]
  if (selected) processFile(selected)
}

const handleDrop = (e) => {
  isDragging.value = false
  const dropped = e.dataTransfer.files[0]
  if (dropped) processFile(dropped)
}

const processFile = (selectedFile) => {
  if (!selectedFile.type.startsWith('image/')) {
    notifyError('Please select an image file')
    return
  }
  file.value = selectedFile
  previewUrl.value = URL.createObjectURL(selectedFile)
  if (!name.value) {
    name.value = selectedFile.name.split('.')[0]
  }
}

const upload = async () => {
  if (!file.value || !name.value) return
  
  loading.value = true
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('type', internalType.value)
  formData.append('name', name.value)

  try {
    await api.post('/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    notifySuccess('Asset uploaded successfully')
    emit('uploaded')
    close()
  } catch (e) {
    console.error(e)
    notifyError('Failed to upload asset')
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('close')
}
</script>
