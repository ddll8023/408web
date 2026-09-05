import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

/**
 * Vite配置文件
 * 配置路径别名、代理和 Tailwind/PostCSS 样式处理
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
    port: 7784,
    // API代理配置（开发环境）
    proxy: {
      '/api': {
        target: 'http://localhost:7785',
        changeOrigin: true,
        // 不重写路径，保持/api前缀
        rewrite: (path) => path
      }
    }
  }
})
