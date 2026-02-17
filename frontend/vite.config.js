import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

/**
 * Vite配置文件
 * 配置路径别名、代理和Sass全局变量
 */
export default defineConfig({
  plugins: [vue()],
  
  // 路径别名配置
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  
  // CSS预处理器配置
  css: {
    postcss: './postcss.config.js',
    preprocessorOptions: {
      scss: {
        additionalData: `
          @use "@/styles/variables.scss" as *;
          @use "@/styles/mixins.scss" as *;
        `
      }
    }
  },
  
  // 开发服务器配置
  server: {
    port: 5174,
    // API代理配置（开发环境）
    proxy: {
      '/api': {
        target: 'http://localhost:8081',
        changeOrigin: true,
        // 不重写路径，保持/api前缀
        rewrite: (path) => path
      }
    }
  }
})
