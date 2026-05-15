<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Settings</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">System configuration and preferences</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="saveSettings" :disabled="saveStatus === 'saving'" class="btn-action"
          :class="{ '!text-emerald-500 !dark:text-emerald-400 !border-emerald-200 !dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20': saveStatus === 'saved' }"
          v-tooltip="saveStatus === 'saved' ? 'Saved' : 'Save Configuration'">
          <Loader2 v-if="saveStatus === 'saving'" class="w-5 h-5 animate-spin" />
          <Check v-else-if="saveStatus === 'saved'" class="w-5 h-5" />
          <Save v-else class="w-5 h-5" />
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Main Content (Left Column) -->
      <div class="lg:col-span-2 space-y-6">

        <!-- Automated Discovery -->
        <div class="glass-panel">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
              <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">Automated Discovery</h2>
              <p class="text-xs text-slate-500">Configure background network scanning</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Left: Subnets -->
            <div class="space-y-3">
              <label class="label-caps">
                Target Subnets
              </label>
              <div class="flex gap-2">
                <input v-model="newSubnet" @keyup.enter="addSubnet" type="text" placeholder="e.g. 192.168.1.0/24"
                  class="input-base !pl-3" :class="{ 'border-red-500': subnetError }" />
                <button @click="addSubnet"
                  class="p-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:opacity-90 transition-opacity"
                  v-tooltip="'Add Subnet'">
                  <Plus class="w-5 h-5" />
                </button>
              </div>
              <p v-if="subnetError" class="text-xs text-red-500 font-medium animate-pulse">{{ subnetError }}</p>

              <div class="flex flex-wrap gap-2 pt-1">
                <div v-for="s in subnetList" :key="s" class="badge-pill !px-3 !py-1 flex items-center gap-2">
                  <span>{{ s }}</span>
                  <button @click="removeSubnet(s)" class="text-slate-400 hover:text-red-500 transition-colors"
                    v-tooltip="'Remove Subnet'">
                    <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div v-if="subnetList.length === 0" class="text-sm text-slate-400 italic">
                  No subnets configured
                </div>
              </div>
            </div>

            <!-- Right: Schedule -->
            <div class="space-y-4">
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Scan Interval
                </label>
                <div class="relative">
                  <select v-model="settings.scan_interval" class="box-input appearance-none">
                    <option value="300">Every 5 minutes</option>
                    <option value="600">Every 10 minutes</option>
                    <option value="1800">Every 30 minutes</option>
                    <option value="3600">Every hour</option>
                    <option value="86400">Once per day</option>
                  </select>
                  <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Last Run
                </label>
                <div
                  class="px-3 py-2 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                  {{ formatLastRun(settings.last_discovery_run_at) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- MQTT Configuration -->
        <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-purple-600 dark:text-purple-400">
              <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2">
                <path
                  d="M8.25 3v1.5M4.5 8.25H3m12.375-3.75a8.25 8.25 0 018.25 8.25H21M6.75 3a12 12 0 0112 12H16.5M3 13.5a8.25 8.25 0 018.25-8.25V6a7.5 7.5 0 00-7.5 7.5v.75m17.625 0V15a6 6 0 01-6 6H12m0 0V21" />
              </svg>
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">MQTT Configuration</h2>
              <p class="text-xs text-slate-500">Integration with Home Assistant</p>
            </div>
            <div class="ml-auto flex items-center gap-3">
              <label class="premium-switch group">
                <span class="premium-switch-label">Integration Enabled</span>
                <div class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="settings.mqtt_enabled" class="sr-only peer">
                  <div class="premium-switch-slider peer-checked:bg-purple-600"></div>
                </div>
              </label>

              <div v-if="mqttStatus"
                class="flex items-center gap-2 px-3 py-1.5 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 mr-2">
                <div class="w-2 h-2 rounded-full"
                  :class="mqttStatus === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'"></div>
                <span class="text-xs font-medium"
                  :class="mqttStatus === 'online' ? 'text-emerald-600' : 'text-red-500'">
                  {{ mqttStatus === 'online' ? 'Online' : 'Offline' }}
                </span>
              </div>
              <button @click="testMqtt" :disabled="testLoading"
                class="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-500 dark:text-slate-400"
                v-tooltip="'Test Connection'">
                <Loader2 v-if="testLoading" class="w-4 h-4 animate-spin" />
                <svg v-else viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>
            </div>
          </div>
          <div class="space-y-4">
            <!-- Connection Details -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="md:col-span-2">
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Broker
                  Address</label>
                <input v-model="settings.mqtt_broker" type="text" placeholder="localhost" class="box-input" />
              </div>
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Port</label>
                <input v-model="settings.mqtt_port" type="text" placeholder="1883" class="box-input" />
              </div>
            </div>

            <!-- Authentication & Topic -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-slate-100 dark:border-slate-700 pt-4">
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Username
                  (Optional)</label>
                <input v-model="settings.mqtt_username" type="text" placeholder="mqtt_user" autocomplete="off"
                  class="box-input" />
              </div>
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Password
                  (Optional)</label>
                <input v-model="settings.mqtt_password" type="password" placeholder="••••••••"
                  autocomplete="new-password" class="box-input" />
              </div>
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Base
                  Topic</label>
                <input v-model="settings.mqtt_base_topic" type="text" placeholder="network_scanner" class="box-input" />
              </div>
            </div>
          </div>
        </div>

        <!-- OpenWRT Integration -->
        <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-400">
              <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2">
                <path
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">OpenWRT Integration</h2>
              <p class="text-xs text-slate-500">Sync leases & traffic from Router (Pull Model)</p>
            </div>
            <!-- Status Badge & Toggle -->
            <div class="ml-auto flex items-center gap-3">
              <label class="premium-switch group">
                <span class="premium-switch-label">Integration Enabled</span>
                <div class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="settings.openwrt_enabled" class="sr-only peer">
                  <div class="premium-switch-slider peer-checked:bg-indigo-600"></div>
                </div>
              </label>

              <div v-if="settings.openwrt_url"
                class="flex items-center gap-2 px-3 py-1.5 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                <div class="w-2 h-2 rounded-full" :class="{
                  'bg-emerald-500 animate-pulse': openWrtStatus === 'online',
                  'bg-red-500': openWrtStatus === 'error',
                  'bg-slate-400': !openWrtStatus
                }"></div>
                <span class="text-xs font-medium" :class="{
                  'text-emerald-600': openWrtStatus === 'online',
                  'text-red-500': openWrtStatus === 'error',
                  'text-slate-500': !openWrtStatus
                }">
                  {{ openWrtStatus === 'online' ? 'Connected' : (openWrtStatus === 'error' ? 'Error' : 'Not Verified')
                  }}
                </span>
              </div>

              <button @click="syncOpenWRT" :disabled="syncOpenWrtLoading"
                class="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-500 dark:text-slate-400"
                v-tooltip="'Sync Now'">
                <Loader2 v-if="syncOpenWrtLoading" class="w-4 h-4 animate-spin" />
                <svg v-else viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>

              <button @click="testOpenWRT" :disabled="testOpenWrtLoading"
                class="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-500 dark:text-slate-400"
                v-tooltip="'Test Connection'">
                <Loader2 v-if="testOpenWrtLoading" class="w-4 h-4 animate-spin" />
                <svg v-else viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>
            </div>
          </div>

          <div class="space-y-4">
            <!-- URL & Usage -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Router
                  URL</label>
                <input v-model="settings.openwrt_url" type="text" placeholder="http://192.168.1.1" class="box-input" />
              </div>
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Interval
                  (Minutes)</label>
                <input v-model="settings.openwrt_interval" type="number" placeholder="15" class="box-input" />
              </div>
            </div>

            <!-- Creds -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">RPC
                  Username</label>
                <input v-model="settings.openwrt_username" type="text" placeholder="root" class="box-input" />
              </div>
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">RPC
                  Password (Optional)</label>
                <input v-model="settings.openwrt_password" type="password" placeholder="••••••••" class="box-input" />
              </div>
            </div>
          </div>
        </div>

        <!-- AdGuard Integration -->
        <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-2 bg-green-100 dark:bg-green-700 rounded-lg text-green-600 dark:text-green-400">
              <ShieldCheck class="w-5 h-5" />
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">AdGuard Home Integration</h2>
              <p class="text-xs text-slate-500">Sync blocked domains and DNS stats</p>
            </div>
            <!-- Status Badge & Toggle -->
            <div class="ml-auto flex items-center gap-3">
              <label class="premium-switch group">
                <span class="premium-switch-label">Integration Enabled</span>
                <div class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="settings.adguard_enabled" class="sr-only peer">
                  <div class="premium-switch-slider peer-checked:bg-emerald-600"></div>
                </div>
              </label>

              <div v-if="settings.adguard_url"
                class="flex items-center gap-2 px-3 py-1.5 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                <div class="w-2 h-2 rounded-full" :class="{
                  'bg-emerald-500 animate-pulse': adguardStatus === 'online',
                  'bg-red-500': adguardStatus === 'error',
                  'bg-slate-400': !adguardStatus
                }"></div>
                <span class="text-xs font-medium" :class="{
                  'text-emerald-600': adguardStatus === 'online',
                  'text-red-500': adguardStatus === 'error',
                  'text-slate-500': !adguardStatus
                }">
                  {{ adguardStatus === 'online' ? 'Connected' : (adguardStatus === 'error' ? 'Error' : 'Not Verified')
                  }}
                </span>
              </div>

              <button @click="syncAdguard" :disabled="syncAdguardLoading"
                class="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-500 dark:text-slate-400"
                v-tooltip="'Sync Now'">
                <Loader2 v-if="syncAdguardLoading" class="w-4 h-4 animate-spin" />
                <svg v-else viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>

              <button @click="testAdguard" :disabled="testAdguardLoading"
                class="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-500 dark:text-slate-400"
                v-tooltip="'Test Connection'">
                <Loader2 v-if="testAdguardLoading" class="w-4 h-4 animate-spin" />
                <svg v-else viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>
            </div>
          </div>

          <div class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">AdGuard
                  URL</label>
                <input v-model="settings.adguard_url" type="text" placeholder="http://192.168.1.50:80"
                  class="box-input" />
              </div>
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Interval
                  (Minutes)</label>
                <input v-model="settings.adguard_interval" type="number" placeholder="5" class="box-input" />
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Username</label>
                <input v-model="settings.adguard_username" type="text" placeholder="admin" class="box-input" />
              </div>
              <div>
                <label
                  class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Password</label>
                <input v-model="settings.adguard_password" type="password" placeholder="••••••••" class="box-input" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar (Right Column) -->
      <div class="space-y-6">

        <!-- UI Appearance -->
        <div class="glass-panel">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg text-emerald-600 dark:text-emerald-400">
              <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2">
                <path
                  d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
              </svg>
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">UI Appearance</h2>
              <p class="text-xs text-slate-500">Configure dashboard visibility</p>
            </div>
          </div>
          <div class="space-y-4">
            <label
              class="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover-row border border-transparent hover:border-slate-200 dark:hover:border-slate-600 w-full md:w-auto">
              <div class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
                :class="settings.hide_offline === 'true' ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-600'">
                <input type="checkbox" v-model="settings.hide_offline" true-value="true" false-value="false"
                  class="hidden" />
                <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                  :class="settings.hide_offline === 'true' ? 'translate-x-6' : 'translate-x-1'"></span>
              </div>
              <div>
                <div class="text-sm font-medium text-slate-900 dark:text-white">Hide Offline Devices</div>
                <div class="text-xs text-slate-500">Only show active network nodes</div>
              </div>
            </label>
          </div>
        </div>

        <!-- Discovery Metrics -->
        <div class="glass-panel">
          <h3 class="text-sm font-semibold text-slate-900 dark:text-white mb-4">Discovery Metrics</h3>
          <div v-if="gist" class="space-y-4">
            <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
              <span class="text-xs text-slate-500">Total Scans Run</span>
              <span class="text-sm font-semibold text-slate-900 dark:text-white">{{ gist.total_scans }}</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
              <span class="text-xs text-slate-500">Discovery Jobs</span>
              <span class="text-sm font-semibold text-emerald-600">{{ gist.scans_done }}</span>
            </div>
            <div class="flex justify-between items-center py-2">
              <span class="text-xs text-slate-500">Currently Active</span>
              <span class="flex items-center gap-2">
                <span v-if="gist.scans_running > 0" class="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
                <span class="text-sm font-semibold text-blue-600">{{ gist.scans_running }}</span>
              </span>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500 italic">No metrics available</div>
        </div>

        <!-- Port Lookup Engine -->
        <div class="glass-panel">
          <div class="flex items-center gap-3 mb-4">
            <div class="p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg text-indigo-600 dark:text-indigo-400">
              <Search class="w-5 h-5" />
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">Port Lookup</h2>
              <p class="text-xs text-slate-500">Device identification engine</p>
            </div>
          </div>

          <div class="space-y-3 mb-4">
            <div class="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-slate-700/50">
              <span class="text-xs text-slate-500">Active Rules</span>
              <span class="text-sm font-semibold text-slate-900 dark:text-white">{{ rules.length }}</span>
            </div>
            <div class="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-slate-700/50">
              <span class="text-xs text-slate-500">Engine Type</span>
              <span
                class="text-xs px-2 py-0.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-full font-medium uppercase tracking-wider">Dynamic</span>
            </div>
          </div>

          <button @click="openRulesModal"
            class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-all shadow-sm">
            <Settings2 class="w-4 h-4" />
            <span>Manage Lookup Rules</span>
          </button>
        </div>

        <!-- Brand & Device Assets -->
        <div class="glass-panel">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-pink-50 dark:bg-pink-900/20 rounded-lg text-pink-600 dark:text-pink-400">
                <Tag class="w-4 h-4" />
              </div>
              <div>
                <h2 class="text-sm font-bold text-slate-900 dark:text-white">Assets</h2>
                <p class="text-[10px] text-slate-500">Custom brand & device icons</p>
              </div>
            </div>
            <button @click="openUploadModal('brand')" 
              class="group relative flex items-center gap-2.5 px-5 py-2.5 bg-gradient-to-br from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white rounded-2xl transition-all shadow-lg shadow-indigo-200 dark:shadow-indigo-900/40 hover:shadow-indigo-400/30 active:scale-95 overflow-hidden"
              v-tooltip="'Add New Branding or Device Icon'"
            >
              <div class="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <Plus class="w-4 h-4 group-hover:rotate-90 transition-transform duration-500 relative z-10" />
              <span class="text-xs font-black uppercase tracking-[0.1em] relative z-10">Add Asset</span>
            </button>
          </div>

          <div class="space-y-4">
            <div v-if="assetsLoading" class="flex justify-center py-4">
              <Loader2 class="w-5 h-5 animate-spin text-slate-400" />
            </div>
            <div v-else-if="assets.length > 0" class="grid grid-cols-5 gap-3 max-h-48 overflow-y-auto custom-scrollbar p-1">
              <div v-for="asset in assets" :key="asset.id" 
                class="group relative aspect-square bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-700 p-2.5 flex items-center justify-center shadow-sm hover:shadow-md hover:border-indigo-500/50 transition-all duration-300"
              >
                <img :src="asset.path" class="max-w-full max-h-full object-contain" :alt="asset.name" v-tooltip="asset.name" />
                
                <!-- Hover Overlay -->
                <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300 rounded-2xl flex items-center justify-center">
                  <button @click="deleteAsset(asset.id)" 
                    class="p-2 bg-white/10 hover:bg-red-500 text-white rounded-xl transition-all hover:scale-110 active:scale-90"
                    v-tooltip="'Delete Asset'"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>

                <!-- Type Badge -->
                <div class="absolute -top-1.5 -right-1.5 px-2 py-0.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-[8px] font-black uppercase tracking-widest shadow-sm group-hover:bg-indigo-500 group-hover:text-white group-hover:border-indigo-400 transition-colors">
                  {{ asset.type === 'brand' ? 'Brand' : 'Device' }}
                </div>
              </div>
            </div>
            <div v-else class="text-center py-6 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
              <p class="text-[10px] text-slate-400 italic">Empty Asset Library</p>
            </div>
          </div>
        </div>

        <!-- Database Management -->
        <div class="glass-panel">
          <div class="flex items-center gap-3 mb-4">
            <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
              <Database class="w-5 h-5" />
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-900 dark:text-white">Database Management</h2>
              <p class="text-xs text-slate-500">Backup and restore system data</p>
            </div>
          </div>

          <div class="space-y-3">
            <button @click="downloadBackup" class="btn-outline">
              <Download class="w-4 h-4" />
              <span>Download Backup</span>
            </button>
            <button @click="triggerRestore" class="btn-outline">
              <Upload class="w-4 h-4" />
              <span>Restore Database</span>
            </button>
            <input type="file" ref="restoreFileInput" @change="handleRestoreUpload" accept=".duckdb" class="hidden" />
          </div>
        </div>

        <!-- System Maintenance -->

        <div class="glass-panel border-red-200 dark:border-red-900/20">
          <h3 class="text-sm font-semibold text-red-600 dark:text-red-400 mb-2">System Maintenance</h3>
          <p class="text-xs text-slate-500 mb-4">Cleanup tools and data management</p>
          <div class="flex items-center gap-2">
            <button @click="clearAllData" class="btn-danger" v-tooltip="'Factory Reset (Delete All Data)'">
              <Trash2 class="w-5 h-5" />
            </button>
            <button @click="resetConfig" :disabled="loading" class="btn-action !p-2"
              v-tooltip="'Restore Default Configuration'">
              <RotateCcw class="w-5 h-5" :class="{ 'animate-spin': loading }" />
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>


  <!-- Confirmation Modal -->
  <div v-if="confirmModal.isOpen" class="fixed inset-0 z-50 overflow-y-auto" @click.self="closeConfirmation">
    <div class="flex min-h-screen items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="closeConfirmation"></div>

      <!-- Modal Card -->
      <div class="modal-container-sm">
        <div class="flex flex-col items-center text-center">
          <div class="h-12 w-12 rounded-full flex items-center justify-center mb-4"
            :class="confirmModal.type === 'delete' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-blue-100 dark:bg-blue-900/30'">
            <component :is="confirmModal.type === 'delete' ? Trash2 : AlertTriangle" class="h-6 w-6"
              :class="confirmModal.type === 'delete' ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'" />
          </div>

          <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ confirmModal.title }}</h3>

          <p class="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
            {{ confirmModal.message }}
          </p>

          <div class="flex gap-3 w-full">
            <button @click="closeConfirmation"
              class="flex-1 px-4 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors border border-slate-200 dark:border-slate-600">
              Cancel
            </button>
            <button @click="confirmAction" :disabled="loading"
              class="flex-1 px-4 py-2.5 text-white rounded-lg text-sm font-semibold shadow-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              :class="confirmModal.confirmClass">
              <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
              {{ loading ? 'Processing...' : confirmModal.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Maintenance Progress Modal -->
  <div v-if="isRestoring || isDownloading" class="fixed inset-0 z-[100] overflow-y-auto">
    <div class="flex min-h-screen items-center justify-center p-4 text-center">
      <div class="fixed inset-0 bg-slate-900/80 backdrop-blur-md transition-opacity"></div>

      <div class="modal-container-sm !max-w-md !p-8">
        <div class="flex flex-col items-center">
          <div class="relative mb-6">
            <div class="absolute inset-0 bg-blue-500/20 rounded-full blur-xl animate-pulse"></div>
            <div class="relative h-16 w-16 rounded-full bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center"
              :class="{ 'bg-emerald-50 dark:bg-emerald-900/30': maintenanceSuccess }">
              <Check v-if="maintenanceSuccess" class="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
              <Loader2 v-else class="h-8 w-8 text-blue-600 dark:text-blue-400 animate-spin" />
            </div>
          </div>

          <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">
            {{ maintenanceSuccess ? 'Operation Successful' : (isRestoring ? 'System Restore' : 'Preparing Backup') }}
          </h3>

          <p class="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
            {{ maintenanceStatus }}
          </p>

          <div v-if="!maintenanceSuccess"
            class="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden relative">
            <div class="absolute top-0 bottom-0 left-0 bg-blue-500 animate-progress-indeterminate w-1/2">
            </div>
          </div>

          <p class="text-[10px] text-slate-400 mt-6 uppercase tracking-widest font-bold italic">
            {{ maintenanceSuccess ? 'The page will reload automatically' : 'Please DO NOT close this window' }}
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- Classification Rules Modal -->
  <div v-if="isRulesModalOpen" class="fixed inset-0 z-50 overflow-y-auto" @click.self="isRulesModalOpen = false">
    <div class="flex min-h-screen items-center justify-center p-4">
      <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="isRulesModalOpen = false">
      </div>
      <div class="modal-container">
        <!-- Header -->
        <div
          class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/20">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg text-indigo-600 dark:text-indigo-400">
              <Fingerprint class="w-5 h-5" />
            </div>
            <div>
              <h3 class="text-lg font-bold text-slate-900 dark:text-white">Port Lookup Rules</h3>
              <p class="text-xs text-slate-500">Define how devices are identified via port probing</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="openAddRule"
              class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-all">
              <Plus class="w-4 h-4" />
              Add New Rule
            </button>
            <button @click="isRulesModalOpen = false"
              class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- List -->
        <div class="flex-1 overflow-auto p-6 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700">
          <div v-if="rulesLoading" class="flex flex-col items-center justify-center py-12 gap-4">
            <Loader2 class="w-8 h-8 animate-spin text-indigo-500" />
            <p class="text-sm text-slate-500 animate-pulse font-medium">Loading rules engine...</p>
          </div>
          <div v-else-if="rules.length === 0" class="text-center py-12">
            <div class="inline-flex p-4 bg-slate-50 dark:bg-slate-900/50 rounded-full mb-4">
              <Search class="w-8 h-8 text-slate-300 dark:text-slate-600" />
            </div>
            <h4 class="text-slate-900 dark:text-white font-semibold">No rules found</h4>
            <p class="text-sm text-slate-500 max-w-xs mx-auto mt-1">Start by adding a classification rule to better
              identify devices on your network.</p>
          </div>
          <div v-else class="space-y-4">
            <div v-for="rule in rules" :key="rule.id"
              class="group bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-700 p-4 transition-all hover:border-indigo-500/50 hover:shadow-md">
              <div class="flex items-start justify-between gap-4">
                <div class="flex items-center gap-4">
                  <div
                    class="p-3 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-100 dark:border-slate-700 text-indigo-600 dark:text-indigo-400">
                    <component :is="getIconComponent(rule.icon)" class="w-6 h-6" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2 mb-1">
                      <h4 class="font-bold text-slate-900 dark:text-white">{{ rule.name }}</h4>
                      <span v-if="rule.is_builtin"
                        class="px-2 py-0.5 bg-slate-200 dark:bg-slate-700 text-[10px] font-bold text-slate-600 dark:text-slate-400 rounded uppercase tracking-tighter">System</span>
                      <span
                        class="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-[10px] font-bold text-indigo-600 dark:text-indigo-400 rounded uppercase tracking-tighter">Prio:
                        {{ rule.priority }}</span>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <span v-if="rule.pattern_hostname"
                        class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded text-[10px] font-medium border border-blue-100/50 dark:border-blue-900/30">Host:
                        {{ rule.pattern_hostname }}</span>
                      <span v-if="rule.pattern_vendor"
                        class="px-2 py-0.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded text-[10px] font-medium border border-purple-100/50 dark:border-purple-900/30">Vendor:
                        {{ rule.pattern_vendor }}</span>
                      <span v-if="rule.ports && rule.ports.length"
                        class="px-2 py-0.5 bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded text-[10px] font-medium border border-amber-100/50 dark:border-amber-900/30">Ports:
                        {{ rule.ports.join(', ') }}</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2 self-start">
                  <button @click="editRule(rule)"
                    class="p-2 text-slate-400 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-all"
                    v-tooltip="'Edit Rule'">
                    <Pencil class="w-4 h-4" />
                  </button>
                  <button v-if="!rule.is_builtin" @click="deleteRule(rule.id)"
                    class="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                    v-tooltip="'Delete Rule'">
                    <Trash class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Rule Form Modal -->
  <div v-if="isRuleFormOpen" class="fixed inset-0 z-[60] overflow-y-auto" @click.self="isRuleFormOpen = false">
    <div class="flex min-h-screen items-center justify-center p-4">
      <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity" @click="isRuleFormOpen = false">
      </div>
      <div
        class="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-700">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-slate-900 dark:text-white">{{ editingRule ? 'Edit' : 'Create' }}
            Classification Rule</h3>
          <button @click="isRuleFormOpen = false" class="p-2 text-slate-400 hover:text-slate-600 rounded-lg">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Rule Name</label>
            <input v-model="ruleForm.name" type="text" placeholder="e.g. My Custom Router"
              class="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none" />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Device Type</label>
              <select v-model="ruleForm.device_type"
                class="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white outline-none">
                <option v-for="type in deviceTypes" :key="type" :value="type">{{ type }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Priority</label>
              <input v-model.number="ruleForm.priority" type="number"
                class="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Hostname Pattern
              (Regex)</label>
            <input v-model="ruleForm.pattern_hostname" type="text" placeholder="e.g. asus-.*"
              class="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white outline-none" />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Vendor Pattern
              (Regex)</label>
            <input v-model="ruleForm.pattern_vendor" type="text" placeholder="e.g. huawei|zte"
              class="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white outline-none" />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Ports (Comma
              separated)</label>
            <input v-model="portInput" type="text" placeholder="e.g. 80, 443, 8080"
              class="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white outline-none" />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Select Icon</label>
            <div
              class="grid grid-cols-6 gap-2 p-3 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 max-h-40 overflow-auto">
              <button v-for="icon in availableIcons" :key="icon" @click="ruleForm.icon = icon"
                class="p-2 rounded-lg transition-all flex items-center justify-center border border-transparent"
                :class="ruleForm.icon === icon ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800' : 'hover:bg-white dark:hover:bg-slate-800 text-slate-400 dark:text-slate-600'">
                <component :is="getIconComponent(icon)" class="w-5 h-5" />
              </button>
            </div>
          </div>

          <div class="flex gap-3 pt-4">
            <button @click="isRuleFormOpen = false"
              class="flex-1 px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors">Cancel</button>
            <button @click="saveRule"
              class="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-lg transition-all">Save
              Rule</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Asset Upload Modal -->
  <AssetUploadModal 
    :is-open="isUploadModalOpen" 
    :type="uploadType" 
    @close="isUploadModalOpen = false" 
    @uploaded="fetchAssets" 
  />
</template>

<script setup>
import { ref, reactive, onMounted, watch, onUnmounted } from 'vue'
import api from '@/utils/api'
import * as LucideIcons from 'lucide-vue-next'
import { Save, RotateCcw, Trash2, AlertTriangle, Loader2, Plus, Fingerprint, Pencil, Trash, X, Check, Search, ShieldCheck, Tag, Settings2, Layout, ChevronDown, Download, Upload, Database } from 'lucide-vue-next'

import { useNotifications } from '@/composables/useNotifications'
import { formatDate } from '@/utils/date'
import AssetUploadModal from '@/components/AssetUploadModal.vue'

const settings = reactive({
  scan_subnets: '[]',
  scan_interval: '300',
  last_discovery_run_at: '',
  hide_offline: 'false',
  mqtt_broker: 'localhost',
  mqtt_port: '1883',
  mqtt_base_topic: 'network_scanner',
  mqtt_username: '',
  mqtt_password: '',
  mqtt_enabled: true,
  openwrt_url: '',
  openwrt_username: '',
  openwrt_password: '',
  openwrt_interval: 15,
  openwrt_enabled: true,
  adguard_url: '',
  adguard_username: '',
  adguard_password: '',
  adguard_interval: 5,
  adguard_enabled: true
})

const openWrtStatus = ref(null)
// ... (rest)

// ... inside fetchSettings ...
const fetchSettings = async () => {
  try {
    const res = await api.get('/config/')
    if (res.data) {
      const mapping = {}
      res.data.forEach(item => {
        mapping[item.key] = item.value
      })

      settings.scan_subnets = mapping.scan_subnets || '[]'
      settings.scan_interval = String(mapping.scan_interval || 300)
      settings.hide_offline = String(mapping.hide_offline || 'false')
      settings.mqtt_broker = mapping.mqtt_broker || ''
      settings.mqtt_port = String(mapping.mqtt_port || 1883)
      settings.mqtt_base_topic = mapping.mqtt_base_topic || 'network_scanner'
      settings.mqtt_username = mapping.mqtt_username || ''
      settings.mqtt_password = mapping.mqtt_password || ''
      settings.mqtt_enabled = mapping.mqtt_enabled !== 'false'
      settings.last_discovery_run_at = mapping.last_discovery_run_at || ''

      try {
        subnetList.value = JSON.parse(settings.scan_subnets)
      } catch {
        subnetList.value = []
      }
    }

    // Fetch OpenWRT specific config
    try {
      const owRes = await api.get('/integrations/openwrt/config')
      if (owRes.data) {
        settings.openwrt_url = owRes.data.url
        settings.openwrt_username = owRes.data.username
        settings.openwrt_password = owRes.data.password
        settings.openwrt_interval = owRes.data.interval
        settings.openwrt_enabled = owRes.data.enabled !== false
        openWrtStatus.value = owRes.data.verified ? 'online' : null
      }
    } catch { }

    // Fetch AdGuard config
    try {
      const agRes = await api.get('/integrations/adguard/config')
      if (agRes.data) {
        settings.adguard_url = agRes.data.url
        settings.adguard_username = agRes.data.username
        settings.adguard_password = agRes.data.password
        settings.adguard_interval = agRes.data.interval
        settings.adguard_enabled = agRes.data.enabled !== false
        adguardStatus.value = agRes.data.verified ? 'online' : null
      }
    } catch (e) {
      console.error("AdGuard config error", e)
    }

  } catch (e) {
    console.error("Failed to fetch settings:", e)
  }
}

const testOpenWrtLoading = ref(false)
const syncOpenWrtLoading = ref(false)

const subnetList = ref([])
const newSubnet = ref('')
const gist = ref(null)
const saveStatus = ref('idle')
const loading = ref(false)
const testLoading = ref(false)
const mqttStatus = ref(null)
const subnetError = ref('')
let mqttPollTimer = null
const restoreFileInput = ref(null)
const isRestoring = ref(false)
const isDownloading = ref(false)
const maintenanceStatus = ref('')
const maintenanceSuccess = ref(false)


// Classification Rules State
const rules = ref([])
const rulesLoading = ref(false)
const isRulesModalOpen = ref(false)
const editingRule = ref(null)
const isRuleFormOpen = ref(false)

const emptyRule = {
  name: '',
  pattern_hostname: '',
  pattern_vendor: '',
  ports: [],
  device_type: 'Generic',
  icon: 'help-circle',
  priority: 100
}
const ruleForm = reactive({ ...emptyRule })
const portInput = ref('')

const deviceTypes = [
  'Smartphone', 'Tablet', 'Laptop', 'Desktop', 'Server',
  'Router/Gateway', 'Network Bridge', 'Switch', 'Access Point',
  'TV/Entertainment', 'IoT Device', 'Smart Bulb', 'Smart Plug/Switch',
  'Microcontroller', 'Security Camera', 'Sensor', 'Audio/Speaker',
  'Streaming Device', 'Printer', 'NAS/Storage', 'Game Console',
  'Media Server', 'Home Automation', 'Generic'
]

const availableIcons = [
  'smartphone', 'tablet', 'laptop', 'monitor', 'server', 'router', 'network',
  'layers', 'rss', 'tv', 'cpu', 'lightbulb', 'plug', 'microchip', 'camera',
  'waves', 'speaker', 'play', 'printer', 'hard-drive', 'gamepad-2',
  'play-circle', 'home', 'settings', 'shield-check', 'help-circle'
]

const getIconComponent = (name) => {
  if (!name) return LucideIcons.HelpCircle
  // Convert kebab to PascalCase (e.g., 'play-circle' -> 'PlayCircle')
  const camel = name.split('-').map(p => p.charAt(0).toUpperCase() + p.slice(1)).join('')
  return LucideIcons[camel] || LucideIcons[name] || LucideIcons.HelpCircle
}

const { notifySuccess, notifyError } = useNotifications()

// Clear error when user types
watch(newSubnet, () => {
  if (subnetError.value) subnetError.value = ''
})

// Confirmation Modal State
const confirmModal = reactive({
  isOpen: false,
  type: '', // 'delete' or 'reset'
  title: '',
  message: '',
  confirmText: '',
  confirmClass: ''
})

const addSubnet = () => {
  const s = newSubnet.value.trim()
  if (!s) {
    subnetError.value = 'Subnet range cannot be empty'
    return
  }
  if (subnetList.value.includes(s)) {
    subnetError.value = 'Subnet already exists'
    return
  }

  subnetList.value.push(s)
  settings.scan_subnets = JSON.stringify(subnetList.value)
  newSubnet.value = ''
  subnetError.value = ''
}

const removeSubnet = (s) => {
  subnetList.value = subnetList.value.filter(item => item !== s)
  settings.scan_subnets = JSON.stringify(subnetList.value)
}




const fetchRules = async () => {
  rulesLoading.value = true
  try {
    const res = await api.get('/classification/')
    rules.value = res.data
  } catch (e) {
    notifyError('Failed to fetch classification rules')
  } finally {
    rulesLoading.value = false
  }
}

const openRulesModal = () => {
  fetchRules()
  isRulesModalOpen.value = true
}

const openAddRule = () => {
  Object.assign(ruleForm, emptyRule)
  portInput.value = ''
  editingRule.value = null
  isRuleFormOpen.value = true
}

const editRule = (rule) => {
  Object.assign(ruleForm, rule)
  portInput.value = rule.ports.join(', ')
  editingRule.value = rule.id
  isRuleFormOpen.value = true
}

const saveRule = async () => {
  try {
    // Parse ports
    const ports = portInput.value.split(',')
      .map(p => parseInt(p.trim()))
      .filter(p => !isNaN(p))
    ruleForm.ports = ports

    if (editingRule.value) {
      await api.put(`/classification/${editingRule.value}`, ruleForm)
      notifySuccess('Rule updated successfully')
    } else {
      await api.post('/classification/', ruleForm)
      notifySuccess('Rule created successfully')
    }
    isRuleFormOpen.value = false
    fetchRules()
  } catch (e) {
    notifyError(e.response?.data?.detail || 'Failed to save rule')
  }
}

const deleteRule = async (id) => {
  if (!confirm('Are you sure you want to delete this rule?')) return
  try {
    await api.delete(`/classification/${id}`)
    notifySuccess('Rule deleted successfully')
    fetchRules()
  } catch (e) {
    notifyError(e.response?.data?.detail || 'Failed to delete rule')
  }
}

const fetchGist = async () => {
  try {
    const res = await api.get('/scans/gist')
    gist.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const testOpenWRT = async () => {
  testOpenWrtLoading.value = true
  try {
    await api.post('/integrations/openwrt/verify', {
      url: settings.openwrt_url,
      username: settings.openwrt_username,
      password: settings.openwrt_password
    })
    notifySuccess("OpenWRT Connection Successful!")
    openWrtStatus.value = 'online'
  } catch (e) {
    notifyError("Connection Failed: " + (e.response?.data?.detail || e.message))
    openWrtStatus.value = 'error'
  } finally {
    testOpenWrtLoading.value = false
  }
}

const syncOpenWRT = async () => {
  syncOpenWrtLoading.value = true
  try {
    await api.post('/integrations/openwrt/sync')
    notifySuccess("Sync started! Check device list shortly.")
  } catch (e) {
    notifyError("Sync Failed: " + (e.response?.data?.detail || e.message))
  } finally {
    syncOpenWrtLoading.value = false
  }
}

// AdGuard logic
const adguardStatus = ref(null)
const testAdguardLoading = ref(false)
const syncAdguardLoading = ref(false)

const testAdguard = async () => {
  testAdguardLoading.value = true
  try {
    await api.post('/integrations/adguard/verify', {
      url: settings.adguard_url,
      username: settings.adguard_username,
      password: settings.adguard_password
    })
    notifySuccess("AdGuard Connection Successful!")
    adguardStatus.value = 'online'
  } catch (e) {
    notifyError("Connection Failed: " + (e.response?.data?.detail || e.message))
    adguardStatus.value = 'error'
  } finally {
    testAdguardLoading.value = false
  }
}

const syncAdguard = async () => {
  syncAdguardLoading.value = true
  try {
    await api.post('/integrations/adguard/sync')
    notifySuccess("AdGuard Sync started!")
  } catch (e) {
    notifyError("Sync Failed: " + (e.response?.data?.detail || e.message))
  } finally {
    syncAdguardLoading.value = false
  }
}

const saveSettings = async () => {
  saveStatus.value = 'saving'
  try {
    await api.post('/config/', settings)

    // Save OpenWRT config separately only if URL is provided
    if (settings.openwrt_url) {
      const owRes = await api.post('/integrations/openwrt/config', {
        url: settings.openwrt_url,
        username: settings.openwrt_username,
        password: settings.openwrt_password,
        interval: parseInt(settings.openwrt_interval) || 15,
        enabled: settings.openwrt_enabled
      })
      // Update status from backend auto-verification
      openWrtStatus.value = owRes.data.verified ? 'online' : null
    }

    // Save AdGuard config
    if (settings.adguard_url) {
      const agRes = await api.post('/integrations/adguard/config', {
        url: settings.adguard_url,
        username: settings.adguard_username,
        password: settings.adguard_password,
        interval: parseInt(settings.adguard_interval) || 5,
        enabled: settings.adguard_enabled
      })
      adguardStatus.value = agRes.data.verified ? 'online' : null
    }

    saveStatus.value = 'saved'
    notifySuccess('Settings saved successfully')
    // Refresh MQTT status after save
    setTimeout(fetchMqttStatus, 1000)
    setTimeout(() => { saveStatus.value = 'idle' }, 2000)
  } catch (e) {
    notifyError('Failed to save settings')
    saveStatus.value = 'idle'
  }
}

const fetchMqttStatus = async () => {
  try {
    const res = await api.get('/mqtt/status')
    mqttStatus.value = res.data.status
  } catch (e) {
    console.error("Failed to fetch MQTT status")
  }
}

const testMqtt = async () => {
  testLoading.value = true
  try {
    const res = await api.post('/mqtt/test', {
      broker: settings.mqtt_broker,
      port: parseInt(settings.mqtt_port),
      username: settings.mqtt_username,
      password: settings.mqtt_password
    })
    if (res.data.success) {
      notifySuccess("MQTT Connection Successful!")
      mqttStatus.value = 'online'
    } else {
      notifyError("Connection Failed: " + (res.data.message || "Unknown error"))
      mqttStatus.value = 'offline'
    }
  } catch (e) {
    console.error(e)
    notifyError("Request failed: " + (e.response?.data?.detail || e.message))
    mqttStatus.value = 'offline'
  } finally {
    testLoading.value = false
  }
}

const openConfirmation = (type) => {
  confirmModal.type = type
  confirmModal.isOpen = true

  if (type === 'delete') {
    confirmModal.title = 'Factory Reset?'
    confirmModal.message = 'This will permanently delete all discovered devices, scan history, and metrics. This action cannot be undone.'
    confirmModal.confirmText = 'Yes, Delete Everything'
    confirmModal.confirmClass = 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
  } else if (type === 'reset') {
    confirmModal.title = 'Restore Defaults?'
    confirmModal.message = 'This will revert all settings (scan intervals, subnets, UI preferences) to their default values. Your data will be preserved.'
    confirmModal.confirmText = 'Restore Defaults'
    confirmModal.confirmClass = 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
  } else if (type === 'restore') {
    confirmModal.title = 'Restore Database?'
    confirmModal.message = 'This will replace your current database with the selected backup. The application will restart and current unsaved progress will be lost.'
    confirmModal.confirmText = 'Yes, Restore and Restart'
    confirmModal.confirmClass = 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500'
  } else if (type === 'delete_asset') {
    confirmModal.title = 'Delete Asset?'
    confirmModal.message = 'Are you sure you want to permanently delete this custom asset? This icon will no longer be visible on associated devices.'
    confirmModal.confirmText = 'Delete Asset'
    confirmModal.confirmClass = 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
  }
}


const closeConfirmation = () => {
  confirmModal.isOpen = false
}

const confirmAction = async () => {
  closeConfirmation()
  loading.value = true

  try {
    if (confirmModal.type === 'delete') {
      await api.delete('/devices/')
      await api.delete('/scans/')
      window.location.reload()
    } else if (confirmModal.type === 'reset') {
      // Reset local state to defaults
      settings.scan_interval = '300'
      settings.scan_subnets = '[]'
      settings.hide_offline = 'false'
      settings.mqtt_broker = 'localhost'
      settings.mqtt_port = '1883'
      settings.mqtt_base_topic = 'network_scanner'
      settings.mqtt_username = ''
      settings.mqtt_password = ''
      subnetList.value = []

      // Save these defaults
      await api.post('/config/', settings)

      // Re-fetch to confirm
      await fetchSettings()
    } else if (confirmModal.type === 'restore') {
      const file = restoreFileInput.value.files[0]
      if (!file) return

      isRestoring.value = true
      maintenanceStatus.value = 'Uploading database backup...'

      try {
        const formData = new FormData()
        formData.append('file', file)

        await api.post('/system/restore', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        maintenanceSuccess.value = true
        maintenanceStatus.value = 'Database restored! Re-initializing system...'
        notifySuccess('Database restored successfully')

        setTimeout(() => {
          window.location.reload()
        }, 3000)
      } catch (err) {
        isRestoring.value = false
        maintenanceSuccess.value = false
        const detail = err.response?.data?.detail || err.message
        notifyError(`Restore failed: ${detail}`)
        // Reset file input so user can try again
        if (restoreFileInput.value) restoreFileInput.value.value = ''
      }
    } else if (confirmModal.type === 'delete_asset') {
      if (!assetToDelete.value) return
      await api.delete(`/assets/${assetToDelete.value}`)
      notifySuccess('Asset deleted')
      fetchAssets()
      assetToDelete.value = null
    }
  } catch (e) {
    console.error(e)
    notifyError(`Action failed: ${e.message}`)
  } finally {
    loading.value = false
    if (confirmModal.type !== 'restore') {
      // Restore handles its own state for the modal
    }
  }
}

// Wrappers for buttons
const clearAllData = () => openConfirmation('delete')
const resetConfig = () => openConfirmation('reset')

const downloadBackup = async () => {
  isDownloading.value = true
  maintenanceStatus.value = 'Generating database checkpoint...'

  try {
    const response = await api.get('/system/backup', {
      responseType: 'blob'
    })

    maintenanceStatus.value = 'Download starting...'
    maintenanceSuccess.value = true

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'network_scanner.duckdb')
    document.body.appendChild(link)
    link.click()
    link.remove()
    notifySuccess('Backup download started')

    setTimeout(() => {
      isDownloading.value = false
      maintenanceSuccess.value = false
    }, 2000)
  } catch (e) {
    isDownloading.value = false
    maintenanceSuccess.value = false
    const detail = e.response?.data?.detail || e.message
    notifyError(`Failed to download backup: ${detail}`)
  }
}

const triggerRestore = () => {
  restoreFileInput.value.click()
}

const handleRestoreUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  if (!file.name.endsWith('.duckdb')) {
    notifyError('Please select a .duckdb file')
    return
  }
  openConfirmation('restore')
}


const formatLastRun = (dateStr) => {
  return formatDate(dateStr)
}

const assets = ref([])
const assetsLoading = ref(false)
const isUploadModalOpen = ref(false)
const uploadType = ref('brand')

const fetchAssets = async () => {
  assetsLoading.value = true
  try {
    const res = await api.get('/assets')
    assets.value = res.data
  } catch (e) {
    console.error('Failed to fetch assets:', e)
  } finally {
    assetsLoading.value = false
  }
}

const openUploadModal = (type) => {
  uploadType.value = type
  isUploadModalOpen.value = true
}

const assetToDelete = ref(null)

const deleteAsset = (id) => {
  assetToDelete.value = id
  openConfirmation('delete_asset')
}

onMounted(async () => {
  await Promise.all([
    fetchSettings(),
    fetchGist(),
    fetchMqttStatus(),
    fetchRules(),
    fetchAssets()
  ])

  // Start polling MQTT status every 10 seconds
  mqttPollTimer = setInterval(fetchMqttStatus, 10000)
})

onUnmounted(() => {
  if (mqttPollTimer) clearInterval(mqttPollTimer)
})
</script>

<style scoped>
@keyframes progress-indeterminate {
  0% {
    transform: translateX(-150%);
  }

  50% {
    transform: translateX(0);
  }

  100% {
    transform: translateX(150%);
  }
}

.animate-progress-indeterminate {
  animation: progress-indeterminate 2.5s infinite ease-in-out;
}

.premium-switch {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
}

.premium-switch:hover {
  background-color: rgba(248, 250, 252, 0.5);
}

.dark .premium-switch:hover {
  background-color: rgba(15, 23, 42, 0.3);
}

.premium-switch-label {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8; /* slate-400 */
  transition: color 0.2s;
}

.premium-switch:hover .premium-switch-label {
  color: #475569; /* slate-600 */
}

.dark .premium-switch:hover .premium-switch-label {
  color: #cbd5e1; /* slate-300 */
}

.premium-switch-slider {
  width: 2.25rem; /* 36px */
  height: 1.25rem; /* 20px */
  background-color: #e2e8f0; /* slate-200 */
  border-radius: 9999px;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dark .premium-switch-slider {
  background-color: #334155; /* slate-700 */
}

.premium-switch-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 1rem; /* 16px */
  height: 1rem; /* 16px */
  background-color: white;
  border-radius: 9999px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

input:checked + .premium-switch-slider::after {
  transform: translateX(1rem);
}
</style>
