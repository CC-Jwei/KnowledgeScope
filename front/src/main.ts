import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'virtual:uno.css'

import App from './App.vue'
import router from './router'

// Vue 应用实例，用在挂载根组件与插件
const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
