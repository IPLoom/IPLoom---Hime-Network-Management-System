<template>
    <div class="premium-card !p-0 h-[calc(100vh-120px)] flex flex-col overflow-hidden" @click="closeDropdowns">
        
        <!-- Header: Smart Filter Bar -->
        <div class="flex flex-col lg:flex-row lg:items-center justify-between px-4 sm:px-6 py-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 z-50 gap-4 lg:gap-0">
            <!-- Left: Legend & Title -->
            <div class="flex flex-wrap items-center gap-4 sm:gap-6">
                <div class="flex items-center gap-3 pr-4 sm:pr-6 border-r border-slate-200 dark:border-slate-700 h-11">
                    <h2 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 whitespace-nowrap">Network Map</h2>
                </div>
                <div class="flex items-center gap-3 sm:gap-5 overflow-x-auto no-scrollbar">
                    <div class="flex items-center gap-2 whitespace-nowrap">
                        <div class="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.4)]"></div>
                        <span class="text-[10px] font-black uppercase tracking-widest text-slate-500 hidden sm:inline">Active</span>
                    </div>
                    <div class="flex items-center gap-2 whitespace-nowrap">
                        <div class="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.4)]"></div>
                        <span class="text-[10px] font-black uppercase tracking-widest text-slate-500 hidden sm:inline">Threat</span>
                    </div>
                    <div class="flex items-center gap-2 whitespace-nowrap">
                        <div class="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.4)]"></div>
                        <span class="text-[10px] font-black uppercase tracking-widest text-slate-500 hidden sm:inline">Insecure</span>
                    </div>
                </div>
            </div>

            <!-- Right: Searchable Dropdowns -->
            <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                
                <!-- 1. Searchable Port Dropdown -->
                <div class="relative h-11 w-full sm:w-40 lg:w-48" @click.stop>
                    <div class="h-full flex items-center bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 rounded-xl px-4 gap-3 cursor-text group focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all"
                         @click="showPortDropdown = !showPortDropdown">
                        <Filter class="w-4 h-4 text-slate-400 shrink-0" />
                        <input 
                            v-model="portSearchQuery"
                            placeholder="All Ports"
                            class="bg-transparent border-none outline-none text-[10px] font-black uppercase tracking-widest text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400"
                            @focus="showPortDropdown = true"
                        />
                        <ChevronDown class="w-4 h-4 text-slate-400 shrink-0 transition-transform duration-300" :class="{ 'rotate-180': showPortDropdown }" />
                    </div>

                    <!-- Dropdown List -->
                    <transition name="fade-slide">
                        <div v-if="showPortDropdown" class="absolute top-12 left-0 right-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden z-[100] max-h-60 overflow-y-auto">
                            <div 
                                @click="selectPort(null)"
                                class="px-4 py-2.5 text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors border-b border-slate-100 dark:border-slate-700/50"
                                :class="{ 'text-blue-500 bg-blue-50/30 dark:bg-blue-900/10': selectedPortFilter === null }"
                            >
                                All Ports
                            </div>
                            <div 
                                v-for="port in filteredPorts" :key="port"
                                @click="selectPort(port)"
                                class="px-4 py-2.5 text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                                :class="{ 'text-blue-500 bg-blue-50/30 dark:bg-blue-900/10': selectedPortFilter === port }"
                            >
                                Port {{ port }}
                            </div>
                        </div>
                    </transition>
                </div>

                <!-- 2. Searchable Device Dropdown -->
                <div class="relative h-11 w-full sm:w-64 lg:w-80" @click.stop>
                    <div class="h-full flex items-center bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 rounded-xl px-4 gap-3 cursor-text group focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all"
                         @click="showDeviceDropdown = !showDeviceDropdown">
                        <Search class="w-4 h-4 text-slate-400 shrink-0" />
                        <input 
                            v-model="deviceSearchQuery"
                            placeholder="Find Device..."
                            class="bg-transparent border-none outline-none text-[11px] font-bold text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400 placeholder:font-medium"
                            @focus="showDeviceDropdown = true"
                        />
                        <ChevronDown class="w-4 h-4 text-slate-400 shrink-0 transition-transform duration-300" :class="{ 'rotate-180': showDeviceDropdown }" />
                    </div>

                    <!-- Dropdown List -->
                    <transition name="fade-slide">
                        <div v-if="showDeviceDropdown" class="absolute top-12 left-0 right-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden z-[100] max-h-80 overflow-y-auto">
                            <div 
                                @click="selectDevice(null)"
                                class="px-4 py-3 text-[11px] font-bold hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors border-b border-slate-100 dark:border-slate-700/50"
                                :class="{ 'text-blue-500 bg-blue-50/30 dark:bg-blue-900/10': !searchQuery }"
                            >
                                All Devices
                            </div>
                            <div 
                                v-for="node in filteredNodesForDropdown" :key="node.id"
                                @click="selectDevice(node)"
                                class="px-4 py-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                                :class="{ 'text-blue-500 bg-blue-50/30 dark:bg-blue-900/10': searchQuery === node.name || searchQuery === node.ip }"
                            >
                                <div class="flex items-center gap-3">
                                    <div class="p-1.5 rounded-lg text-white" :style="{ backgroundColor: getNodeColor(node) }">
                                        <component :is="getIcon(node.icon)" class="w-3.5 h-3.5" />
                                    </div>
                                    <div class="flex flex-col min-w-0">
                                        <span class="text-[11px] font-bold truncate max-w-[120px] sm:max-w-[160px]">{{ node.name }}</span>
                                        <span class="text-[9px] font-mono text-slate-400">{{ node.ip }}</span>
                                    </div>
                                </div>
                                <div class="flex flex-col items-end gap-1 shrink-0">
                                    <span class="text-[8px] font-black uppercase tracking-tighter px-1.5 py-0.5 rounded-md bg-slate-100 dark:bg-slate-900 text-slate-500">{{ node.type }}</span>
                                    <div v-if="node.open_ports?.length" class="flex gap-1">
                                        <div v-for="p in node.open_ports.slice(0, 3)" :key="p.port" class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: getPortColor(p.port, p.service) }"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </transition>
                </div>

                <!-- Refresh -->
                <button @click="fetchTopology" class="h-11 w-11 flex items-center justify-center bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 hover:border-slate-300 dark:hover:border-slate-600 text-slate-500 dark:text-slate-400 transition-all shrink-0" v-tooltip="'Refresh View'">
                    <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
                </button>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="flex-1 relative overflow-hidden">
            <!-- Loading State -->
            <div v-if="loading"
                class="absolute inset-0 flex items-center justify-center z-10 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
                <Loader2 class="h-10 w-10 animate-spin text-blue-500" />
            </div>

            <!-- Graph -->
            <v-network-graph v-if="!loading" class="w-full h-full" :nodes="nodes" :edges="edges"
                :configs="configs" v-model:zoom-level="zoomLevel" :event-handlers="eventHandlers">
                <!-- Custom Node Rendering -->
                <template #override-node="{ nodeId, scale, config }">
                    <!-- Search/Filter Highlight Ring -->
                    <circle v-if="isHighlighted(nodes[nodeId])" :r="(nodes[nodeId].isPort ? 12 : 20) * 2.2"
                        fill="none" stroke="#3b82f6" stroke-width="3" class="animate-pulse" />

                    <!-- Vulnerability Warning Glow -->
                    <circle v-if="!nodes[nodeId].isPort && nodes[nodeId].open_ports?.some(p => isInsecurePort(p.port))" 
                        :r="20 * 2.5" fill="none" stroke="rgba(245, 158, 11, 0.3)" stroke-width="12" class="animate-pulse" />

                    <!-- Activity Heatmap -->
                    <circle v-if="!nodes[nodeId].isPort" :r="20 * 2.2" :fill="getActivityColor(nodes[nodeId].last_seen)"
                        class="transition-all duration-1000" :class="{ 'opacity-10': isDimmed(nodes[nodeId]) }" />

                    <!-- Red Alert -->
                    <circle v-if="nodes[nodeId].block_count > 10" :r="(nodes[nodeId].isPort ? 12 : 20) * 1.8" fill="none"
                        stroke="rgba(239, 68, 68, 0.5)" stroke-width="6" class="animate-pulse" />

                    <circle :r="(nodes[nodeId].isPort ? 12 : 20) * 1.5" :fill="getNodeColor(nodes[nodeId])"
                        class="transition-all duration-300" :class="{
                            'filter drop-shadow-lg scale-110': selectedNodeId === nodeId,
                            'opacity-20': isDimmed(nodes[nodeId]),
                            'opacity-40': !searchQuery && !selectedPortFilter && selectedNodeId && selectedNodeId !== nodeId,
                            'cursor-pointer hover:brightness-110': true
                        }" />

                    <!-- Badges -->
                    <g v-if="nodes[nodeId].block_count > 10" :transform="`translate(${nodes[nodeId].isPort ? 10 : 20}, -${nodes[nodeId].isPort ? 10 : 20})`"
                        :class="{ 'opacity-20': isDimmed(nodes[nodeId]) }">
                        <circle r="8" fill="#ef4444" class="filter drop-shadow-sm" />
                        <text y="3" text-anchor="middle" fill="white" class="text-[9px] font-black pointer-events-none">!</text>
                    </g>

                    <g v-if="nodes[nodeId].isPort && isInsecurePort(nodes[nodeId].port)" :transform="`translate(10, -10)`"
                        :class="{ 'opacity-20': isDimmed(nodes[nodeId]) }">
                        <circle r="6" fill="#f59e0b" />
                        <text y="2.5" text-anchor="middle" fill="white" class="text-[7px] font-black pointer-events-none">?</text>
                    </g>

                    <!-- Icon -->
                    <foreignObject :x="-(nodes[nodeId].isPort ? 12 : 20)" :y="-(nodes[nodeId].isPort ? 12 : 20)"
                        :width="(nodes[nodeId].isPort ? 12 : 20) * 2" :height="(nodes[nodeId].isPort ? 12 : 20) * 2"
                        class="pointer-events-none transition-opacity"
                        :class="{ 'opacity-20': isDimmed(nodes[nodeId]) }">
                        <div class="flex items-center justify-center h-full w-full text-white">
                            <component :is="getIcon(nodes[nodeId].icon)" :size="(nodes[nodeId].isPort ? 12 : 20) * 1.2"
                                stroke-width="2" />
                        </div>
                    </foreignObject>
                </template>

                <!-- Tooltip / Label -->
                <template #override-node-label="{ nodeId, scale, config, text }">
                    <text x="0" :y="(config.radius || 20) + 25" text-anchor="middle" fill="currentColor"
                        class="text-[11px] font-bold tracking-tight pointer-events-none transition-all"
                        :class="{
                            'fill-blue-600 dark:fill-blue-400': selectedNodeId === nodeId || isHighlighted(nodes[nodeId]),
                            'fill-slate-500 dark:fill-slate-400': selectedNodeId !== nodeId && !isHighlighted(nodes[nodeId]),
                            'opacity-20': isDimmed(nodes[nodeId])
                        }">
                        {{ text }}
                    </text>
                </template>
            </v-network-graph>

            <!-- Mini Profile Card -->
            <transition name="slide-up">
                <div v-if="selectedNode"
                    class="absolute bottom-4 sm:bottom-6 left-4 sm:left-6 w-[calc(100%-32px)] sm:w-80 bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl shadow-2xl p-4 sm:p-5 z-20 max-h-[60%] overflow-y-auto">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex items-center gap-4">
                            <div class="p-3 rounded-2xl text-white shadow-lg shrink-0" :style="{ backgroundColor: getNodeColor(selectedNode) }">
                                <component :is="getIcon(selectedNode.icon)" class="w-6 h-6" />
                            </div>
                            <div class="min-w-0">
                                <h3 class="text-base font-black text-slate-900 dark:text-white truncate">
                                    {{ selectedNode.name }}
                                </h3>
                                <p class="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{{ selectedNode.ip }}</p>
                            </div>
                        </div>
                        <button @click="selectedNodeId = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
                            <X class="w-4 h-4" />
                        </button>
                    </div>

                    <!-- Vulnerability Warning -->
                    <div v-if="!selectedNode.isPort && selectedNode.open_ports?.some(p => isInsecurePort(p.port))" 
                        class="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-900/50 rounded-2xl flex items-center gap-3">
                        <div class="p-2 bg-amber-100 dark:bg-amber-900/40 rounded-xl text-amber-600 dark:text-amber-400">
                            <ShieldAlert class="w-4 h-4" />
                        </div>
                        <div class="min-w-0">
                            <div class="text-[10px] font-black text-amber-600 dark:text-amber-400 uppercase tracking-widest">Insecure Ports</div>
                            <div class="text-xs text-amber-900 dark:text-amber-200 font-medium">Unencrypted services detected</div>
                        </div>
                    </div>

                    <!-- Live Traffic Stats -->
                    <div class="grid grid-cols-2 gap-3 mb-6">
                        <div class="bg-slate-50 dark:bg-slate-900/50 rounded-2xl p-3 border border-slate-100 dark:border-slate-700/50">
                            <div class="flex items-center gap-1.5 text-[9px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest mb-1">
                                <ArrowDown class="w-3 h-3" /> Download
                            </div>
                            <div class="text-[11px] font-bold text-slate-900 dark:text-white">{{ formatBytes(selectedNode.down_rate || 0) }}/s</div>
                        </div>
                        <div class="bg-slate-50 dark:bg-slate-900/50 rounded-2xl p-3 border border-slate-100 dark:border-slate-700/50">
                            <div class="flex items-center gap-1.5 text-[9px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-1">
                                <ArrowUp class="w-3 h-3" /> Upload
                            </div>
                            <div class="text-[11px] font-bold text-slate-900 dark:text-white">{{ formatBytes(selectedNode.up_rate || 0) }}/s</div>
                        </div>
                    </div>

                    <router-link :to="`/devices/${selectedNodeId}`" 
                        class="w-full flex items-center justify-center gap-2 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl text-[11px] font-black uppercase tracking-[0.1em] hover:opacity-90 transition-all shadow-lg">
                        Manage Device <ExternalLink class="w-3.5 h-3.5" />
                    </router-link>

                    <!-- Risk Warning -->
                    <div v-if="selectedNode.block_count > 10" class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/50 rounded-2xl flex items-center gap-3">
                        <div class="p-2 bg-red-100 dark:bg-red-900/40 rounded-xl text-red-600 dark:text-red-400">
                            <AlertTriangle class="w-4 h-4" />
                        </div>
                        <div class="min-w-0">
                            <div class="text-[10px] font-black text-red-600 dark:text-red-400 uppercase tracking-widest">High Risk Activity</div>
                            <div class="text-xs text-red-900 dark:text-red-200 font-medium">{{ selectedNode.block_count }} DNS threats blocked</div>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- Controls -->
            <div
                class="absolute bottom-4 sm:bottom-6 right-4 sm:right-6 flex flex-col gap-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur-lg p-2 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 z-10">
                <button @click="zoomIn" class="btn-action !p-2 sm:!p-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20" v-tooltip="'Zoom In'">
                    <Plus class="h-4 w-4 sm:h-5 sm:w-5" />
                </button>
                <button @click="zoomOut" class="btn-action !p-2 sm:!p-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20" v-tooltip="'Zoom Out'">
                    <Minus class="h-4 w-4 sm:h-5 sm:w-5" />
                </button>
            </div>

            <!-- Floating Tooltip -->
            <div v-if="tooltip.visible && !isMobile" 
                class="fixed pointer-events-none z-[100] px-3 py-1.5 bg-slate-900/90 backdrop-blur-md text-white text-[10px] font-black uppercase tracking-widest rounded-lg shadow-2xl border border-slate-700/50 flex items-center gap-2"
                :style="{ left: tooltip.x + 15 + 'px', top: tooltip.y + 15 + 'px' }">
                <div class="w-1 h-1 rounded-full bg-blue-400"></div>
                {{ tooltip.content }}
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed, onUnmounted } from "vue"
import * as vNG from "v-network-graph"
import { ForceLayout } from "v-network-graph/lib/force-layout"
import api from '@/utils/api'
import { getIcon } from '@/utils/icons'
import { formatBytes } from '@/utils/format'
import {
    Loader2, Plus, Minus, RefreshCw, X, ArrowDown, ArrowUp, ExternalLink, AlertTriangle, Search, ShieldAlert, Filter, ChevronDown
} from 'lucide-vue-next'

const nodes = ref<any>({})
const edges = ref<any>({})
const loading = ref(true)
const zoomLevel = ref(1.0)
const selectedNodeId = ref<string | null>(null)
const isMobile = ref(window.innerWidth < 640)

// Dropdown States
const showPortDropdown = ref(false)
const showDeviceDropdown = ref(false)
const portSearchQuery = ref("")
const deviceSearchQuery = ref("")

const searchQuery = ref("")
const selectedPortFilter = ref<number | null>(null)

const tooltip = reactive({
    visible: false,
    content: '',
    x: 0,
    y: 0
})

const selectedNode = computed(() => {
    if (!selectedNodeId.value) return null
    return nodes.value[selectedNodeId.value]
})

const uniquePorts = computed(() => {
    const ports = new Set<number>()
    Object.values(nodes.value).forEach((n: any) => {
        if (n.isPort) ports.add(n.port)
    })
    return Array.from(ports).sort((a, b) => a - b)
})

const filteredPorts = computed(() => {
    const q = portSearchQuery.value.toLowerCase()
    if (!q) return uniquePorts.value
    return uniquePorts.value.filter(p => p.toString().includes(q))
})

const filteredNodesForDropdown = computed(() => {
    const q = deviceSearchQuery.value.toLowerCase()
    const allNodes = Object.values(nodes.value).filter((n: any) => !n.isPort)
    if (!q) return allNodes
    return allNodes.filter((n: any) => 
        n.name?.toLowerCase().includes(q) || 
        n.ip?.toLowerCase().includes(q) ||
        n.vendor?.toLowerCase().includes(q)
    )
})

const handleResize = () => {
    isMobile.value = window.innerWidth < 640
}

const closeDropdowns = () => {
    showPortDropdown.value = false
    showDeviceDropdown.value = false
}

const selectPort = (port: number | null) => {
    selectedPortFilter.value = port
    portSearchQuery.value = port ? `Port ${port}` : ""
    showPortDropdown.value = false
}

const selectDevice = (node: any | null) => {
    if (!node) {
        searchQuery.value = ""
        deviceSearchQuery.value = ""
    } else {
        searchQuery.value = node.ip 
        deviceSearchQuery.value = node.name
    }
    showDeviceDropdown.value = false
}

const isInsecurePort = (port: number) => [21, 23, 161, 389, 445].includes(port)

const matchesSearch = (node: any) => {
    if (!searchQuery.value) return true
    const q = searchQuery.value.toLowerCase()
    return (
        node.name?.toLowerCase().includes(q) ||
        node.ip?.toLowerCase().includes(q) ||
        node.type?.toLowerCase().includes(q) ||
        node.vendor?.toLowerCase().includes(q) ||
        node.port?.toString().includes(q) ||
        node.service?.toLowerCase().includes(q)
    )
}

const isHighlighted = (node: any) => {
    if (searchQuery.value && matchesSearch(node)) return true
    if (selectedPortFilter.value !== null) {
        if (node.isPort && node.port === selectedPortFilter.value) return true
        if (!node.isPort && node.open_ports?.some((p: any) => p.port === selectedPortFilter.value)) return true
    }
    return false
}

const isDimmed = (node: any) => {
    if (!searchQuery.value && selectedPortFilter.value === null) return false
    return !isHighlighted(node)
}

// Configs for v-network-graph
const configs = reactive(
    vNG.defineConfigs({
        view: {
            panEnabled: true,
            zoomEnabled: true,
            layoutHandler: new ForceLayout({
                positionFixedByDrag: false,
                positionFixedByClickWithAltKey: true,
                createSimulation: (d3, d3Nodes, d3Edges) => {
                    const forceLink = d3.forceLink(d3Edges).id((d: any) => d.id)
                    
                    const categoryTargets: any = {
                        'Router': { x: 0, y: 0 },
                        'Mobile': { x: 300, y: 300 },
                        'Desktop': { x: -300, y: 300 },
                        'Server': { x: -300, y: -300 },
                        'IoT': { x: 300, y: -300 },
                        'Entertainment': { x: 0, y: 450 }
                    }

                    const sim = d3
                        .forceSimulation(d3Nodes)
                        .force("edge", forceLink.distance((d: any) => {
                            const edgeId = `edge_${d.source.id}_${d.target.id}`
                            const edge = edges.value[edgeId]
                            return edge?.isPortEdge ? 60 : 150
                        }))
                        .force("charge", d3.forceManyBody().strength(-1500))
                        .force("collide", d3.forceCollide(80))
                        .force("center", d3.forceCenter().strength(0.05))
                        .alphaMin(0.001)

                    sim.force("x", d3.forceX().strength(0.08).x((d: any) => {
                        const node = nodes.value[d.id]
                        if (!node) return 0
                        return categoryTargets[node.type]?.x || 0
                    }))
                    sim.force("y", d3.forceY().strength(0.08).y((d: any) => {
                        const node = nodes.value[d.id]
                        if (!node) return 0
                        return categoryTargets[node.type]?.y || 0
                    }))
                    
                    return sim
                }
            }),
        },
        node: {
            normal: {
                type: "circle",
                radius: 20,
                color: "#4466cc",
            },
            hover: {
                radius: 24,
            },
            label: {
                visible: true,
                fontFamily: "Inter, sans-serif",
                fontSize: 14,
                color: "#ffffff",
            },
        },
        edge: {
            normal: {
                width: 2,
                color: "rgba(148, 163, 184, 0.2)",
            },
            hover: {
                width: 3,
                color: "#3b82f6",
            },
        },
        path: {
            visible: false
        }
    })
)

const eventHandlers: vNG.EventHandlers = {
    "node:click": ({ node }) => {
        const n = nodes.value[node]
        if (n && n.isPort) {
            window.open(`http://${n.ip}:${n.port}`, '_blank')
            return
        }
        selectedNodeId.value = node
    },
    "node:pointerover": ({ node, event }) => {
        const n = nodes.value[node]
        if (!n) return
        tooltip.visible = true
        tooltip.content = n.isPort 
            ? `Port ${n.port}: ${n.service.toUpperCase()} (${n.ip})`
            : `${n.name} • ${n.ip}`
        tooltip.x = event.clientX
        tooltip.y = event.clientY
    },
    "node:pointerout": () => {
        tooltip.visible = false
    },
    "view:click": () => {
        selectedNodeId.value = null
        closeDropdowns()
    }
}

const fetchTopology = async () => {
    if (Object.keys(nodes.value).length === 0) {
        loading.value = true
    }
    
    try {
        const res = await api.get("/topology/")
        const newNodes: any = {}
        const newEdges: any = res.data.edges

        Object.entries(res.data.nodes).forEach(([id, node]: [string, any]) => {
            if (nodes.value[id]) {
                node.x = nodes.value[id].x
                node.y = nodes.value[id].y
            }
            newNodes[id] = node

            if (node.open_ports && node.open_ports.length > 0) {
                node.open_ports.forEach((p: any) => {
                    const portId = `port:${id}:${p.port}`
                    newNodes[portId] = {
                        name: `${p.port}`,
                        service: p.service || 'unknown',
                        port: p.port,
                        ip: node.ip,
                        type: 'Port',
                        isPort: true,
                        icon: getPortIcon(p.port, p.service),
                        status: node.status
                    }
                    if (nodes.value[portId]) {
                        newNodes[portId].x = nodes.value[portId].x
                        newNodes[portId].y = nodes.value[portId].y
                    }
                    newEdges[`edge_${id}_${portId}`] = {
                        source: id,
                        target: portId,
                        isPortEdge: true
                    }
                })
            }
        })

        nodes.value = newNodes
        edges.value = newEdges
    } catch (e) {
        console.error("Failed to load topology", e)
    } finally {
        loading.value = false
    }
}

const getPortIcon = (port: number, service: string) => {
    const s = (service || '').toLowerCase()
    const p = port
    if (p === 80 || p === 443 || s.includes('http')) return 'Globe'
    if (p === 22 || s.includes('ssh')) return 'Terminal'
    if (p === 21 || s.includes('ftp')) return 'FolderSync'
    if (p === 23 || s.includes('telnet')) return 'Terminal'
    if (p === 53 || s.includes('dns')) return 'Shield'
    if (p === 1883 || p === 8883 || s.includes('mqtt')) return 'Zap'
    if (p === 32400 || s.includes('plex')) return 'Play'
    if (p === 8123 || s.includes('home-assistant')) return 'Home'
    if (p === 161 || s.includes('snmp')) return 'Activity'
    if (p === 3306 || p === 5432 || s.includes('sql') || s.includes('db')) return 'Database'
    if (p === 5000 || p === 5001 || s.includes('synology')) return 'Server'
    if (s.includes('vnc') || s.includes('rdp')) return 'Monitor'
    if (s.includes('printer')) return 'Printer'
    return 'Cpu'
}

const getPortColor = (port: number, service: string) => {
    const s = (service || '').toLowerCase()
    const p = port
    if (p === 80 || p === 443 || s.includes('http')) return '#06b6d4' 
    if (p === 22 || p === 23 || s.includes('ssh')) return '#8b5cf6'
    if (p === 1883 || p === 8123 || s.includes('mqtt')) return '#10b981'
    if (p === 3306 || p === 5432 || s.includes('sql')) return '#f59e0b'
    if (p === 32400 || s.includes('plex')) return '#f43f5e'
    return '#06b6d4'
}

const getActivityColor = (lastSeen: string | null) => {
    if (!lastSeen) return 'rgba(148, 163, 184, 0.05)'
    const diff = Date.now() - new Date(lastSeen).getTime()
    const mins = diff / 1000 / 60
    if (mins < 5) return 'rgba(34, 211, 238, 0.4)' 
    if (mins < 30) return 'rgba(34, 211, 238, 0.15)' 
    if (mins < 60) return 'rgba(148, 163, 184, 0.1)' 
    return 'rgba(148, 163, 184, 0.05)' 
}

const getNodeColor = (node: any) => {
    if (node.isPort) return getPortColor(node.port, node.service)
    if (node.type === 'Router') return '#6366f1'
    if (node.status === 'offline') return '#94a3b8'
    const colors: any = {
        'Mobile': '#10b981', 'Desktop': '#3b82f6', 'Server': '#8b5cf6', 'IoT': '#f59e0b', 'Entertainment': '#f43f5e'
    }
    if (node.type) {
        const type = node.type.toLowerCase()
        if (type.includes('phone') || type.includes('mobile')) return colors['Mobile']
        if (type.includes('pc') || type.includes('desktop') || type.includes('laptop')) return colors['Desktop']
        if (type.includes('server') || type.includes('nas')) return colors['Server']
        if (type.includes('iot') || type.includes('home') || type.includes('sensor')) return colors['IoT']
        if (type.includes('tv') || type.includes('entertainment') || type.includes('game')) return colors['Entertainment']
    }
    return '#3b82f6'
}

const zoomIn = () => {
    zoomLevel.value = Math.min(zoomLevel.value * 1.2, 5)
}
const zoomOut = () => {
    zoomLevel.value = Math.max(zoomLevel.value / 1.2, 0.1)
}

let pollInterval: any = null

onMounted(() => {
    fetchTopology()
    pollInterval = setInterval(fetchTopology, 10000)
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval)
    window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%) scale(0.9);
  opacity: 0;
}
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease-out;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>

<style>
.v-network-graph {
  background-color: transparent !important;
}
</style>
