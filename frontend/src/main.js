/**
 * Vue应用入口文件
 * 集成Element Plus、Router、Pinia、全局样式
 * 遵循KISS原则：简单的初始化逻辑
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'katex/dist/katex.min.css'
import App from './App.vue'
import router from './router'

// 导入全局样式（包含全局重置和通用样式）
import '@/styles/global.scss'

// 创建Vue应用实例
const app = createApp(App)

// 创建Pinia实例
const pinia = createPinia()

// 注册插件
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 挂载应用
app.mount('#app')
