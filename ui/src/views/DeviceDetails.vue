<template>
  <div v-if="device" class="space-y-6 max-w-7xl mx-auto pb-12">
    <!-- Header Area -->
    <!-- Header Area -->
    <div class="sticky top-0 z-30 -mx-4 px-4 py-3 mb-8 bg-slate-50/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        <!-- Left: Identity & Context -->
        <div class="flex items-center gap-4 flex-1 min-w-0">
          <router-link to="/devices" 
            class="group flex items-center justify-center w-10 h-10 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all" 
            v-tooltip="'Back to Inventory'">
            <ArrowLeft class="w-5 h-5 text-slate-400 group-hover:text-blue-500 transition-colors" />
          </router-link>

          <div class="flex items-center gap-4 flex-1 min-w-0">
            <!-- Large Main Icon with Popover and Status Badge -->
            <Popover class="relative shrink-0">
              <PopoverButton
                v-tooltip="'Change Device Category & Icon'"
                class="h-16 w-16 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center hover:border-blue-500 transition-all group focus:outline-none shadow-sm relative overflow-hidden">
                <img v-if="form.icon && form.icon.startsWith('/static/')" :src="form.icon" class="h-10 w-10 object-contain" />
                <component :is="resolveIcon(form.icon || 'help-circle')" v-else class="h-8 w-8 text-slate-500 group-hover:text-blue-500 transition-colors" />
                
                <div class="absolute inset-0 bg-blue-600/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <Pencil class="w-4 h-4 text-blue-600" />
                </div>
              </PopoverButton>

              <!-- Online Status Badge overlapping/next to icon -->
              <div :class="[
                device.status === 'online' ? 'bg-emerald-500 border-white dark:border-slate-900' : 'bg-slate-400 border-white dark:border-slate-900',
                'absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 z-10 shadow-sm'
              ]" v-tooltip="device.status">
                <div v-if="device.status === 'online'" class="absolute inset-0 bg-emerald-500 rounded-full animate-ping opacity-25"></div>
              </div>

              <transition enter-active-class="transition duration-200 ease-out"
                enter-from-class="translate-y-1 opacity-0" enter-to-class="translate-y-0 opacity-100"
                leave-active-class="transition duration-150 ease-in" leave-from-class="translate-y-0 opacity-100"
                leave-to-class="translate-y-1 opacity-0">
                <PopoverPanel
                  class="absolute z-50 mt-4 left-0 w-[320px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl p-4 focus:outline-none overflow-x-hidden">
                  <div class="mb-3 px-1">
                    <div class="space-y-2">
                      <label class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 ml-1">Device Type</label>
                      <Popover class="relative" v-slot="{ open, close }">
                        <PopoverButton
                          v-tooltip="'Change Device Category'"
                          class="w-full flex items-center justify-between px-5 py-4 bg-slate-100 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-bold text-slate-900 dark:text-white hover:border-blue-500/50 transition-all group outline-none">
                          <div class="flex items-center gap-3">
                            <component :is="resolveIcon(form.device_type)" class="w-5 h-5 text-blue-500" />
                            <span class="text-xs font-black uppercase tracking-widest">{{ form.device_type || 'Select Type' }}</span>
                          </div>
                          <ChevronDown class="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-all" :class="{ 'rotate-180': open }" />
                        </PopoverButton>
                        <transition enter-active-class="transition duration-200 ease-out" enter-from-class="translate-y-1 opacity-0"
                          enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-150 ease-in"
                          leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-1 opacity-0">
                          <PopoverPanel
                            class="absolute z-50 mt-2 w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden p-2">
                            <div class="max-h-64 overflow-y-auto custom-scrollbar space-y-1">
                              <button v-for="type in deviceTypes" :key="type" 
                                @click="form.device_type = type; form.icon = systemStore.getIcon(type); close()"
                                class="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all"
                                :class="form.device_type === type ? 'bg-blue-600 text-white shadow-lg' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300'">
                                <component :is="resolveIcon(type)" class="w-4 h-4" />
                                {{ type }}
                              </button>
                            </div>
                          </PopoverPanel>
                        </transition>
                      </Popover>
                    </div>

                    <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg mt-4">
                      <Search class="w-3.5 h-3.5 text-slate-400" />
                      <input v-model="iconSearch" type="text" placeholder="Search icons or categories..."
                        class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                    </div>
                  </div>
                  <div class="max-h-[360px] overflow-y-auto overflow-x-hidden pr-1 custom-scrollbar">
                    <div v-for="(icons, category) in groupedIcons" :key="category" class="mb-5">
                      <h4 class="text-[9px] font-black uppercase tracking-[0.15em] text-slate-400 mb-2.5 px-1">{{ category }}</h4>
                      <div class="grid grid-cols-4 gap-2">
                        <button v-for="icon in icons" :key="icon.name" type="button" @click="updateFields({ icon: icon.name })"
                          class="group/item relative flex flex-col items-center gap-1.5 p-2 rounded-xl transition-all"
                          :class="form.icon === icon.name ? 'bg-blue-600 text-white shadow-lg' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500'">
                          <div class="h-8 w-8 flex items-center justify-center">
                            <img v-if="icon.name.startsWith('/static/')" :src="icon.name" class="h-6 w-6 object-contain" />
                            <component :is="resolveIcon(icon.name)" v-else class="h-6 w-6" />
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

            <div class="flex-1 min-w-0">
              <div class="flex flex-col">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">Network Resource</span>
                  <div class="w-1 h-1 bg-slate-300 dark:bg-slate-700 rounded-full"></div>
                  <span class="text-[9px] font-black uppercase tracking-[0.2em] text-blue-500">{{ device.ip }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <input v-model="form.display_name" type="text" 
                    @change="updateFields({ display_name: form.display_name }, 'Name updated')"
                    @keyup.enter="$event.target.blur()"
                    class="bg-transparent border-none p-0 focus:ring-0 text-3xl font-black text-slate-900 dark:text-white flex-1 min-w-0 placeholder:text-slate-200 dark:placeholder:text-slate-800"
                    placeholder="Untagged Device" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Meta Info & Trusted Badge -->
        <div class="flex items-center gap-3 shrink-0">
          <!-- Trusted / Shield -->
          <div v-if="device.is_trusted" 
            class="flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest shadow-sm"
            v-tooltip="'Verified Configuration'">
            <ShieldCheck class="w-3.5 h-3.5"></ShieldCheck>
            <span>Verified</span>
          </div>

          <!-- Block / Unblock Toggle -->
          <button @click="toggleBlock"
            class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest shadow-sm transition-all"
            :class="device.is_blocked 
              ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 hover:bg-red-500/20' 
              : 'bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:border-red-500 hover:text-red-500'"
            v-tooltip="device.is_blocked ? 'Unblock Device Access' : 'Block Device Access'">
            <Ban class="w-3.5 h-3.5" :class="{ 'text-red-500': device.is_blocked }" />
            <span>{{ device.is_blocked ? 'Blocked' : 'Block' }}</span>
          </button>

          <!-- Brand Popover Integration -->
          <Popover class="relative">
            <PopoverButton
              v-tooltip="'Update Device Branding'"
              class="p-1 w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:border-blue-500 transition-all group overflow-hidden focus:outline-none flex items-center justify-center relative">
              <img v-if="form.brand_icon" :src="form.brand_icon" class="w-7 h-7 object-contain" />
              <div v-else class="flex flex-col items-center">
                <component :is="resolveIcon('shield-question')" class="w-5 h-5 text-slate-300 group-hover:text-blue-500" />
              </div>
              <div class="absolute inset-0 bg-blue-600/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Pencil class="w-3 h-3 text-blue-600" />
              </div>
            </PopoverButton>

            <transition enter-active-class="transition duration-200 ease-out"
              enter-from-class="translate-y-1 opacity-0" enter-to-class="translate-y-0 opacity-100"
              leave-active-class="transition duration-150 ease-in" leave-from-class="translate-y-0 opacity-100"
              leave-to-class="translate-y-1 opacity-0">
              <PopoverPanel
                class="absolute z-[60] mt-4 right-0 w-[280px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl p-4 focus:outline-none">
                <div class="mb-3 px-1">
                  <p class="text-[9px] font-black uppercase tracking-[0.15em] text-slate-400 mb-2 px-1">Identity Provider</p>
                  <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                    <Search class="w-3.5 h-3.5 text-slate-400" />
                    <input v-model="brandSearch" type="text" placeholder="Search brands..."
                      class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                  </div>
                </div>
                <div class="max-h-[280px] overflow-y-auto pr-1 custom-scrollbar">
                  <div class="grid grid-cols-2 gap-2">
                    <button type="button" @click="updateFields({ brand: '', brand_icon: '' })"
                      class="flex items-center gap-2 p-2 rounded-xl border border-dashed border-slate-200 dark:border-slate-700 hover:border-blue-500 transition-all text-left">
                      <div class="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
                        <X class="w-4 h-4 text-slate-400" />
                      </div>
                      <span class="text-[10px] font-bold text-slate-500">None</span>
                    </button>
                    <button v-for="brand in filteredBrands" :key="brand.id" type="button"
                      @click="updateFields({ brand: brand.name, brand_icon: brand.path }, `Brand updated to ${brand.name}`)"
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
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Column 1 & 2: Main Info -->
      <div class="lg:col-span-2 space-y-6">

        <!-- Approval Banner -->
        <div v-if="!device.is_trusted"
          class="relative overflow-hidden rounded-3xl bg-red-500 dark:bg-red-600 p-6 shadow-xl text-white">
          <div class="absolute -right-6 -top-6 w-24 h-24 bg-white/20 rounded-full blur-2xl"></div>
          <div class="relative z-10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-4">
              <ShieldAlert class="w-10 h-10 text-white/90" />
              <div>
                <h2 class="text-lg font-bold">Untrusted Device</h2>
                <p class="text-sm text-red-100 font-medium">This device has not been verified yet.</p>
              </div>
            </div>
            <button @click="approveDevice"
              class="btn-primary !bg-white !text-red-600 !px-5 !py-2.5 rounded-xl shadow-lg hover:shadow-xl hover:scale-105">
              <ShieldCheck class="w-5 h-5"></ShieldCheck> Approve
            </button>
          </div>
        </div>

        <!-- Metadata Protection Banner -->
        <div class="relative overflow-hidden rounded-3xl p-5 shadow-xl border transition-all mb-6"
          :class="device.is_trusted 
            ? 'bg-emerald-500 dark:bg-emerald-600 text-white border-emerald-400/30' 
            : 'bg-blue-500 dark:bg-blue-600 text-white border-blue-400/30'">
          <div class="absolute -right-8 -bottom-8 w-32 h-32 bg-white/10 rounded-full blur-3xl"></div>
          <div class="relative z-10 flex items-center gap-4">
            <div class="p-3 bg-white/20 rounded-2xl backdrop-blur-md">
              <ShieldCheck v-if="device.is_trusted" class="w-6 h-6 text-white"></ShieldCheck>
              <Info v-else class="w-6 h-6 text-white" />
            </div>
            <div class="flex-1">
              <h3 class="text-sm font-black uppercase tracking-wider leading-none mb-1">
                {{ device.is_trusted ? 'Configuration Locked' : 'Auto-Updates Active' }}
              </h3>
              <p class="text-xs text-white/90 font-medium leading-relaxed max-w-xl">
                {{ device.is_trusted 
                  ? 'This device is verified. All manual edits to the name, icon, and brand are protected from being overwritten by automated system scans.' 
                  : 'The system may automatically update this device\'s name and icon during scans. Mark it as Trusted to lock your manual configuration.' 
                }}
              </p>
            </div>
          </div>
        </div>

        <!-- Device Info Card -->
        <div class="premium-card group">
          <div
            class="absolute top-0 right-0 p-8 opacity-5 dark:opacity-10 group-hover:opacity-10 dark:group-hover:opacity-20 transition-opacity pointer-events-none select-none">
            <img v-if="(form.icon || device.icon) && (form.icon || device.icon).startsWith('/static/')" :src="form.icon || device.icon" class="w-32 h-32 object-contain" />
            <component v-else :is="resolveIcon(form.icon || device.icon)" class="w-32 h-32" />
          </div>

          <div class="flex items-center justify-between mb-6 relative z-10">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <div class="w-1.5 h-6 bg-blue-500 rounded-full"></div>
              Device Identification
            </h2>
            <button @click="saveChanges" :disabled="!isChanged || isSaving"
              class="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg shadow-blue-500/20 transition-all font-black uppercase tracking-[0.15em] text-[10px] relative z-20 disabled:opacity-50 disabled:bg-slate-400 disabled:shadow-none disabled:cursor-not-allowed">
              <Loader2 v-if="isSaving" class="w-3 h-3 animate-spin" />
              <Save v-else class="w-3 h-3" />
              <span>{{ isSaving ? 'Saving...' : 'Save Changes' }}</span>
            </button>
          </div>

          <div class="space-y-8">
            <!-- Tier 2: Classification & Hostname -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div class="space-y-3">
                <label class="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500 ml-1">Classification Type</label>
                <div class="relative w-full group" v-click-outside="() => isCategoryOpen = false">
                  <button @click="isCategoryOpen = !isCategoryOpen"
                    class="w-full flex items-center justify-between px-5 py-3.5 bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 hover:border-blue-500/30 transition-all rounded-2xl">
                    <div class="flex items-center gap-3">
                      <div class="p-1.5 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-lg">
                        <component :is="resolveIcon(form.icon || systemStore.getIcon(form.device_type))" class="w-4 h-4" />
                      </div>
                      <span class="font-bold text-slate-900 dark:text-white">{{ form.device_type || 'Select Category' }}</span>
                    </div>
                    <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200" :class="{ 'rotate-180': isCategoryOpen }" />
                  </button>

                  <transition enter-active-class="transition duration-100 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                    <div v-if="isCategoryOpen" class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-1.5 overflow-hidden">
                      <div class="px-3 py-2 border-b border-slate-100 dark:border-slate-700/50">
                        <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg border border-transparent focus-within:border-blue-500/30 transition-colors">
                          <Search class="w-3.5 h-3.5 text-slate-400" />
                          <input v-model="categorySearch" @click.stop type="text" placeholder="Search..." class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" autofocus />
                        </div>
                      </div>
                      <div class="overflow-y-auto max-h-60 custom-scrollbar">
                        <button v-for="type in filteredDeviceTypes" :key="type" @click="form.device_type = type; form.icon = systemStore.getIcon(type); isCategoryOpen = false; categorySearch = ''" class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors" :class="form.device_type === type ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                          {{ type }}
                        </button>
                      </div>
                    </div>
                  </transition>
                </div>
              </div>

              <div class="space-y-3">
                <label class="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500 ml-1">Network Hostname</label>
                <div class="relative group">
                  <input v-model="form.name" type="text" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/5 transition-all rounded-2xl px-5 py-3.5 font-mono text-sm font-bold text-slate-700 dark:text-slate-300" />
                  <div class="absolute right-4 top-1/2 -translate-y-1/2">
                    <div class="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-[8px] font-black uppercase tracking-widest text-slate-500">Local</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tier 3: Connectivity & Uplink -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div class="space-y-3">
                <label class="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500 ml-1">IP Management</label>
                <div class="relative w-full group" v-click-outside="() => isIPOpen = false">
                  <button @click="isIPOpen = !isIPOpen" class="w-full flex items-center justify-between px-5 py-3.5 bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 hover:border-blue-500/30 transition-all rounded-2xl">
                    <span class="font-bold text-slate-900 dark:text-white">{{ getIPAllocationLabel(form.ip_type) }}</span>
                    <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200" :class="{ 'rotate-180': isIPOpen }" />
                  </button>

                  <transition enter-active-class="transition duration-100 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                    <div v-if="isIPOpen" class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-1.5 overflow-hidden">
                      <button @click="form.ip_type = 'dynamic'; isIPOpen = false" class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors" :class="form.ip_type === 'dynamic' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                        Dynamic (DHCP)
                      </button>
                      <button @click="form.ip_type = 'static'; isIPOpen = false" class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors" :class="form.ip_type === 'static' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                        Static Reservation
                      </button>
                    </div>
                  </transition>
                </div>
              </div>

              <div class="space-y-3">
                <label class="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500 ml-1">Upstream Connection</label>
                <div class="relative w-full group" v-click-outside="() => isParentOpen = false">
                  <button @click="isParentOpen = !isParentOpen" class="w-full flex items-center justify-between px-5 py-3.5 bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 hover:border-blue-500/30 transition-all rounded-2xl">
                    <div class="flex items-center gap-2 overflow-hidden">
                      <component :is="resolveIcon(getParentIcon)" class="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span class="font-bold text-slate-900 dark:text-white truncate">{{ getParentLabel }}</span>
                    </div>
                    <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200" :class="{ 'rotate-180': isParentOpen }" />
                  </button>

                  <transition enter-active-class="transition duration-100 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                    <div v-if="isParentOpen" class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-1.5 overflow-hidden">
                      <div class="px-3 py-2 border-b border-slate-100 dark:border-slate-700/50">
                        <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                          <Search class="w-3.5 h-3.5 text-slate-400" />
                          <input v-model="parentSearch" @click.stop type="text" placeholder="Search devices..." class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                        </div>
                      </div>
                      <div class="max-h-60 overflow-y-auto custom-scrollbar">
                        <button @click="form.parent_id = null; isParentOpen = false" class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors" :class="!form.parent_id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                          Main Gateway (Default)
                        </button>
                        <button v-for="d in filteredPotentialParents" :key="d.id" @click="form.parent_id = d.id; isParentOpen = false" class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors" :class="form.parent_id === d.id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                          <img v-if="d.icon && d.icon.startsWith('/static/')" :src="d.icon" class="w-4 h-4 object-contain opacity-70" />
                          <component v-else :is="resolveIcon(d.icon)" class="w-4 h-4 opacity-70" />
                          <span>{{ d.display_name || d.name || d.ip }}</span>
                        </button>
                      </div>
                    </div>
                  </transition>
                </div>
              </div>
            </div>
          </div>

        </div>

      <!-- Slim & Compact Network Insights Bar -->
      <div class="premium-card !p-4 group">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 lg:divide-x divide-slate-100 dark:divide-slate-800">
          
          <!-- Manufacturer -->
          <div class="px-6 py-2 first:pl-0 lg:px-8">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-lg">
                <Cpu class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Vendor</div>
                <div class="text-xs font-bold text-slate-900 dark:text-white truncate max-w-[120px]">{{ device.vendor || 'Generic' }}</div>
              </div>
            </div>
          </div>

          <!-- MAC Signature -->
          <div class="px-6 py-2 lg:px-8">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-lg">
                <Fingerprint class="w-4 h-4" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between">
                  <span class="text-[9px] font-black uppercase tracking-widest text-slate-400">MAC</span>
                  <button @click="copyToClipboard(device.mac)" class="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors">
                    <Copy class="w-2.5 h-2.5 text-slate-400" />
                  </button>
                </div>
                <div class="text-[11px] font-mono font-bold text-slate-700 dark:text-slate-300">{{ (device.mac || '00:00:00:00:00:00').toUpperCase() }}</div>
              </div>
            </div>
          </div>

          <!-- Discovery -->
          <div class="px-6 py-2 lg:px-8">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-lg">
                <Calendar class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Age</div>
                <div class="text-xs font-bold text-slate-900 dark:text-white truncate">{{ formatRelativeTime(device.first_seen) }}</div>
              </div>
            </div>
          </div>

          <!-- Path -->
          <div class="px-6 py-2 lg:px-8 last:pr-0">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-lg">
                <Globe class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Node</div>
                <div class="text-xs font-bold text-slate-900 dark:text-white truncate">{{ device.internet_path || 'Local Network' }}</div>
              </div>
            </div>
          </div>

        </div>
      </div>
      
      <!-- Wireless Link Status (Only for wireless devices) -->
      <div v-if="form.attributes?.connection_type === 'wireless'" class="premium-card !p-4 group border-blue-500/20 bg-blue-500/5">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 lg:divide-x divide-blue-500/10">
          
          <!-- Signal Strength -->
          <div class="px-6 py-2 first:pl-0 lg:px-8">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-lg">
                <Wifi class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Signal (RSSI)</div>
                <div class="flex items-center gap-2">
                  <div class="text-xs font-bold text-slate-900 dark:text-white">{{ form.attributes?.wlan_rssi }} dBm</div>
                  <div class="flex gap-0.5 h-2 items-end">
                    <div class="w-0.5 rounded-full bg-current" :class="form.attributes?.wlan_rssi > -90 ? 'h-1' : 'h-1 opacity-20'"></div>
                    <div class="w-0.5 rounded-full bg-current" :class="form.attributes?.wlan_rssi > -80 ? 'h-1.5' : 'h-1.5 opacity-20'"></div>
                    <div class="w-0.5 rounded-full bg-current" :class="form.attributes?.wlan_rssi > -70 ? 'h-2' : 'h-2 opacity-20'"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Band -->
          <div class="px-6 py-2 lg:px-8">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-lg">
                <Radio class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Band</div>
                <div class="text-xs font-bold text-slate-900 dark:text-white">{{ form.attributes?.wlan_band }}</div>
              </div>
            </div>
          </div>

          <!-- SSID -->
          <div class="px-6 py-2 lg:px-8">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-lg">
                <Network class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Network (SSID)</div>
                <div class="text-xs font-bold text-slate-900 dark:text-white truncate max-w-[120px]">{{ form.attributes?.wlan_ssid }}</div>
              </div>
            </div>
          </div>

          <!-- Speed -->
          <div class="px-6 py-2 lg:px-8 last:pr-0">
            <div class="flex items-center gap-4">
              <div class="p-2 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-lg">
                <Activity class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Link Rate</div>
                <div class="text-xs font-bold text-slate-900 dark:text-white">
                  {{ (form.attributes?.wlan_tx_rate / 1000).toFixed(0) }} <span class="text-[10px] opacity-60">Mbps</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

        <!-- Availability Trend Chart -->
        <div class="premium-card">
          <div class="flex items-center justify-between mb-8">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <div class="w-1.5 h-6 bg-blue-500 rounded-full"></div>
              Network Availability History
            </h2>
            <div
              class="px-3 py-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-full text-[10px] font-black tracking-widest uppercase">
              Full Record
            </div>
          </div>

          <div class="h-64">
            <apexchart v-if="chartSeries && chartSeries[0].data.length > 0" type="area" height="100%"
              :options="chartOptions" :series="chartSeries"></apexchart>
            <div v-else class="h-full flex flex-col items-center justify-center text-slate-400 italic text-sm gap-2">
              <Loader2 class="w-5 h-5 animate-spin opacity-20" />
              <span>Collecting historical trend data...</span>
            </div>
          </div>

          <!-- Detailed Activity Log Table -->
          <div class="mt-8 pt-8 border-t border-slate-100 dark:border-slate-700/50">
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-4">
                <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 ml-1">Recent Activity Log
                </h3>
                <span class="text-[10px] font-bold text-slate-400">{{ historyTotal }} Events Recorded</span>
              </div>
              <div class="flex items-center gap-2" v-if="historyTotal > historyLimit">
                <button @click="changeHistoryPage(historyPage - 1)" :disabled="historyPage <= 1"
                  class="p-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-900 dark:hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                  <ChevronDown class="w-3 h-3 rotate-90" />
                </button>
                <span class="text-[9px] font-bold text-slate-400">
                  Page {{ historyPage }} of {{ Math.ceil(historyTotal / historyLimit) || 1 }}
                </span>
                <button @click="changeHistoryPage(historyPage + 1)"
                  :disabled="historyPage >= (Math.ceil(historyTotal / historyLimit) || 1)"
                  class="p-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-900 dark:hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                  <ChevronDown class="w-3 h-3 -rotate-90" />
                </button>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-2 pr-2">
              <div v-for="h in history" :key="h.id"
                class="flex items-center justify-between p-2 rounded-lg bg-white/50 dark:bg-slate-900/30 border border-slate-100 dark:border-slate-800/50 hover:border-blue-500/30 hover:shadow-sm hover:shadow-blue-500/5 transition-all group/item">
                <div class="flex items-center gap-2.5">
                  <div :class="h.status === 'online' ? 'bg-emerald-500 text-white' : 'bg-rose-500 text-white'"
                    class="w-7 h-7 rounded-md flex items-center justify-center shadow-sm shadow-black/5">
                    <component :is="h.status === 'online' ? Wifi : WifiOff" class="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span class="text-[9px] font-black uppercase tracking-widest leading-none"
                      :class="h.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
                      {{ h.status }}
                    </span>
                    <p class="text-[10px] text-slate-500 font-medium leading-tight">
                      {{ parseUTC(h.changed_at).toLocal().toFormat('HH:mm') }}
                    </p>
                  </div>
                </div>
                <div class="text-right">
                  <div class="text-[10px] font-bold text-slate-700 dark:text-slate-300">
                    {{ parseUTC(h.changed_at).toLocal().toFormat('MMM d') }}
                  </div>
                </div>
              </div>

              <div v-if="history.length === 0" class="py-12 text-center">
                <p class="text-xs text-slate-400 italic">No historical events recorded for this device yet.</p>
              </div>
            </div>
          </div>
        </div>






        <!-- Traffic History Chart -->
        <div class="premium-card">
          <div class="flex items-center justify-between mb-8">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <div class="w-1.5 h-6 bg-purple-500 rounded-full"></div>
              Network Traffic
            </h2>
          </div>

          <div class="h-64" v-if="device && device.traffic_history && device.traffic_history.length > 0">
            <apexchart type="area" height="100%" :options="trafficChartOptions" :series="trafficSeries"></apexchart>
          </div>
          <div v-else class="h-64 flex flex-col items-center justify-center text-slate-400 italic text-sm gap-2">
            <Activity class="w-5 h-5 opacity-20" />
            <span>No traffic history recorded yet.</span>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-4"
            v-if="device && device.traffic_history && device.traffic_history.length > 0">
            <div
              class="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4 border border-emerald-100 dark:border-emerald-800/30">
              <div class="text-[10px] font-black uppercase text-emerald-600 dark:text-emerald-400 mb-1">Total Download
              </div>
              <div class="text-xl font-bold text-slate-900 dark:text-white">{{ formatBytes(totalTraffic.down) }}</div>
            </div>
            <div class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800/30">
              <div class="text-[10px] font-black uppercase text-blue-600 dark:text-blue-400 mb-1">Total Upload</div>
              <div class="text-xl font-bold text-slate-900 dark:text-white">{{ formatBytes(totalTraffic.up) }}</div>
            </div>
          </div>
        </div>


        <!-- DNS Insights Card -->
        <div class="premium-card relative overflow-hidden">
          <!-- Background Decor -->
          <div class="absolute -top-12 -right-12 w-64 h-64 bg-purple-500/10 dark:bg-purple-400/5 rounded-full blur-3xl">
          </div>

          <div class="flex items-center justify-between mb-8 relative z-10">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <div class="w-1.5 h-6 bg-purple-500 rounded-full"></div>
              DNS Security Profile
            </h2>
            <div class="flex items-center gap-2">
              <ShieldCheck v-if="dnsDeviceStats && dnsDeviceStats.blocked === 0 && dnsDeviceStats.total > 0" class="w-4 h-4 text-emerald-500"></ShieldCheck>
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">Security Audit</span>
            </div>
          </div>

          <div v-if="dnsDeviceStats && dnsDeviceStats.total > 0" class="space-y-6 relative z-10">
            <!-- KPI Row -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div
                class="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-100 dark:border-slate-800">
                <div class="text-[10px] font-black uppercase text-slate-400 mb-1">Total Queries</div>
                <div class="text-2xl font-bold text-slate-900 dark:text-white">{{ dnsDeviceStats.total }}</div>
                <div class="text-[10px] text-slate-500 mt-1">Last 24 Hours</div>
              </div>
              <div class="p-4 bg-red-50 dark:bg-red-900/20 rounded-2xl border border-red-100 dark:border-red-800/30">
                <div class="text-[10px] font-black uppercase text-red-600 dark:text-red-400 mb-1">Blocked</div>
                <div class="text-2xl font-bold text-red-700 dark:text-red-400">{{ dnsDeviceStats.blocked }}</div>
                <div class="text-[10px] text-red-500/60 mt-1">Filtered by Policy</div>
              </div>
              <div
                class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-100 dark:border-blue-800/30">
                <div class="text-[10px] font-black uppercase text-blue-600 dark:text-blue-400 mb-1">Block Rate</div>
                <div class="text-2xl font-bold text-slate-900 dark:text-white">{{ dnsDeviceStats.block_rate }}%</div>
                <div class="text-[10px] text-blue-500/60 mt-1">Threat Mitigation</div>
              </div>
              <div
                class="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-2xl border border-emerald-100 dark:border-emerald-800/30">
                <div class="text-[10px] font-black uppercase text-emerald-600 dark:text-emerald-400 mb-1">Avg Latency
                </div>
                <div class="text-2xl font-bold text-slate-900 dark:text-white">{{ dnsDeviceStats.avg_latency }}<span
                    class="text-sm font-medium opacity-50 ml-1">ms</span></div>
                <div class="text-[10px] text-emerald-500/60 mt-1">Response Time</div>
              </div>
            </div>

            <!-- Health Score -->
            <div class="p-5 bg-white/50 dark:bg-slate-800/50 rounded-3xl border border-slate-100 dark:border-slate-700">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-slate-500">DNS Health Score</span>
                  <div class="w-1 h-1 bg-slate-300 rounded-full"></div>
                  <span class="text-[10px] font-bold"
                    :class="dnsDeviceStats.blocked > 0 ? 'text-amber-500' : 'text-emerald-500'">
                    {{ dnsDeviceStats.block_rate < 5 ? 'Excellent' : dnsDeviceStats.block_rate < 15 ? 'Good'
                      : 'Needs Review' }} </span>
                </div>
                <span class="text-xs font-black"
                  :class="dnsDeviceStats.blocked > 0 ? 'text-amber-500' : 'text-emerald-500'">
                  {{ Math.max(0, 100 - dnsDeviceStats.block_rate) }}%
                </span>
              </div>
              <div class="w-full h-2 by-slate-100 dark:bg-slate-700/50 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-1000"
                  :class="dnsDeviceStats.blocked > 0 ? 'bg-amber-500' : 'bg-emerald-500'"
                  :style="`width: ${Math.max(10, 100 - dnsDeviceStats.block_rate)}%`"></div>
              </div>
            </div>

            <!-- Recent Queries List -->
            <div class="space-y-4">
              <div class="flex items-center justify-between px-1">
                <div class="flex items-center gap-4">
                  <h3 class="text-[10px] font-black uppercase tracking-widest text-slate-400">Live Query Stream</h3>
                  <span class="text-[10px] font-bold text-slate-400">{{ dnsTotal }} Queries Recorded</span>
                </div>
                <div class="flex items-center gap-2" v-if="dnsTotal > dnsLimit">
                  <button @click="changeDnsPage(dnsPage - 1)" :disabled="dnsPage <= 1"
                    class="p-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-900 dark:hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                    <ChevronDown class="w-3 h-3 rotate-90" />
                  </button>
                  <span class="text-[9px] font-bold text-slate-400">
                    Page {{ dnsPage }} of {{ Math.ceil(dnsTotal / dnsLimit) || 1 }}
                  </span>
                  <button @click="changeDnsPage(dnsPage + 1)"
                    :disabled="dnsPage >= (Math.ceil(dnsTotal / dnsLimit) || 1)"
                    class="p-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-900 dark:hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                    <ChevronDown class="w-3 h-3 -rotate-90" />
                  </button>
                </div>
              </div>

              <div
                class="bg-slate-50/50 dark:bg-slate-900/30 rounded-3xl border border-slate-100 dark:border-slate-800/50 overflow-hidden">
                <div class="overflow-x-auto">
                  <table class="w-full text-left border-collapse">
                    <thead>
                      <tr class="border-b border-slate-100 dark:border-slate-800">
                        <th class="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Time</th>
                        <th class="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Domain</th>
                        <th class="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Status</th>
                        <th class="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-right">
                          Lat</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                      <tr v-for="(log, idx) in dnsLogs" :key="idx"
                        class="hover:bg-white dark:hover:bg-slate-800/50 transition-colors group">
                        <td class="py-2.5 px-4 whitespace-nowrap text-[10px] font-bold text-slate-400">
                          {{ formatRelativeTime(log.timestamp) }}
                        </td>
                        <td class="py-2.5 px-4">
                          <div class="flex flex-col max-w-[200px] lg:max-w-md">
                            <span class="truncate font-mono text-xs font-bold text-slate-700 dark:text-slate-200"
                              :title="log.domain">
                              {{ log.domain }}
                            </span>
                            <span v-if="log.category"
                              class="text-[8px] text-slate-400 font-bold uppercase tracking-tighter">{{ log.category
                              }}</span>
                          </div>
                        </td>
                        <td class="py-2.5 px-4">
                          <div class="flex items-center gap-2">
                            <span v-if="log.is_blocked"
                              class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800/50">
                              Block
                            </span>
                            <span v-else-if="log.status === 'Rewrite'"
                              class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/50">
                              Rewr
                            </span>
                            <span v-else
                              class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/50">
                              Allow
                            </span>
                          </div>
                        </td>
                        <td class="py-2.5 px-4 text-right">
                          <span class="text-xs font-mono font-bold text-slate-500">{{ log.response_time }}<span
                              class="text-[8px] opacity-70">ms</span></span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-if="dnsLogs.length === 0" class="py-16 text-center">
                  <Loader2 class="w-8 h-8 mx-auto mb-2 text-slate-200 animate-spin" />
                  <p class="text-xs text-slate-400 italic">Analysing real-time DNS stream...</p>
                </div>
              </div>
            </div>

          </div>
          <div v-else class="py-20 text-center text-slate-400">
            <ShieldAlert class="w-12 h-12 mx-auto mb-4 opacity-10" />
            <h3 class="text-slate-900 dark:text-white font-bold">No DNS Activity</h3>
            <p class="text-xs mt-1 opacity-60">Wait for this device to make queries or check AdGuard link.</p>
          </div>
        </div>
      </div>

      <!-- Column 3: Ports & Services (Sidebar) -->
      <div class="space-y-6">
        <!-- Health & Uptime Metrics (Sidebar Stack) -->
        <div class="space-y-4">
          <div
            class="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-3xl border border-slate-200 dark:border-slate-700/50 p-6 shadow-xl">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Longest Streak</div>
            <div class="text-2xl font-black text-emerald-500">{{ longestOnlineStreak }} <span
                class="text-xs font-medium text-slate-400">hours</span></div>
          </div>
          <div class="card-base">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Avg Offline</div>
            <div class="text-2xl font-black text-rose-500">{{ avgOfflineDuration }} <span
                class="text-xs font-medium text-slate-400">mins</span></div>
          </div>
          <div class="card-base">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Total Uptime</div>
            <div class="text-2xl font-black text-blue-500">{{ uptimePercentage }}%</div>
          </div>
        </div>

        <div class="premium-card">
          <!-- Background Decoration -->
          <div class="absolute -bottom-12 -right-12 w-48 h-48 bg-blue-500/10 dark:bg-blue-400/5 rounded-full blur-3xl pointer-events-none">
          </div>

          <div class="flex items-center justify-between mb-6 relative z-10">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <div class="w-1.5 h-6 bg-blue-500 rounded-full"></div>
              Port Lookup Results
            </h2>
            <button @click="runDeepScan" :disabled="isScanning" v-tooltip="'Run comprehensive port & service discovery'"
              class="group flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800/50 hover:bg-blue-600 hover:text-white transition-all disabled:opacity-50 relative z-20">
              <component :is="isScanning ? Loader2 : ScanSearch" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 group-hover:text-white" :class="{ 'animate-spin': isScanning }" />
              <span class="text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400 group-hover:text-white">{{ isScanning ? 'Auditing...' : 'Deep Audit' }}</span>
            </button>
          </div>

          <div v-if="parsedPorts.length > 0" class="space-y-3 relative z-10">
            <div v-for="port in parsedPorts" :key="port.port"
              class="group flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-700/50 hover:border-blue-500/30 rounded-2xl transition-all">
              <div class="flex items-center gap-4">
                <div class="flex flex-col items-center justify-center">
                  <div class="text-xs font-black text-blue-600 dark:text-blue-400 tracking-tighter">{{ port.port }}
                  </div>
                  <div class="text-[8px] font-black text-slate-500 uppercase">{{ port.protocol || 'TCP' }}</div>
                </div>
                <div>
                  <div class="text-sm font-bold text-slate-900 dark:text-white">{{ port.service || 'Unknown' }}</div>
                  <div class="text-[10px] text-slate-500 font-medium">Service Active</div>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button v-if="port.port === 22" @click="openSSH(port.port)"
                  class="p-2 transition-all rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-900 hover:text-white text-slate-600 dark:text-slate-300"
                  v-tooltip="'Terminal Access'">
                  <Terminal class="w-4 h-4" />
                </button>
                <a v-if="[80, 443, 8080, 8000, 3000].includes(port.port)" :href="`http://${device.ip}:${port.port}`"
                  target="_blank"
                  class="p-2 transition-all rounded-lg bg-blue-500/10 hover:bg-blue-500 text-blue-600 dark:text-blue-400 hover:text-white"
                  v-tooltip="'Open Interface'">
                  <ExternalLink class="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div class="p-6 bg-slate-50 dark:bg-slate-900/50 rounded-full">
              <ShieldAlert class="w-12 h-12 text-slate-300 dark:text-slate-600" />
            </div>
            <div>
              <p class="text-slate-900 dark:text-white font-bold">No Open Ports</p>
              <p class="text-xs text-slate-500 mt-1 max-w-[180px]">Run a Deep Scan to audit common network services.</p>
            </div>
          </div>

          <div class="mt-8 pt-8 border-t border-slate-100 dark:border-slate-700/50">
            <div
              class="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-slate-500">
              <span>Last Audit Scan</span>
              <span class="text-slate-400">{{ formatRelativeTime(device.last_seen) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <TerminalModal v-if="showTerminal" :device="device" :port="sshPort" @close="showTerminal = false" />
  </div>
</template>

<script setup>
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import { ref, onMounted, reactive, computed, watch } from 'vue'
import {
  ArrowLeft, Loader2, ScanSearch, Save, Search, ChevronDown, Activity, Terminal, ExternalLink, ShieldAlert, ShieldCheck,
  Wifi, WifiOff, Pencil, Info, X, Fingerprint, Globe, Calendar, Cpu, Copy, Check, Ban, Radio, Network
} from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import api from '@/utils/api'
import TerminalModal from '../components/TerminalModal.vue'
import { DateTime } from 'luxon'
import { formatRelativeTime, formatDate, parseUTC } from '@/utils/date'
import { useNotifications } from '@/composables/useNotifications'
import { useSystemStore } from '@/stores/system'
import { getIcon as resolveIcon } from '@/utils/icons'

const systemStore = useSystemStore()
const deviceTypes = computed(() => systemStore.deviceTypes)
const availableIcons = computed(() => systemStore.availableIcons)
const getIcon = (type) => resolveIcon(systemStore.getIcon(type))

const route = useRoute()
const device = ref(null)
const showTerminal = ref(false)
const sshPort = ref(22)

const allDevices = ref([])
const form = reactive({ 
  display_name: '', 
  name: '', 
  device_type: '', 
  icon: '', 
  brand: '', 
  brand_icon: '', 
  ip_type: '', 
  parent_id: null, 
  attributes: {} 
})

const isScanning = ref(false)
const history = ref([])
const historyPage = ref(1)
const historyLimit = ref(5)
const historyTotal = ref(0)
const fidelityHistory = ref([])
const { notifySuccess, notifyError } = useNotifications()
const isSaving = ref(false)

const isCategoryOpen = ref(false)
const isIPOpen = ref(false)
const isParentOpen = ref(false)
const categorySearch = ref('')
const iconSearch = ref('')
const parentSearch = ref('')
const brandSearch = ref('')

// getIcon is now imported from @/utils/icons

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
  const others = allDevices.value.filter(d => d.id !== device.value?.id)
  if (!parentSearch.value) return others
  const s = parentSearch.value.toLowerCase()
  return others.filter(d =>
    (d.display_name || '').toLowerCase().includes(s) ||
    (d.name || '').toLowerCase().includes(s) ||
    (d.ip || '').includes(s)
  )
})

const getParentLabel = computed(() => {
  if (!form.parent_id) return 'Main Gateway (Default)'
  const p = allDevices.value.find(d => d.id === form.parent_id)
  return p ? (p.display_name || p.name || p.ip) : 'Unknown Device'
})

watch(() => form.device_type, (newType) => {
  if (newType && systemStore.iconMap[newType]) {
    form.icon = systemStore.iconMap[newType]
  }
})
const formatTime = (ts) => {
  return formatDate(ts)
}

const getIPAllocationLabel = (val) => {
  if (val === 'static') return 'Static IP'
  return 'Dynamic (DHCP)'
}

const toggleBlock = async () => {
  if (!device.value) return
  if (!device.value.mac || device.value.mac === 'unknown' || device.value.mac === 'N/A') {
    notify('Error', 'Cannot block device without a valid MAC address', 'error')
    return
  }
  const isCurrentlyBlocked = device.value.is_blocked
  const action = isCurrentlyBlocked ? 'unblock' : 'block'
  
  try {
    const res = await api.post(`/integrations/openwrt/devices/${device.value.mac}/${action}`)
    if (res.data.status === 'success') {
      device.value.is_blocked = !isCurrentlyBlocked
      notify(
        'Success', 
        `Device ${isCurrentlyBlocked ? 'unblocked' : 'blocked'} successfully`, 
        'success'
      )
    }
  } catch (err) {
    notify('Error', err.response?.data?.detail || `Failed to ${action} device`, 'error')
  }
}

const approveDevice = async () => {
  try {
    await api.patch(`/devices/${device.value.id}`, { is_trusted: true })
    await fetchDevice()
    notifySuccess('Device approved successfully')
  } catch (e) {
    notifyError('Failed to approve device')
  }
}

const fetchAllDevices = async () => {
  try {
    const res = await api.get('/devices/?limit=-1')
    allDevices.value = res.data.items || []
  } catch (e) {
    console.error('Failed to fetch devices:', e)
  }
}

const fetchHistory = async () => {
  try {
    const offset = (historyPage.value - 1) * historyLimit.value
    const res = await api.get(`/events/device/${route.params.id}?limit=${historyLimit.value}&offset=${offset}`)
    history.value = res.data

    // Fetch total count for pagination
    const countRes = await api.get(`/events/device/${route.params.id}/count`)
    historyTotal.value = countRes.data.total

    // Also fetch high-fidelity data for the chart (independent of pagination)
    const fidelityRes = await api.get(`/events/device/${route.params.id}/fidelity?hours=24`)
    fidelityHistory.value = fidelityRes.data
  } catch (e) {
    console.error("Failed to fetch history:", e)
  }
}

const dnsDeviceStats = ref(null)
const dnsLogs = ref([])
const dnsPage = ref(1)
const dnsLimit = ref(10)
const dnsTotal = ref(0)

const fetchDeviceDns = async () => {
  try {
    const offset = (dnsPage.value - 1) * dnsLimit.value
    const [statsRes, logsRes, countRes] = await Promise.all([
      api.get(`/analytics/dns/stats/${route.params.id}`),
      api.get(`/analytics/dns/logs/${route.params.id}?limit=${dnsLimit.value}&offset=${offset}`),
      api.get(`/analytics/dns/logs/${route.params.id}/count`)
    ])
    dnsDeviceStats.value = statsRes.data
    dnsLogs.value = logsRes.data
    dnsTotal.value = countRes.data.total
  } catch (e) {
    console.error("Failed to fetch device DNS data:", e)
  }
}

const changeDnsPage = (newPage) => {
  if (newPage < 1) return
  const maxPage = Math.ceil(dnsTotal.value / dnsLimit.value) || 1
  if (newPage > maxPage) return

  dnsPage.value = newPage
  fetchDeviceDns()
}

const changeHistoryPage = (newPage) => {
  if (newPage < 1) return
  const maxPage = Math.ceil(historyTotal.value / historyLimit.value) || 1
  if (newPage > maxPage) return

  historyPage.value = newPage
  fetchHistory()
}

onMounted(() => {
  fetchDevice()
  fetchHistory()
  fetchAllDevices()
  fetchDeviceDns()
})



const longestOnlineStreak = computed(() => {
  let maxHours = 0
  let currentStreak = 0
  const sorted = [...history.value].reverse()
  const now = DateTime.now().toUTC()

  for (let i = 0; i < sorted.length; i++) {
    const start = parseUTC(sorted[i].changed_at)
    const end = (i < sorted.length - 1) ? parseUTC(sorted[i + 1].changed_at) : now

    if (sorted[i].status === 'online') {
      const diffHours = end.diff(start, 'hours').hours
      if (diffHours > 0) currentStreak += diffHours
    } else {
      maxHours = Math.max(maxHours, currentStreak)
      currentStreak = 0
    }
  }
  return Math.round(Math.max(maxHours, currentStreak))
})

const avgOfflineDuration = computed(() => {
  if (history.value.length === 0) return 0

  let totalMins = 0
  let counts = 0

  const sorted = [...history.value].reverse()
  const now = DateTime.now().toUTC()

  for (let i = 0; i < sorted.length; i++) {
    const start = parseUTC(sorted[i].changed_at)
    const end = (i < sorted.length - 1) ? parseUTC(sorted[i + 1].changed_at) : now

    if (sorted[i].status === 'offline') {
      const diffMins = end.diff(start, 'minutes').minutes
      if (diffMins > 0) {
        totalMins += diffMins
        counts++
      }
    }
  }
  return counts > 0 ? Math.round(totalMins / counts) : 0
})

const availabilitySummary = computed(() => {
  // Create 24 blocks for the last 24 hours
  const blocks = []
  const now = DateTime.now().toUTC()

  for (let i = 23; i >= 0; i--) {
    const blockTime = now.minus({ hours: i })
    const label = blockTime.toFormat('HH:mm')

    // Find history event closest to this time
    // For now, simpler: check if device was online in that window
    // Higher fidelity: find last status before this window
    const eventInWindow = history.value.find(e => {
      const et = parseUTC(e.changed_at)
      return et <= blockTime
    })

    blocks.push({
      time: i,
      label,
      status: eventInWindow ? eventInWindow.status : (device.value?.status || 'unknown')
    })
  }
  return blocks
})

const uptimePercentage = computed(() => {
  if (availabilitySummary.value.length === 0) return 0
  const onlineCount = availabilitySummary.value.filter(b => b.status === 'online').length
  return Math.round((onlineCount / availabilitySummary.value.length) * 100)
})

const chartOptions = computed(() => ({
  chart: {
    id: 'device-availability',
    toolbar: { show: false },
    background: 'transparent',
    animations: { enabled: true, easing: 'easeinout', speed: 800 },
    fontFamily: 'inherit',
    dropShadow: {
      enabled: true,
      top: 10,
      left: 0,
      blur: 10,
      color: '#3b82f6',
      opacity: 0.15
    }
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 },
      datetimeFormatter: {
        year: 'yyyy',
        month: 'MMM',
        day: 'dd MMM',
        hour: 'HH:mm'
      }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    labels: { show: false },
    min: 0,
    max: 1.1,
    tickAmount: 1
  },
  grid: {
    borderColor: 'rgba(148, 163, 184, 0.05)',
    strokeDashArray: 6,
    padding: { left: 0, right: 0 }
  },
  tooltip: {
    theme: 'dark',
    x: { format: 'MMM dd, HH:mm' },
    y: {
      formatter: (val) => val === 1 ? 'Online' : 'Offline'
    }
  },
  colors: ['#3b82f6'],
  stroke: { curve: 'smooth', width: 4 },
  markers: {
    size: 0,
    hover: {
      size: 6,
      colors: ['#3b82f6'],
      strokeColors: '#fff',
      strokeWidth: 3
    }
  },
  dataLabels: { enabled: false },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.5,
      opacityTo: 0.0,
      stops: [0, 90, 100],
      colorStops: [
        { offset: 0, color: "#3b82f6", opacity: 0.5 },
        { offset: 100, color: "#3b82f6", opacity: 0 }
      ]
    }
  }
}))

const chartSeries = computed(() => {
  if (!fidelityHistory.value || fidelityHistory.value.length === 0) return [{ name: 'Status', data: [] }]

  return [{
    name: 'Status',
    data: fidelityHistory.value
      .filter(h => h && h.timestamp)
      .map(h => {
        const ts = parseUTC(h.timestamp).toMillis()
        return {
          x: isNaN(ts) ? 0 : ts,
          y: h.status === 'online' ? 1 : 0
        }
      })
      .filter(p => p.x > 0)
  }]
})

const formatBytes = (bytes, decimals = 2) => {
  if (!+bytes) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}
const totalTraffic = computed(() => {
  if (!device.value?.traffic_history) return { down: 0, up: 0 }
  return device.value.traffic_history.reduce((acc, curr) => ({
    down: acc.down + (curr.down || 0),
    up: acc.up + (curr.up || 0)
  }), { down: 0, up: 0 })
})

const trafficSeries = computed(() => {
  if (!device.value?.traffic_history) return []
  const mapped = device.value.traffic_history.map(h => {
    const ts = parseUTC(h.timestamp).toMillis()
    return {
      ts: isNaN(ts) ? 0 : ts,
      down: h.down || 0,
      up: h.up || 0
    }
  }).filter(d => d.ts > 0)

  return [
    { name: 'Download', data: mapped.map(d => ({ x: d.ts, y: d.down })) },
    { name: 'Upload', data: mapped.map(d => ({ x: d.ts, y: d.up })) }
  ]
})

const trafficChartOptions = computed(() => ({
  chart: {
    id: 'device-traffic',
    toolbar: { show: false },
    background: 'transparent',
    fontFamily: 'inherit',
    zoom: { enabled: false }
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 },
      datetimeFormatter: { year: 'yyyy', month: 'MMM', day: 'dd MMM', hour: 'HH:mm' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
    tooltip: { enabled: false }
  },
  yaxis: {
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px', fontFamily: 'inherit' },
      formatter: (val) => formatBytes(val, 0)
    },
  },
  grid: {
    borderColor: 'rgba(148, 163, 184, 0.05)',
    strokeDashArray: 4,
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  colors: ['#10b981', '#3b82f6'], // Emerald (Down), Blue (Up)
  fill: {
    type: 'gradient',
    gradient: {
      opacityFrom: 0.5,
      opacityTo: 0.1,
    }
  },
  tooltip: {
    theme: 'dark',
    x: { format: 'MMM dd, HH:mm' },
    y: { formatter: (val) => formatBytes(val) }
  },
  legend: {
    position: 'top',
    horizontalAlign: 'right'
  }
}))

const parsedPorts = computed(() => {
  if (!device.value || !device.value.open_ports) return []

  let data = device.value.open_ports
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch {
      return []
    }
  }

  if (Array.isArray(data) && data.length > 0) {
    let normalized = []
    if (typeof data[0] === 'number') {
      const commonMap = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 80: 'HTTP', 443: 'HTTPS', 445:
          'SMB', 3000: 'React', 8080: 'Web', 3306: 'MySQL', 5432: 'Postgres'
      }
      normalized = data.map(p => ({ port: p, service: commonMap[p] || 'Unknown', protocol: 'tcp' }))
    } else {
      // Already loaded as objects {port, service, protocol}
      // Normalize protocol and filter out exact duplicates
      normalized = data.map(p => ({ ...p, protocol: (p.protocol || 'tcp').toLowerCase() }))
    }

    // Strict de-duplication by port (since we only handle TCP for now)
    const seen = new Set()
    return normalized.filter(p => {
      const key = `${p.port}-${p.protocol}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  }
  return []
})

const isChanged = computed(() => {
  if (!device.value) return false
  return (
    form.display_name !== (device.value.display_name || '') ||
    form.name !== (device.value.name || '') ||
    form.device_type !== (device.value.device_type || '') ||
    form.icon !== (device.value.icon || '') ||
    form.ip_type !== (device.value.ip_type || 'dynamic') ||
    form.parent_id !== (device.value.parent_id || null)
  )
})

const runDeepScan = async () => {
  if (isScanning.value) return
  isScanning.value = true
  try {
    await api.post(`/scans/audit/${device.value.id}`)
    await fetchDevice() // Refresh details to show new ports
    notifySuccess('Port scan complete')
  } catch (e) {
    notifyError('Scan failed: ' + (e.response?.data?.detail || e.message))
  } finally {
    isScanning.value = false
  }
}

const openSSH = (port) => {
  sshPort.value = port
  showTerminal.value = true
}

const copyToClipboard = async (text) => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    notifySuccess('Copied to clipboard')
  } catch (e) {
    notifyError('Failed to copy')
  }
}


const updateFields = async (updates, successMsg = 'Identity updated') => {
  // Update local state immediately for UI snappiness
  Object.assign(form, updates)
  try {
    await api.patch(`/devices/${route.params.id}`, updates)
    notifySuccess(successMsg)
    // Refresh device state to ensure consistency across the page
    const response = await api.get(`/devices/${route.params.id}`)
    device.value = response.data
  } catch (e) {
    notifyError('Failed to update identity')
    console.error('Update failed:', e)
  }
}

watch(() => form.device_type, (newType) => {
  if (newType && systemStore.iconMap[newType] && !form.icon.startsWith('/static/')) {
    // Only auto-update icon if it's a standard one, don't overwrite custom brand icons
    form.icon = systemStore.iconMap[newType]
  }
})

const fetchDevice = async () => {
  try {
    const response = await api.get(`/devices/${route.params.id}`)
    device.value = response.data
    Object.assign(form, {
      display_name: device.value.display_name || '',
      name: device.value.name || '',
      device_type: device.value.device_type || '',
      icon: device.value.icon || '',
      brand: device.value.brand || '',
      brand_icon: device.value.brand_icon || '',
      ip_type: device.value.ip_type || 'dynamic',
      parent_id: device.value.parent_id || null,
      attributes: device.value.attributes || {}
    })
  } catch (error) {
    console.error('Failed to fetch device details', error)
  }
}

const saveChanges = async () => {
  if (isSaving.value) return
  isSaving.value = true
  try {
    await api.patch(`/devices/${route.params.id}`, form)
    notifySuccess('Device configuration updated')
    await fetchDevice()
  } catch (e) {
    notifyError('Failed to save changes')
  } finally {
    isSaving.value = false
  }
}

onMounted(async () => {
  await fetchDevice()
  systemStore.fetchConstants()
  
  // Also fetch all devices for parent selection
  try {
    const res = await api.get('/devices/?limit=-1')
    allDevices.value = res.data.items || []
  } catch (e) {
    console.error('Failed to fetch all devices:', e)
  }
})


</script>
