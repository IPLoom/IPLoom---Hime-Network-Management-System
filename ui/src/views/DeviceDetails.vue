<template>
  <div v-if="device" class="space-y-6 max-w-7xl mx-auto pb-12">
    <!-- Header Area -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex items-center gap-4">
        <router-link to="/devices" class="btn-action !p-2.5 rounded-xl" v-tooltip="'Back to Device List'">
          <ArrowLeft class="w-5 h-5" />
        </router-link>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-2xl font-bold text-slate-900 dark:text-white leading-tight">
              {{ form.display_name || device.name || 'Unnamed Device' }}
            </h1>
            <ShieldCheck v-if="device.is_trusted" class="w-5 h-5 text-emerald-500" v-tooltip="'Verified & Trusted'" />
            <div :class="[
              device.status === 'online' ? 'bg-emerald-500' : 'bg-slate-400',
              'w-2 h-2 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]'
            ]"></div>
          </div>
          <p class="text-sm font-mono text-slate-500 dark:text-slate-400 mt-1.5 flex items-center gap-2">
            <span class="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] font-bold">IP</span>
            {{ device.ip }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button @click="runDeepScan" :disabled="isScanning" class="btn-action"
          v-tooltip="'Deep Port Audit (Scan top 1000 ports)'">
          <component :is="isScanning ? Loader2 : ScanSearch" class="w-5 h-5" :class="{ 'animate-spin': isScanning }" />
        </button>
        <button @click="saveChanges"
          class="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
          v-tooltip="'Save Device Configuration'">
          <Save class="w-5 h-5" />
        </button>
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
              <ShieldCheck class="w-5 h-5" /> Approve
            </button>
          </div>
        </div>

        <!-- Device Info Card -->
        <div class="premium-card group">
          <div
            class="absolute top-0 right-0 p-8 opacity-5 dark:opacity-10 group-hover:opacity-10 dark:group-hover:opacity-20 transition-opacity">
            <component :is="getIcon(form.icon || device.icon)" class="w-32 h-32" />
          </div>

          <h2 class="text-lg font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <div class="w-1.5 h-6 bg-blue-500 rounded-full"></div>
            Device Identification
          </h2>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
            <div class="space-y-1">
              <label
                class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Display
                Name</label>
              <input v-model="form.display_name" type="text" placeholder="Friendly Name"
                class="input-base px-4 py-3 bg-white/50 dark:bg-slate-900/50 rounded-2xl" />
            </div>

            <div class="space-y-1">
              <label
                class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Device
                Category</label>
              <div class="relative w-full group" v-click-outside="() => isCategoryOpen = false">
                <button @click="isCategoryOpen = !isCategoryOpen"
                  class="input-base flex items-center justify-between px-4 py-3 bg-white/50 dark:bg-slate-900/50 rounded-2xl">
                  <div class="flex items-center gap-2.5">
                    <span class="truncate">{{ form.device_type || 'Select Category' }}</span>
                  </div>
                  <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                    :class="{ 'rotate-180': isCategoryOpen }" />
                </button>

                <transition enter-active-class="transition duration-100 ease-out"
                  enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
                  leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100"
                  leave-to-class="transform scale-95 opacity-0">
                  <div v-if="isCategoryOpen"
                    class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-1.5 overflow-hidden">
                    <div class="px-3 py-2 border-b border-slate-100 dark:border-slate-700/50">
                      <div
                        class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg border border-transparent focus-within:border-blue-500/30 transition-colors">
                        <Search class="w-3.5 h-3.5 text-slate-400" />
                        <input v-model="categorySearch" @click.stop type="text" placeholder="Search..."
                          class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400"
                          autofocus />
                      </div>
                    </div>
                    <div class="overflow-y-auto max-h-60 custom-scrollbar">
                      <button v-for="type in filteredDeviceTypes" :key="type"
                        @click="form.device_type = type; isCategoryOpen = false; categorySearch = ''"
                        class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                        :class="form.device_type === type ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                        {{ type }}
                      </button>
                      <div v-if="filteredDeviceTypes.length === 0" class="px-4 py-3 text-xs text-slate-400 text-center">
                        No matches found
                      </div>
                    </div>
                  </div>
                </transition>
              </div>
            </div>

            <div class="space-y-1">
              <label
                class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Icon
                Selection</label>
              <Popover class="relative">
                <PopoverButton
                  class="input-base flex items-center justify-between px-4 py-3 bg-white/50 dark:bg-slate-900/50 rounded-2xl">
                  <div class="flex items-center gap-3">
                    <component :is="getIcon(form.icon)" class="w-5 h-5 text-blue-500" />
                    <span class="text-sm font-medium">{{ form.icon || 'Select Icon' }}</span>
                  </div>
                  <ChevronDown class="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
                </PopoverButton>

                <transition enter-active-class="transition duration-200 ease-out"
                  enter-from-class="translate-y-1 opacity-0" enter-to-class="translate-y-0 opacity-100"
                  leave-active-class="transition duration-150 ease-in" leave-from-class="translate-y-0 opacity-100"
                  leave-to-class="translate-y-1 opacity-0">
                  <PopoverPanel
                    class="absolute z-50 bottom-full mb-3 right-0 w-[260px] bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl shadow-2xl overflow-hidden flex flex-col">
                    <div class="p-3 border-b border-slate-100 dark:border-slate-700/50">
                      <div
                        class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg border border-transparent focus-within:border-blue-500/30 transition-colors">
                        <Search class="w-3.5 h-3.5 text-slate-400" />
                        <input v-model="iconSearch" type="text" placeholder="Find icon..."
                          class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                      </div>
                    </div>
                    <div class="p-4 overflow-y-auto max-h-[220px] custom-scrollbar">
                      <div class="grid grid-cols-4 gap-2">
                        <button v-for="iconName in filteredIcons" :key="iconName" type="button"
                          @click="form.icon = iconName"
                          class="p-3 rounded-xl transition-all flex items-center justify-center"
                          :class="form.icon === iconName ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'"
                          v-tooltip="iconName">
                          <component :is="getIcon(iconName)" class="w-5 h-5" />
                        </button>
                      </div>
                      <div v-if="filteredIcons.length === 0" class="py-2 text-xs text-slate-400 text-center">
                        No icons found
                      </div>
                    </div>
                  </PopoverPanel>
                </transition>
              </Popover>
            </div>

            <div class="space-y-1">
              <label
                class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Network
                Hostname</label>
              <input v-model="form.name" type="text"
                class="input-base px-4 py-3 bg-white/50 dark:bg-slate-900/50 rounded-2xl font-mono text-sm" />
            </div>

            <div class="space-y-1">
              <label class="text-[10px] font-black uppercase tracking-widest text_slate-400 dark:text-slate-500 ml-1">IP
                Reservation</label>
              <div class="relative w-full group" v-click-outside="() => isIPOpen = false">
                <button @click="isIPOpen = !isIPOpen"
                  class="input-base flex items-center justify-between px-4 py-3 bg-white/50 dark:bg-slate-900/50 rounded-2xl">
                  <span class="truncate">{{ getIPAllocationLabel(form.ip_type) }}</span>
                  <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                    :class="{ 'rotate-180': isIPOpen }" />
                </button>

                <transition enter-active-class="transition duration-100 ease-out"
                  enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
                  leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100"
                  leave-to-class="transform scale-95 opacity-0">
                  <div v-if="isIPOpen"
                    class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-1.5 overflow-hidden">
                    <button @click="form.ip_type = 'dynamic'; isIPOpen = false"
                      class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                      :class="form.ip_type === 'dynamic' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                      Dynamic (DHCP)
                    </button>
                    <button @click="form.ip_type = 'static'; isIPOpen = false"
                      class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                      :class="form.ip_type === 'static' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                      Static IP
                    </button>
                  </div>
                </transition>
              </div>
            </div>

            <div class="space-y-1">
              <label
                class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Connected
                Via (Parent)</label>
              <div class="relative w-full group" v-click-outside="() => isParentOpen = false">
                <button @click="isParentOpen = !isParentOpen"
                  class="input-base flex items-center justify-between px-4 py-3 bg-white/50 dark:bg-slate-900/50 rounded-2xl">
                  <span class="truncate">{{ getParentLabel }}</span>
                  <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                    :class="{ 'rotate-180': isParentOpen }" />
                </button>

                <transition enter-active-class="transition duration-100 ease-out"
                  enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
                  leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100"
                  leave-to-class="transform scale-95 opacity-0">
                  <div v-if="isParentOpen"
                    class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-1.5 overflow-hidden">
                    <div class="px-3 py-2 border-b border-slate-100 dark:border-slate-700/50">
                      <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                        <Search class="w-3.5 h-3.5 text-slate-400" />
                        <input v-model="parentSearch" @click.stop type="text" placeholder="Search devices..."
                          class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                      </div>
                    </div>
                    <div class="max-h-60 overflow-y-auto custom-scrollbar">
                      <button @click="form.parent_id = null; isParentOpen = false"
                        class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                        :class="!form.parent_id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                        Main Gateway (Default)
                      </button>
                      <button v-for="d in filteredPotentialParents" :key="d.id"
                        @click="form.parent_id = d.id; isParentOpen = false"
                        class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                        :class="form.parent_id === d.id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                        <component :is="getIcon(d.icon)" class="w-4 h-4 opacity-70" />
                        <span>{{ d.display_name || d.name || d.ip }}</span>
                      </button>
                    </div>
                  </div>
                </transition>
              </div>
            </div>
          </div>

          <div
            class="mt-8 pt-8 border-t border-slate-100 dark:border-slate-700/50 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-6">
            <div>
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Category</div>
              <div class="text-sm font-bold text-slate-900 dark:text-white">{{ device.device_type || 'Unknown' }}</div>
            </div>
            <div>
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Manufacturer</div>
              <div class="text-sm font-bold text-slate-900 dark:text-white">{{ device.vendor || 'Unknown' }}</div>
            </div>
            <div>
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">MAC Signature</div>
              <div class="text-sm font-mono text-slate-600 dark:text-slate-400">{{ device.mac || 'N/A' }}</div>
            </div>
            <div>
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">First Seen</div>
              <div class="text-sm font-bold text-slate-900 dark:text-white">{{ formatTime(device.first_seen) }}</div>
            </div>
            <div>
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Network Path</div>
              <div class="text-sm font-bold text-slate-900 dark:text-white">{{ device.internet_path || 'Local LAN' }}
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
              <ShieldCheck v-if="dnsDeviceStats && dnsDeviceStats.blocked === 0 && dnsDeviceStats.total > 0"
                class="w-4 h-4 text-emerald-500" />
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
          <div class="absolute -bottom-12 -right-12 w-48 h-48 bg-blue-500/10 dark:bg-blue-400/5 rounded-full blur-3xl">
          </div>

          <h2 class="text-lg font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <div class="w-1.5 h-6 bg-blue-500 rounded-full"></div>
            Port Lookup Results
          </h2>

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

  </div>

  <TerminalModal v-if="showTerminal" :device="device" :port="sshPort" @close="showTerminal = false" />

</template>

<script setup>
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import { ref, onMounted, reactive, computed, watch } from 'vue'
import {
  ArrowLeft, Loader2, ScanSearch, Save, Search, ChevronDown, Activity, Terminal, ExternalLink, ShieldAlert, ShieldCheck,
  Wifi, WifiOff
} from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import api from '@/utils/api'
import TerminalModal from '../components/TerminalModal.vue'
import { DateTime } from 'luxon'
import { formatRelativeTime, formatDate, parseUTC } from '@/utils/date'
import { useNotifications } from '@/composables/useNotifications'
import { getIcon } from '@/utils/icons'
import { deviceTypes, availableIcons, typeToIconMap } from '@/constants/devices'

const route = useRoute()
const device = ref(null)
const showTerminal = ref(false)
const sshPort = ref(22)

const allDevices = ref([])
const form = reactive({ display_name: '', name: '', device_type: '', icon: '', ip_type: '', parent_id: null, attributes: {} })

const isScanning = ref(false)
const history = ref([])
const historyPage = ref(1)
const historyLimit = ref(5)
const historyTotal = ref(0)
const fidelityHistory = ref([])
const { notifySuccess, notifyError } = useNotifications()

const isCategoryOpen = ref(false)
const isIPOpen = ref(false)
const isParentOpen = ref(false)
const categorySearch = ref('')
const iconSearch = ref('')
const parentSearch = ref('')

// getIcon is now imported from @/utils/icons

const filteredDeviceTypes = computed(() => {
  if (!categorySearch.value) return deviceTypes
  return deviceTypes.filter(t => t.toLowerCase().includes(categorySearch.value.toLowerCase()))
})

const filteredIcons = computed(() => {
  if (!iconSearch.value) return availableIcons
  return availableIcons.filter(k => k.toLowerCase().includes(iconSearch.value.toLowerCase()))
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
  if (newType && typeToIconMap[newType]) {
    form.icon = typeToIconMap[newType]
  }
})
const formatTime = (ts) => {
  return formatDate(ts)
}

const getIPAllocationLabel = (val) => {
  if (val === 'static') return 'Static IP'
  return 'Dynamic (DHCP)'
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

const fetchDevice = async () => {
  try {
    const response = await api.get(`/devices/${route.params.id}`)
    device.value = response.data
    Object.assign(form, {
      display_name: device.value.display_name || '',
      name: device.value.name || '',
      device_type: device.value.device_type || '',
      icon: device.value.icon || '',
      ip_type: device.value.ip_type || 'dynamic',
      parent_id: device.value.parent_id || null,
      attributes: device.value.attributes || {}
    })
  } catch (error) {
    console.error('Failed to fetch device details', error)
  }
}

const saveChanges = async () => {
  try {
    await api.patch(`/devices/${route.params.id}`, form)
    notifySuccess('Device configuration updated')
    await fetchDevice()
    fetchAllDevices() // Refresh list for parent labels elsewhere if needed
  } catch (e) {
    notifyError('Failed to save changes')
  }
}


</script>
```