<template>
  <div class="flex items-center group cursor-pointer" @click="$router.push('/')">
    <div class="relative flex items-center justify-center transition-all duration-300">
      <!-- Background Glow for Visibility -->
      <div class="absolute inset-0 bg-blue-600/5 dark:bg-blue-400/10 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
      
      <!-- Logo/Icon Container with 'Crop' logic -->
      <div :class="[
        'relative z-10 transition-all duration-500 group-hover:scale-110 overflow-hidden flex items-center justify-center',
        compact ? 'w-10 h-10' : 'h-10 md:h-12 w-auto'
      ]">
        <!-- 
          We use scale-125 to 'zoom in' and effectively crop out 
          the vertical/horizontal whitespace from the source image.
        -->
        <img :src="compact ? '/brand/icon.png' : '/brand/logo.png'" alt="IPLoom" 
          class="h-full w-auto object-contain scale-[1.35] drop-shadow-[0_2px_15px_rgba(30,64,175,0.5)] dark:drop-shadow-[0_2px_15px_rgba(255,255,255,0.2)]" />
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
