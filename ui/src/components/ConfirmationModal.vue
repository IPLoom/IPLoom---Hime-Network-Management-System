<template>
    <Teleport to="body">
        <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="transform scale-95 opacity-0"
            enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-150 ease-in"
            leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
            <div v-if="isOpen"
                class="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
                <div class="modal-container-sm" v-click-outside="close">
                    <div class="flex flex-col gap-4">
                        <div class="flex items-start gap-4">
                            <div :class="[
                                'p-3 rounded-full flex-shrink-0',
                                type === 'danger' ? 'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400' : 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                            ]">
                                <component :is="type === 'danger' ? AlertTriangle : Info" class="w-6 h-6" />
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                                    {{ title }}
                                </h3>
                                <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
                                    {{ message }}
                                </p>
                            </div>
                        </div>

                        <div class="flex justify-end gap-3 mt-2">
                            <button @click="close"
                                class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                                Cancel
                            </button>
                            <button @click="confirm" :disabled="loading" :class="[
                                'px-4 py-2 text-sm font-medium text-white rounded-lg shadow-sm transition-colors flex items-center gap-2',
                                type === 'danger' ? 'bg-red-600 hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2' : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                                loading ? 'opacity-75 cursor-not-allowed' : ''
                            ]">
                                <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
                                {{ confirmText }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup>
import { AlertTriangle, Info, Loader2 } from 'lucide-vue-next'

const props = defineProps({
    isOpen: Boolean,
    title: {
        type: String,
        default: 'Confirmation'
    },
    message: {
        type: String,
        required: true
    },
    confirmText: {
        type: String,
        default: 'Confirm'
    },
    type: {
        type: String,
        default: 'primary', // 'primary' or 'danger'
        validator: (value) => ['primary', 'danger'].includes(value)
    },
    loading: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['close', 'confirm'])

const close = () => {
    if (!props.loading) {
        emit('close')
    }
}

const confirm = () => {
    emit('confirm')
}
</script>
