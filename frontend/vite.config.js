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
    preprocessorOptions: {
      scss: {
        // 全局注入Sass变量和mixins
        // 使用@use替代已弃用的@import，符合Dart Sass 3.0.0标准
        // as * 表示不使用命名空间，保持向后兼容
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
