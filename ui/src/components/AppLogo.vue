<template>
  <div class="flex items-center space-x-2.5 group">
    <div class="relative">
      <!-- Outer Ring -->
      <div
        class="absolute inset-0 bg-blue-500/20 dark:bg-white/10 rounded-xl blur-md group-hover:blur-lg transition-all">
      </div>

      <!-- Logo Body (Interconnected Mesh) -->
      <div
        class="relative w-10 h-10 bg-slate-900 dark:bg-white rounded-xl flex items-center justify-center shadow-lg transition-transform group-hover:scale-110 duration-500">
        <svg viewBox="0 0 24 24" class="w-6 h-6 text-white dark:text-slate-900" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <!-- Central Hub -->
          <circle cx="12" cy="12" r="2" fill="currentColor" />

          <!-- Outer Nodes -->
          <circle cx="12" cy="5" r="1.5" />
          <circle cx="18" cy="9" r="1.5" />
          <circle cx="18" cy="15" r="1.5" />
          <circle cx="12" cy="19" r="1.5" />
          <circle cx="6" cy="15" r="1.5" />
          <circle cx="6" cy="9" r="1.5" />

          <!-- Radial Connections -->
          <path d="M12 7v3M17 10l-3 1M17 14l-3-1M12 17v-3M7 14l3-1M7 10l3 1" opacity="0.6" />

          <!-- Mesh Perimeter -->
          <path d="M12 5l6 4v6l-6 4l-6-4v-6l6-4" stroke-dasharray="1 1.5" opacity="0.3" />
        </svg>
      </div>

      <!-- Pulse Effect -->
      <div
        class="absolute -inset-1 border-2 border-blue-500/30 dark:border-white/20 rounded-2xl animate-ping opacity-20 group-hover:opacity-40 pointer-events-none">
      </div>
    </div>

    <div v-if="!compact" class="flex flex-col leading-none">
      <span
        class="text-xl font-black tracking-tighter text-slate-900 dark:text-white uppercase transition-colors group-hover:text-blue-500">
        IPLoom
      </span>
      <span class="text-[8px] font-black tracking-[0.3em] text-slate-400 dark:text-slate-500 uppercase mt-0.5">Network
        OS</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  compact: {
    type: Boolean,
    default: false
  }
})
</script>
