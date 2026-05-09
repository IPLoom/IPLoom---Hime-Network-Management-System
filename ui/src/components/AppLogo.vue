<template>
  <div class="flex items-center group cursor-pointer" @click="$router.push('/')">
    <div class="relative flex items-center">
      <!-- Icon for compact mode or as part of logo -->
      <div v-if="compact" class="relative w-9 h-9 transition-transform duration-500 group-hover:scale-110">
        <img src="/brand/icon.png" alt="IPLoom" class="w-full h-full object-contain drop-shadow-md" />
        <!-- Pulse Effect -->
        <div class="absolute -inset-1 border-2 border-blue-500/20 rounded-xl animate-ping opacity-0 group-hover:opacity-40 pointer-events-none"></div>
      </div>

      <!-- Full Logo for standard mode -->
      <div v-else :class="[
        size === 'sm' ? 'h-6' : 
        size === 'lg' ? 'h-12' : 
        size === 'xl' ? 'h-16' : 
        size === '2xl' ? 'h-24' : 
        size === '3xl' ? 'h-32' : 'h-8',
        'transition-all duration-500 group-hover:brightness-110'
      ]">
        <img src="/brand/logo.png" alt="IPLoom" class="h-full object-contain drop-shadow-sm" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  compact: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md'
  }
})
</script>
