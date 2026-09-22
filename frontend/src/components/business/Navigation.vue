<!-- 全局导航外壳：组合宽屏与窄屏呈现组件，共享导航状态和业务动作。 -->
<template>
  <nav class="navigation">
    <NavigationDesktop
      v-model:search-type="searchType"
      v-model:search-keyword="searchKeyword"
      :search-type-options="searchTypeOptions"
      :manage-items="manageItems"
      :is-admin="authStore.isAdmin()"
      :is-logged-in="authStore.isLoggedIn()"
      :username="authStore.userInfo?.username ?? ''"
      @search="handleSearch"
      @manage-command="handleManageCommand"
      @login="goToLogin"
      @register="goToRegister"
      @logout="handleLogout"
    />

    <NavigationMobile
      v-model:search-type="searchType"
      v-model:search-keyword="searchKeyword"
      v-model:menu-open="mobileMenuOpen"
      :search-type-options="searchTypeOptions"
      :manage-items="manageItems"
      :is-admin="authStore.isAdmin()"
      :is-logged-in="authStore.isLoggedIn()"
      :username="authStore.userInfo?.username ?? ''"
      @search="handleSearch"
      @manage-command="handleManageCommand"
      @login="goToLogin"
      @register="goToRegister"
      @user-center="goToUserCenter"
      @logout="handleLogout"
    />
  </nav>
</template>

<script setup lang="ts">
/**
 * 全局导航组合器。
 * 宽屏和窄屏只负责不同呈现，搜索、权限入口、跳转和退出逻辑统一由 composable 提供。
 */
import NavigationDesktop from '@/components/business/NavigationDesktop.vue'
import NavigationMobile from '@/components/business/NavigationMobile.vue'
import { useNavigation } from '@/composables/useNavigation'

const {
  authStore,
  searchTypeOptions,
  manageItems,
  searchType,
  searchKeyword,
  mobileMenuOpen,
  handleSearch,
  goToLogin,
  goToRegister,
  goToUserCenter,
  handleManageCommand,
  handleLogout,
} = useNavigation()
</script>

<style scoped>
.navigation {
  position: fixed;
  inset: 0 0 auto;
  z-index: 1000;
  height: var(--app-nav-height);
  padding-top: env(safe-area-inset-top);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: color-mix(in srgb, var(--brand-surface) 92%, transparent);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(12px);
}
</style>
