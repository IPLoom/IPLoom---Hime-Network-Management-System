import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import tooltip from './directives/tooltip'
import clickOutside from './directives/click-outside'
import VueApexCharts from "vue3-apexcharts"
import VNetworkGraph from "v-network-graph"
import "v-network-graph/lib/style.css"

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(VueApexCharts)
app.use(VNetworkGraph)
app.directive('tooltip', tooltip)
app.directive('click-outside', clickOutside)

// Initialize auth store
import { useAuthStore } from './stores/authStore'
const authStore = useAuthStore()
authStore.init()

app.mount('#app')
