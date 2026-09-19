import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const backendProxy = {
  '/api': {
    target: 'http://localhost:7785',
    changeOrigin: true,
  },
  '/uploads': {
    target: 'http://localhost:7785',
    changeOrigin: true,
  },
}

/**
 * Vite 配置：开发服务器监听局域网地址，并将 API 与上传资源代理到后端。
 */
export default defineConfig({
  plugins: [vue()],
  
  // 路径别名配置
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'vue': 'vue/dist/vue.esm-bundler.js'
    }
  },
  
  // CSS预处理器配置
  css: {
    postcss: './postcss.config.js',
    // SCSS全局注入已移除，组件已迁移到Tailwind CSS
  },
  
  // 开发服务器配置
  server: {
    host: '0.0.0.0',
    port: 7784,
    proxy: backendProxy,
  },
  preview: {
    host: '0.0.0.0',
    proxy: backendProxy,
  },
})
