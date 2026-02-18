<template>
  <div id="app">
    <!-- 顶部导航栏（登录/注册页面不显示） -->
    <Navigation v-if="showNavigation" />
    
    <!-- 主内容区域 -->
    <div :class="['main-content', { 'with-nav': showNavigation }]">
      <router-view v-slot="{ Component, route }">
        <keep-alive v-if="route.meta && route.meta.keepAlive">
          <component
            :is="Component"
          />
        </keep-alive>
        <component
          :is="Component"
          v-else
        />
      </router-view>
    </div>
  </div>
</template>

<script setup>
/**
 * 应用根组件
 * 管理全局布局结构：导航栏 + 内容区域
 * 遵循KISS原则：简洁的布局管理
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navigation from '@/components/business/Navigation.vue'

const route = useRoute()

/**
 * 判断是否显示导航栏
 * 登录和注册页面不显示导航栏
 */
const showNavigation = computed(() => {
  const noNavRoutes = ['/login', '/register']
  return !noNavRoutes.includes(route.path)
})
</script>

<style scoped>
/**
 * 应用根组件样式
 * 使用 Tailwind CSS
 * 注：变量和mixins已通过Vite全局注入，无需手动导入
 */

/* 主内容区域 */
.main-content {
  min-height: 100vh;
}

/* 有导航栏时，添加顶部padding */
.main-content.with-nav {
  padding-top: 60px; /* $nav-height */
}
</style>
