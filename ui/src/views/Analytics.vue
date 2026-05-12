<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div class="flex flex-col sm:flex-row sm:items-center gap-4">
                <div>
                    <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Network Analytics</h1>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        Traffic insights and device distribution
                    </p>
                </div>
            </div>

            <div class="flex items-center gap-4">
                <!-- Time Range Picker (Standardized) -->
                <div class="flex p-1 bg-slate-100 dark:bg-slate-700/50 rounded-xl h-11"
                    v-if="(localConfigured && currentView === 'traffic') || (dnsConfigured && currentView === 'dns')">
                    <button
                        v-for="r in ['24h', 'yesterday', '7d', '30d', '3m', 'mtd', 'last_month', 'ytd', '1y', 'all']"
                        :key="r" @click="timeRange = r"
                        class="px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all whitespace-nowrap uppercase tracking-wider"
                        :class="timeRange === r ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'">
                        {{ {
                            '24h': '24H', 'yesterday': 'Yest', '7d': '7D', '30d': '30D', '3m': '3M', 'mtd': 'MTD',
                            'last_month': 'Last M', 'ytd': 'YTD', '1y': '1Y', 'all': 'All'
                        }[r] }}
                    </button>
                </div>

                <!-- View Switcher (Standardized) -->
                <div class="flex p-1 bg-slate-100 dark:bg-slate-700/50 rounded-xl h-11">
                    <button @click="currentView = 'traffic'"
                        class="px-5 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2"
                        :class="currentView === 'traffic' ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'">
                        <Activity class="w-4 h-4" />
                        Traffic
                    </button>
                    <button @click="currentView = 'dns'"
                        class="px-5 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2"
                        :class="currentView === 'dns' ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'">
                        <ShieldCheck class="w-4 h-4" />
                        DNS Security
                    </button>
                </div>
            </div>
        </div>

        <!-- View Container -->
        <div v-if="currentView === 'dns'">
            <!-- DNS Analytics Component (To be added) -->
            <div v-if="dnsConfigured" class="space-y-6">
                <!-- DNS KPIs -->

                <!-- DNS KPIs -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <Activity class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Total Queries</p>
                        <p class="text-2xl font-bold text-slate-900 dark:text-white">{{
                            dnsStats.total_queries.toLocaleString() }}</p>
                    </div>
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <ShieldCheck class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Blocked</p>
                        <p class="text-2xl font-bold text-red-600 dark:text-red-400">{{
                            dnsStats.blocked_queries.toLocaleString() }}</p>
                    </div>
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <ShieldCheck class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Block Rate</p>
                        <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ dnsStats.block_percentage }}%
                        </p>
                    </div>
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <Activity class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Avg Response</p>
                        <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ dnsStats.avg_response_time }} ms
                        </p>
                    </div>
                </div>

                <!-- DNS Traffic Chart -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div
                        class="lg:col-span-3 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-6">DNS Traffic</h3>
                        <div class="h-[350px]">
                            <apexchart type="area" height="100%" :options="dnsChartOptions"
                                :series="dnsTrafficSeries" />
                        </div>
                    </div>
                </div>

                <!-- Top Lists -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Top Blocked Domains -->
                    <div class="premium-card !p-0 shadow-sm flex flex-col">
                        <div
                            class="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
                            <h3 class="text-base font-semibold text-slate-900 dark:text-white">Top Blocked Domains</h3>
                            <div class="flex gap-2">
                                <button @click="changeDnsPage('blocked', -1)" :disabled="dnsPage.blocked === 1"
                                    class="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30">
                                    <ChevronLeft class="w-4 h-4" />
                                </button>
                                <span class="text-xs font-mono self-center">Page {{ dnsPage.blocked }}</span>
                                <button @click="changeDnsPage('blocked', 1)"
                                    :disabled="topBlockedDomains.length < dnsLimit"
                                    class="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30">
                                    <ChevronRight class="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                        <div class="flex-1 p-4 space-y-3">
                            <div v-for="(domain, idx) in topBlockedDomains" :key="idx" class="flex items-center gap-3">
                                <div class="w-6 text-center text-xs font-bold text-slate-400">#{{ ((dnsPage.blocked - 1)
                                    * dnsLimit) + idx + 1 }}</div>
                                <div class="flex-1 min-w-0">
                                    <div class="flex justify-between">
                                        <span class="text-sm font-medium text-red-600 dark:text-red-400 truncate"
                                            :title="domain.domain">{{ domain.domain }}</span>
                                        <span class="text-xs font-mono text-slate-500">{{ domain.count }}</span>
                                    </div>
                                    <div class="flex justify-between items-end">
                                        <div class="text-[10px] text-slate-400">
                                            {{ domain.category || 'Uncategorized' }}
                                        </div>
                                        <div
                                            class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 text-[10px] font-bold text-blue-700 dark:text-blue-300 shadow-sm">
                                            <component :is="getIcon(domain.top_client_icon || domain.top_client_type)"
                                                class="w-3 h-3" />
                                            <span>{{ domain.top_client_name }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-if="topBlockedDomains.length === 0" class="text-center text-sm text-slate-500 py-4">
                                No blocked domains</div>
                        </div>
                    </div>

                    <!-- Top Allowed Domains -->
                    <div class="premium-card !p-0 shadow-sm flex flex-col">
                        <div
                            class="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
                            <h3 class="text-base font-semibold text-slate-900 dark:text-white">Top Queried Domains</h3>
                            <div class="flex gap-2">
                                <button @click="changeDnsPage('allowed', -1)" :disabled="dnsPage.allowed === 1"
                                    class="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30">
                                    <ChevronLeft class="w-4 h-4" />
                                </button>
                                <span class="text-xs font-mono self-center">Page {{ dnsPage.allowed }}</span>
                                <button @click="changeDnsPage('allowed', 1)"
                                    :disabled="topAllowedDomains.length < dnsLimit"
                                    class="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30">
                                    <ChevronRight class="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                        <div class="flex-1 p-4 space-y-3">
                            <div v-for="(domain, idx) in topAllowedDomains" :key="idx" class="flex items-center gap-3">
                                <div class="w-6 text-center text-xs font-bold text-slate-400">#{{ ((dnsPage.allowed - 1)
                                    * dnsLimit) + idx + 1 }}</div>
                                <div class="flex-1 min-w-0">
                                    <div class="flex justify-between">
                                        <span class="text-sm font-medium text-slate-700 dark:text-slate-200 truncate"
                                            :title="domain.domain">{{ domain.domain }}</span>
                                        <span class="text-xs font-mono text-slate-500">{{ domain.count }}</span>
                                    </div>
                                    <div class="flex justify-between items-end">
                                        <div class="text-[10px] text-slate-400">
                                            {{ domain.category || 'Uncategorized' }}
                                        </div>
                                        <div
                                            class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 text-[10px] font-bold text-blue-700 dark:text-blue-300 shadow-sm">
                                            <component :is="getIcon(domain.top_client_icon || domain.top_client_type)"
                                                class="w-3 h-3" />
                                            <span>{{ domain.top_client_name }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-if="topAllowedDomains.length === 0" class="text-center text-sm text-slate-500 py-4">
                                No queries recorded</div>
                        </div>
                    </div>
                </div>

                <!-- Bottom DNS Row: Query Types & Risky Devices -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Query Type Distribution -->
                    <div
                        class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-4">Query Types</h3>
                        <div class="h-[300px] flex items-center justify-center">
                            <div v-if="queryTypeSeries.length === 0" class="text-sm text-slate-400">No data</div>
                            <apexchart v-else type="donut" width="100%" height="300" :options="queryTypeOptions"
                                :series="queryTypeSeries" />
                        </div>
                    </div>

                    <!-- Risky Devices (High Block Rate) -->
                    <div class="lg:col-span-2 premium-card !p-0 shadow-sm flex flex-col">
                        <div
                            class="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
                            <div>
                                <h3 class="text-base font-semibold text-slate-900 dark:text-white">Risky Clients</h3>
                                <p class="text-[10px] text-slate-400 uppercase font-black">Highest block rate (min 10
                                    queries)</p>
                            </div>
                            <ShieldAlert class="w-5 h-5 text-red-500 opacity-50" />
                        </div>
                        <div class="flex-1 p-4">
                            <div v-if="riskyDevices.length > 0" class="space-y-4">
                                <div v-for="device in riskyDevices" :key="device.id"
                                    class="flex items-center gap-4 group">
                                    <div class="icon-box-sm">
                                        <component :is="getIcon(device.icon || 'help-circle')" class="w-5 h-5" />
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="flex justify-between mb-1">
                                            <span
                                                class="text-sm font-bold text-slate-700 dark:text-slate-200 truncate">{{
                                                    device.name }}</span>
                                            <span class="text-xs font-black text-red-600 dark:text-red-400">{{
                                                device.block_rate }}% Blocked</span>
                                        </div>
                                        <div
                                            class="w-full h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                            <div class="h-full bg-red-500 rounded-full"
                                                :style="{ width: `${device.block_rate}%` }"></div>
                                        </div>
                                        <div class="flex justify-between mt-1 text-[10px] text-slate-400">
                                            <span>{{ device.ip }}</span>
                                            <span>{{ device.blocked }} of {{ device.total }} queries blocked</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="py-12 text-center text-sm text-slate-500 italic">
                                No high-risk clients detected
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Top Clients (Chart) - Full Width -->
                <div class="grid grid-cols-1 gap-6">
                    <div
                        class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-4">Top Clients (DNS
                            Queries)
                        </h3>
                        <div class="h-[350px]">
                            <apexchart type="bar" height="100%" :options="dnsBarOptions" :series="dnsClientsSeries" />
                        </div>
                    </div>
                </div>
            </div>
            <div v-else
                class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-8 text-center max-w-2xl mx-auto mt-12">
                <div
                    class="w-16 h-16 bg-slate-50 dark:bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <ShieldCheck class="w-8 h-8 text-slate-400" />
                </div>
                <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                    {{ !configStatus.adguard.enabled ? 'AdGuard Integration Disabled' : 'AdGuard Integration Required'
                    }}
                </h2>
                <p v-if="configStatus.adguard.error"
                    class="text-red-500 dark:text-red-400 text-sm mb-4 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-100 dark:border-red-800/30">
                    <span class="font-bold">Error:</span> {{ configStatus.adguard.error }}
                </p>
                <p v-else class="text-slate-500 dark:text-slate-400 text-sm mb-6 max-w-md mx-auto">
                    {{ !configStatus.adguard.enabled ? 'Enable the AdGuard integration in settings to view DNS analytics.' : 'To view DNS analytics, connect your AdGuard Home instance.' }}
                </p>
                <router-link to="/settings" class="btn-primary">
                    <Settings class="w-4 h-4" />
                    {{ configStatus.adguard.error || !configStatus.adguard.enabled ? 'Fix in Settings' : 'Configure AdGuard' }}
                </router-link>
            </div>
        </div>

        <div v-else-if="currentView === 'traffic'">
            <!-- Existing Traffic Dashboard Content (Wrapper) -->

            <!-- Not Configured State -->
            <div v-if="!loading && !localConfigured"
                class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-8 text-center max-w-2xl mx-auto mt-12">
                <div
                    class="w-16 h-16 bg-slate-50 dark:bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Router class="w-8 h-8 text-slate-400" />
                </div>
                <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                    {{ !configStatus.openwrt.enabled ? 'OpenWRT Integration Disabled' : 'OpenWRT Integration Required'
                    }}
                </h2>
                <p v-if="configStatus.openwrt.error"
                    class="text-red-500 dark:text-red-400 text-sm mb-4 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-100 dark:border-red-800/30">
                    <span class="font-bold">Error:</span> {{ configStatus.openwrt.error }}
                </p>
                <p v-else class="text-slate-500 dark:text-slate-400 text-sm mb-6 max-w-md mx-auto">
                    {{ !configStatus.openwrt.enabled ? 'Enable the OpenWRT integration in settings to view traffic analytics.' : 'To view traffic analytics, you need to connect your OpenWRT router and install the nlbwmon package.' }}
                </p>
                <router-link to="/settings" class="btn-primary">
                    <Settings class="w-4 h-4" />
                    {{ configStatus.openwrt.error || !configStatus.openwrt.enabled ? 'Fix in Settings' : 'Configure OpenWRT' }}
                </router-link>

                <div class="mt-8 pt-8 border-t border-slate-100 dark:border-slate-700 text-left">
                    <p class="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider mb-3">Quick
                        Setup Guide</p>
                    <ol class="space-y-2 text-sm text-slate-600 dark:text-slate-400 list-decimal pl-4">
                        <li>SSH into your OpenWRT router</li>
                        <li>Run: <code
                                class="bg-slate-100 dark:bg-slate-900 px-1 py-0.5 rounded font-mono text-xs">opkg update && opkg install nlbwmon</code>
                        </li>
                        <li>Go to Settings > Integrations in this app</li>
                        <li>Enter your router IP and credentials</li>
                    </ol>
                </div>
            </div>

            <!-- Dashboard -->
            <div v-else-if="!loading" class="space-y-6">

                <!-- Key Metrics -->
                <!-- Active Devices Count Fix -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <Download class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Total Download</p>
                        <p class="text-2xl font-bold text-slate-900 dark:text-white">{{
                            formatBytes(trafficTotals.download)
                        }}</p>
                    </div>
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <Upload class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Total Upload</p>
                        <p class="text-2xl font-bold text-slate-900 dark:text-white">{{
                            formatBytes(trafficTotals.upload) }}
                        </p>
                    </div>
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <Users class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Active Devices</p>
                        <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ trafficTotals.active_devices }}
                        </p>
                    </div>
                    <div class="card-base">
                        <div class="absolute right-0 top-0 p-4 opacity-5">
                            <Activity class="w-16 h-16" />
                        </div>
                        <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Avg
                            Throughput</p>
                        <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ calculateAvgThroughput() }}</p>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Main Traffic Chart -->
                    <div
                        class="lg:col-span-3 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-6">Traffic Overview</h3>
                        <div class="h-[350px]">
                            <apexchart type="area" height="100%" :options="chartOptions" :series="chartSeries" />
                        </div>
                    </div>

                    <!-- Usage Heatmap -->
                    <div
                        class="lg:col-span-3 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-2">Usage Patterns</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">Intensity of data consumption by Day
                            and
                            Hour</p>
                        <div class="h-[350px]">
                            <apexchart type="heatmap" height="100%" :options="heatmapOptions" :series="heatmapSeries" />
                        </div>
                        <!-- Custom Gradient Legend -->
                        <div
                            class="mt-4 flex items-center justify-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                            <span>Low (Green)</span>
                            <div
                                class="w-64 h-3 rounded-full bg-gradient-to-r from-[#10b981] via-[#f59e0b] to-[#ef4444] relative shadow-sm border border-slate-200 dark:border-slate-700">
                            </div>
                            <span>High (Red)</span>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Top Consumers List (Moved here, resized) -->
                    <div class="premium-card !p-0 shadow-sm flex flex-col">
                        <div class="p-6 border-b border-slate-100 dark:border-slate-700">
                            <h3 class="text-base font-semibold text-slate-900 dark:text-white">Top Consumers</h3>
                        </div>
                        <div class="flex-1 overflow-y-auto max-h-[350px] p-4 space-y-4 custom-scrollbar">
                            <div v-for="(device, idx) in topDevices" :key="device.id"
                                class="flex items-center gap-3 group">
                                <div class="w-6 text-center text-xs font-bold text-slate-400">#{{ idx + 1 }}</div>
                                <div class="icon-box-sm">
                                    <component :is="getIcon(device.icon || 'help-circle')" class="w-5 h-5" />
                                </div>
                                <div class="flex-1 min-w-0">
                                    <div class="flex justify-between mb-1">
                                        <span class="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{{
                                            device.name }}</span>
                                        <span class="text-xs font-semibold text-slate-900 dark:text-white">{{
                                            formatBytes(device.total) }}</span>
                                    </div>
                                    <div
                                        class="w-full h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                        <div class="h-full bg-blue-500 rounded-full"
                                            :class="`w-[${Math.round(getUsagePercent(device.total))}%]`"></div>
                                    </div>
                                    <div class="flex justify-between mt-1 text-[10px] text-slate-400">
                                        <span>↓ {{ formatBytes(device.download) }}</span>
                                        <span>↑ {{ formatBytes(device.upload) }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Vendor Distribution (Moved next to Top Consumers) -->
                    <div
                        class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-4">Vendor Distribution
                            (Count)
                        </h3>
                        <div class="h-[350px] flex items-center justify-center">
                            <apexchart type="donut" height="300" :options="donutOptions" :series="vendorSeries" />
                        </div>
                    </div>
                </div>

                <!-- Bottom Row: Category Usage & Device Types -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Usage by Category (Traffic) -->
                    <div class="premium-card !p-6 shadow-sm flex flex-col">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-2">Traffic Volume by
                            Category
                        </h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Total data consumed by device type
                        </p>
                        <div class="flex-1 min-h-[300px] flex items-center justify-center">
                            <div v-if="categorySeries.length === 0" class="text-sm text-slate-400">No data available
                            </div>
                            <apexchart v-else type="donut" width="100%" height="300" :options="categoryOptions"
                                :series="categorySeries" />
                        </div>
                    </div>

                    <!-- Device Types (Count) -->
                    <div
                        class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-2">Device Count by Category
                        </h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Number of devices per type</p>
                        <div class="h-[300px]">
                            <apexchart type="bar" height="100%" :options="barOptions" :series="typeSeries" />
                        </div>
                    </div>
                </div>



            </div>

            <!-- Loading State -->
            <div v-else class="h-96 flex items-center justify-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import api from '@/utils/api'
import { DateTime } from 'luxon'
import { useNotifications } from '@/composables/useNotifications'
import { parseUTC } from '@/utils/date'
import { getIcon } from '@/utils/icons'
import {
    Router, Settings, Download, Upload, Users, Activity, ShieldCheck, ChevronLeft, ChevronRight, ShieldAlert
} from 'lucide-vue-next'
import { formatBytes } from '@/utils/format'

const loading = ref(true)
const localConfigured = ref(false)
const dnsConfigured = ref(false)
const configStatus = reactive({
    openwrt: { enabled: true, verified: true, error: null },
    adguard: { enabled: true, verified: true, error: null }
})
const currentView = ref('traffic') // 'traffic' or 'dns'
const timeRange = ref('7d')

const trafficTotals = ref({ download: 0, upload: 0, active_devices: 0 })
const topDevices = ref([])

const chartSeries = ref([])
const vendorSeries = ref([])
const categorySeries = ref([])
const typeSeries = ref([])
const heatmapSeries = ref([])

// getIcon is now imported from @/utils/icons

// ...

// Check Config
const checkConfig = async () => {
    try {
        const res = await api.get('/integrations/openwrt/config')
        configStatus.openwrt.enabled = res.data.enabled !== false
        configStatus.openwrt.verified = res.data.verified
        configStatus.openwrt.error = res.data.error
        localConfigured.value = configStatus.openwrt.verified && configStatus.openwrt.enabled
    } catch (e) {
        localConfigured.value = false
    }

    try {
        const res = await api.get('/integrations/adguard/config')
        configStatus.adguard.enabled = res.data.enabled !== false
        configStatus.adguard.verified = res.data.verified
        configStatus.adguard.error = res.data.error
        dnsConfigured.value = configStatus.adguard.verified && configStatus.adguard.enabled
    } catch (e) {
        dnsConfigured.value = false
    }
}

const usagePage = ref(1)
const usageTotalPages = ref(1)
const usageDevices = ref([])
const usageLoading = ref(false)

const fetchUsageDetails = async () => {
    usageLoading.value = true
    try {
        const res = await api.get(`/analytics/usage-details?range=${timeRange.value}&page=${usagePage.value}&limit=10`)
        usageDevices.value = res.data.items || []
        usageTotalPages.value = res.data.pages || 1
    } catch (e) {
        console.error("Failed to load usage details", e)
    } finally {
        usageLoading.value = false
    }
}

const changeUsagePage = (delta) => {
    const newPage = usagePage.value + delta
    if (newPage >= 1 && newPage <= usageTotalPages.value) {
        usagePage.value = newPage
        fetchUsageDetails()
    }
}

const fetchData = async () => {
    // Dispatch based on current view
    if (currentView.value === 'traffic') {
        if (localConfigured.value) await fetchTrafficData()
        else loading.value = false
    } else if (currentView.value === 'dns') {
        if (dnsConfigured.value) await fetchDnsData()
        else loading.value = false
    }
}

const fetchTrafficData = async () => {
    // Renaming original fetchData to fetchTrafficData
    // Logic stays same mostly, just moving it here
    loading.value = true
    try {
        // Parallel Fetch (Top Consumers Limit reduced to 5)
        const [trafficRes, topRes, distRes, catRes, heatRes] = await Promise.all([
            api.get(`/analytics/traffic?range=${timeRange.value}`),
            api.get(`/analytics/top-devices?range=${timeRange.value}&limit=5`),
            api.get(`/analytics/distribution?range=${timeRange.value}`),
            api.get(`/analytics/category-usage?range=${timeRange.value}`),
            api.get(`/analytics/heatmap?range=${timeRange.value}`)
        ])

        // Process Traffic
        trafficTotals.value = trafficRes.data.totals
        const series = trafficRes.data.series
        chartSeries.value = [
            { name: 'Download', data: series.map(d => [parseUTC(d.timestamp).toJSDate().getTime(), d.download]) },
            { name: 'Upload', data: series.map(d => [parseUTC(d.timestamp).toJSDate().getTime(), d.upload]) }
        ]

        // Process Top Devices (Top 5 for widget)
        topDevices.value = topRes.data

        // Process Distribution
        vendorSeries.value = distRes.data.vendors.map(v => v.value)
        typeSeries.value = [{ name: 'Devices', data: distRes.data.types.map(t => t.value) }]

        // Process Category Usage
        categorySeries.value = catRes.data.map(c => c.total)

        // Process Heatmap with Localization
        // Shifting UTC hours from backend to user's local time
        const offsetHours = Math.round(DateTime.now().offset / 60)
        const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        // matrix[day][hour]
        const localizedMatrix = Array.from({ length: 7 }, () => Array.from({ length: 24 }, () => null))

        heatRes.data.forEach((daySeries, dayIdx) => {
            daySeries.data.forEach((point, hourIdx) => {
                // Local Hour calculation
                let localHour = (hourIdx + offsetHours) % 24
                if (localHour < 0) localHour += 24

                // Day shift calculation
                const dayShift = Math.floor((hourIdx + offsetHours) / 24)
                let localDayIdx = (dayIdx + dayShift) % 7
                if (localDayIdx < 0) localDayIdx += 7

                localizedMatrix[localDayIdx][localHour] = {
                    x: `${String(localHour).padStart(2, '0')}:00`,
                    y: point.y,
                    top: point.top
                }
            })
        })

        heatmapSeries.value = days.map((day, idx) => ({
            name: day,
            data: localizedMatrix[idx]
        }))

        // Dynamic Color Scale Logic
        let maxVal = 0
        heatRes.data.forEach(d => {
            d.data.forEach(p => {
                if (p.y > maxVal) maxVal = p.y
            })
        })

        if (maxVal > 0) {
            // Gradient Scale: 10 steps from Green -> Yellow -> Orange -> Red
            // Plus specific 0 handling
            const colors = [
                '#10b981', '#34d399', '#6ee7b7', // Greens
                '#a3e635', '#facc15', '#f59e0b', // Yellows/Oranges
                '#fb923c', '#f87171', '#ef4444', '#dc2626' // Reds
            ]

            const ranges = []

            // Zero value (light/transparent)
            ranges.push({ from: 0, to: 0, color: '#f1f5f9', name: '0 B' })

            // Positive values divided into 10 buckets
            const step = maxVal / 10
            for (let i = 0; i < 10; i++) {
                ranges.push({
                    from: (i * step) + (i === 0 ? 0.000001 : 0), // Start just above 0
                    to: (i + 1) * step,
                    color: colors[i],
                    name: i < 3 ? 'Low' : (i < 7 ? 'Med' : 'High')
                })
            }

            heatmapOptions.value = {
                ...heatmapOptions.value,
                legend: { show: false }, // Hide default messy legend
                plotOptions: {
                    ...heatmapOptions.value.plotOptions,
                    heatmap: {
                        ...heatmapOptions.value.plotOptions.heatmap,
                        colorScale: {
                            ranges: ranges
                        }
                    }
                }
            }
        }

        // Update Options
        updateChartOptions(distRes.data, topRes.data, catRes.data)

        // Fetch paginated table
        await fetchUsageDetails()

    } catch (e) {
        console.error("Failed to load analytics", e)
    } finally {
        loading.value = false
    }
}

// Chart Options
const commonOptions = {
    chart: { toolbar: { show: false }, fontFamily: 'inherit', background: 'transparent' },
    theme: { mode: 'light' },
    stroke: { curve: 'smooth', width: 2 },
    xaxis: { type: 'datetime', tooltip: { enabled: false }, axisBorder: { show: false }, axisTicks: { show: false } },
    grid: { borderColor: '#f1f5f9', strokeDashArray: 4, padding: { top: 0, right: 0, bottom: 0, left: 10 } },
    colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
    dataLabels: { enabled: false },
    tooltip: { theme: 'dark' },
    legend: { position: 'top' }
}

const chartOptions = ref({
    ...commonOptions,
    tooltip: { theme: 'dark', x: { format: 'dd MMM HH:mm' } },
    yaxis: {
        labels: { formatter: (val) => formatBytes(val, 0) }
    },
    fill: { type: 'gradient', gradient: { opacityFrom: 0.5, opacityTo: 0.1 } }
})

const dnsChartOptions = ref({
    ...commonOptions,
    tooltip: { theme: 'dark', x: { format: 'dd MMM HH:mm' } },
    yaxis: {
        labels: { formatter: (val) => Math.round(val).toLocaleString() }
    },
    colors: ['#10b981', '#ef4444'], // Green for Passed, Red for Blocked
    fill: { type: 'gradient', gradient: { opacityFrom: 0.5, opacityTo: 0.1 } }
})

const donutOptions = ref({
    ...commonOptions,
    chart: { type: 'donut', fontFamily: 'inherit' },
    plotOptions: { pie: { donut: { size: '65%' } } },
    stroke: { show: false },
    labels: [],
    dataLabels: { enabled: false },
    legend: { position: 'bottom' }
})

const categoryOptions = ref({
    ...commonOptions,
    chart: { type: 'donut', fontFamily: 'inherit' },
    plotOptions: { pie: { donut: { size: '65%' } } },
    stroke: { show: false },
    labels: [],
    colors: ['#6366f1', '#8b5cf6', '#d946ef', '#f43f5e', '#f97316'],
    dataLabels: { enabled: false },
    legend: { position: 'bottom' },
    tooltip: {
        theme: 'dark',
        y: { formatter: (val) => formatBytes(val) }
    }
})

const queryTypeOptions = ref({
    ...commonOptions,
    chart: { type: 'donut', fontFamily: 'inherit' },
    plotOptions: { pie: { donut: { size: '65%' } } },
    stroke: { show: false },
    labels: [],
    colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'],
    dataLabels: { enabled: false },
    legend: { position: 'bottom' },
    tooltip: {
        theme: 'dark',
        y: { formatter: (val) => val.toLocaleString() }
    }
})

const heatmapOptions = ref({
    ...commonOptions,
    chart: { type: 'heatmap', fontFamily: 'inherit', toolbar: { show: false } },
    dataLabels: { enabled: false },
    legend: { position: 'right', offsetY: 50 }, // Scale beside chart
    plotOptions: {
        heatmap: {
            shadeIntensity: 0.5,
            radius: 4,
            useFillColorAsStroke: false,
            colorScale: {
                ranges: [] // Dynamic based on data
            }
        }
    },
    stroke: { show: true, width: 1, colors: ['#fff'] },
    xaxis: {
        type: 'category',
        tooltip: { enabled: false },
        labels: {
            rotate: -45,
            formatter: (val) => {
                // Show label only every 3 hours (00, 03, 06...)
                if (typeof val === 'string') {
                    const h = parseInt(val.split(':')[0])
                    if (!isNaN(h) && h % 3 === 0) return val
                    return ''
                }
                return val
            }
        },
        axisTicks: { show: false } // Hide ticks for cleaner look
    },
    tooltip: {
        custom: ({ series, seriesIndex, dataPointIndex, w }) => {
            try {
                // Defensive check to prevent crash
                if (!w.config.series || !w.config.series[seriesIndex] || !w.config.series[seriesIndex].data[dataPointIndex]) {
                    return ''
                }

                const data = w.config.series[seriesIndex].data[dataPointIndex]

                // If data is just a number or null (fallback)
                if (typeof data !== 'object' || data === null) {
                    return `<div class="px-2 py-1 bg-slate-800 text-white text-xs">${data}</div>`
                }

                const val = formatBytes(data.y || 0)
                const top = data.top || []

                // Filter out devices with 0 usage
                const activeTop = Array.isArray(top) ? top.filter(t => (t.value || 0) > 0) : []

                let html = `
                    <div class="px-3 py-2 bg-slate-800 text-white rounded shadow-lg border border-slate-700 text-xs font-sans z-50">
                        <div class="font-bold mb-1 border-b border-slate-600 pb-1 flex justify-between gap-4">
                            <span>${w.globals.seriesNames[seriesIndex]} ${data.x}</span>
                            <span class="text-blue-400">${val}</span>
                        </div>
                `

                if (activeTop.length > 0) {
                    html += `<div class="space-y-1 mt-1">`
                    activeTop.forEach(t => {
                        html += `
                            <div class="flex justify-between gap-3 text-[10px] text-slate-300">
                                <span class="truncate max-w-[100px]">${t.name || 'Unknown'}</span>
                                <span class="font-mono">${formatBytes(t.value || 0)}</span>
                            </div>
                        `
                    })
                    html += `</div>`
                } else {
                    html += `<div class="italic text-slate-500 text-[10px]">No activity</div>`
                }

                html += `</div>`
                return html
            } catch (e) {
                console.error("Tooltip error", e)
                return ''
            }
        }
    }
})

const barOptions = ref({
    // ...
    ...commonOptions,
    chart: { type: 'bar', fontFamily: 'inherit', toolbar: { show: false } },
    xaxis: { categories: [], axisBorder: { show: false }, axisTicks: { show: false } },
    plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } }
})

const dnsBarOptions = ref({
    ...commonOptions,
    chart: { type: 'bar', fontFamily: 'inherit', toolbar: { show: false } },
    plotOptions: { bar: { borderRadius: 4, columnWidth: '50%', distributed: true } },
    xaxis: { categories: [], axisBorder: { show: false }, axisTicks: { show: false }, labels: { style: { fontSize: '10px' } } }, // Smaller labels
    yaxis: { labels: { formatter: (val) => Math.round(val).toLocaleString() } },
    legend: { show: false }, // Hide legend for colored bars
    colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1', '#8b5cf6', '#d946ef', '#f43f5e'] // More colors
})

const updateChartOptions = (distData, topData, catData) => {
    donutOptions.value = {
        ...donutOptions.value,
        labels: distData.vendors.map(v => v.label)
    }

    barOptions.value = {
        ...barOptions.value,
        xaxis: { ...barOptions.value.xaxis, categories: distData.types.map(t => t.label) }
    }

    categoryOptions.value = {
        ...categoryOptions.value,
        labels: catData.map(c => c.label)
    }
}

const dnsStats = ref({
    total_queries: 0,
    blocked_queries: 0,
    block_percentage: 0,
    avg_response_time: 0
})

const dnsTrafficSeries = ref([])
const topBlockedDomains = ref([])
const topAllowedDomains = ref([])
const topClients = ref([])
const dnsClientsSeries = ref([])
const queryTypeSeries = ref([])
const riskyDevices = ref([])
const dnsPage = reactive({ blocked: 1, allowed: 1 })
const dnsLimit = 10

const changeDnsPage = (type, delta) => {
    if (type === 'blocked') {
        const newPage = dnsPage.blocked + delta
        if (newPage >= 1) {
            dnsPage.blocked = newPage
            fetchDnsData()
        }
    } else {
        const newPage = dnsPage.allowed + delta
        if (newPage >= 1) {
            dnsPage.allowed = newPage
            fetchDnsData()
        }
    }
}

const fetchDnsData = async () => {
    loading.value = true
    try {
        const blockedOffset = (dnsPage.blocked - 1) * dnsLimit
        const allowedOffset = (dnsPage.allowed - 1) * dnsLimit

        const [statsRes, trafficRes, blockedRes, allowedRes, clientsRes, qtypesRes, riskyRes] = await Promise.all([
            api.get(`/analytics/dns/stats?range=${timeRange.value}`),
            api.get(`/analytics/dns/traffic?range=${timeRange.value}`),
            api.get(`/analytics/dns/top-domains?range=${timeRange.value}&limit=${dnsLimit}&offset=${blockedOffset}&type=blocked`),
            api.get(`/analytics/dns/top-domains?range=${timeRange.value}&limit=${dnsLimit}&offset=${allowedOffset}&type=allowed`),
            api.get(`/analytics/dns/top-clients?range=${timeRange.value}&limit=10`),
            api.get(`/analytics/dns/query-types?range=${timeRange.value}`),
            api.get(`/analytics/dns/risky-devices?range=${timeRange.value}`)
        ])

        dnsStats.value = statsRes.data

        // Format Traffic Series
        const series = trafficRes.data
        dnsTrafficSeries.value = [
            { name: 'Passed', data: series.map(d => [parseUTC(d.timestamp).toJSDate().getTime(), d.total - d.blocked]) },
            { name: 'Blocked', data: series.map(d => [parseUTC(d.timestamp).toJSDate().getTime(), d.blocked]) }
        ]

        topBlockedDomains.value = blockedRes.data
        topAllowedDomains.value = allowedRes.data
        topClients.value = clientsRes.data

        // Format Top Clients Chart
        const clientNames = clientsRes.data.map(c => c.name || c.ip)
        const clientCounts = clientsRes.data.map(c => c.count)

        dnsBarOptions.value = {
            ...dnsBarOptions.value,
            xaxis: { ...dnsBarOptions.value.xaxis, categories: clientNames }
        }
        dnsClientsSeries.value = [{ name: 'Queries', data: clientCounts }]

        // Query Types
        queryTypeSeries.value = qtypesRes.data.map(q => q.value)
        queryTypeOptions.value = {
            ...queryTypeOptions.value,
            labels: qtypesRes.data.map(q => q.label)
        }

        riskyDevices.value = riskyRes.data

    } catch (e) {
        console.error("Failed to fetch DNS data", e)
    } finally {
        loading.value = false
    }
}

const getUsagePercent = (val) => {
    if (topDevices.value.length === 0) return 0
    const max = topDevices.value[0].total
    return max > 0 ? (val / max) * 100 : 0
}

const calculateAvgThroughput = () => {
    const total = trafficTotals.value.download + trafficTotals.value.upload
    if (total === 0) return '0 B/s'

    let seconds = 1
    const now = DateTime.now().toUTC()

    switch (timeRange.value) {
        case '24h':
        case 'yesterday':
            seconds = 24 * 3600
            break
        case '7d':
            seconds = 7 * 24 * 3600
            break
        case '30d':
            seconds = 30 * 24 * 3600
            break
        case '3m':
            seconds = 90 * 24 * 3600
            break
        case 'last_month':
            const thisMonth = now.startOf('month')
            const lastMonthEnd = thisMonth.minus({ milliseconds: 1 })
            const lastMonthStart = lastMonthEnd.startOf('month')
            seconds = Math.ceil(lastMonthEnd.diff(lastMonthStart, 'seconds').seconds)
            break
        case 'mtd':
            const mtdStart = now.startOf('month')
            seconds = Math.max(1, now.diff(mtdStart, 'seconds').seconds)
            break
        case 'ytd':
            const ytdStart = now.startOf('year')
            seconds = Math.max(1, now.diff(ytdStart, 'seconds').seconds)
            break
        case '1y':
            seconds = 365 * 24 * 3600
            break
        case 'all':
            // Try to find earliest data point, else default to 1y
            let earliest = now.toMillis()
            if (chartSeries.value.length > 0 && chartSeries.value[0].data.length > 0) {
                earliest = chartSeries.value[0].data[0][0]
            }
            const diff = (now.toMillis() - earliest) / 1000
            seconds = Math.max(24 * 3600, diff) // Min 1 day
            break
    }

    return formatBytes(total / seconds) + '/s'
}

onMounted(async () => {
    await checkConfig()
    if (localConfigured.value) {
        await fetchData()
    } else {
        loading.value = false
    }
})

watch(timeRange, () => {
    usagePage.value = 1
    fetchData()
})

watch(currentView, () => {
    fetchData()
})

</script>
