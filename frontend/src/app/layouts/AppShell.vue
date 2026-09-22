<!-- 全局应用外壳：承载导航、路由视图和按路由控制的 keep-alive。 -->
<template>
  <div id="app">
    <Navigation v-if="showNavigation" />

    <div :class="['main-content', { 'with-nav': showNavigation }]">
      <component :is="pageLayout">
        <router-view v-slot="{ Component, route }">
          <keep-alive v-if="route.meta && route.meta.keepAlive">
            <component :is="Component" />
          </keep-alive>
          <component :is="Component" v-else />
        </router-view>
      </component>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 全局应用外壳。
 * 页面业务不再负责判断登录/注册页是否需要全局导航，路由元信息统一控制应用布局。
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AdminLayout from '@/app/layouts/AdminLayout.vue'
import Navigation from '@/components/business/Navigation.vue'

const route = useRoute()
const showNavigation = computed(() => route.meta.layout !== 'blank')
const pageLayout = computed(() => route.meta.layout === 'admin' ? AdminLayout : 'div')
</script>
