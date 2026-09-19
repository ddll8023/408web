<!-- 全局导航组件：桌面端保持单行布局，窄屏切换为固定高度菜单栏与可滚动面板。 -->
<template>
  <nav class="navigation">
    <!-- 桌面导航 -->
    <div class="nav-container desktop-nav">
      <div class="nav-search" role="search">
        <div class="search-container">
          <Select
            v-model="searchType"
            class="search-type-select"
            :options="searchTypeOptions"
            size="sm"
            placeholder="类型"
            aria-label="搜索类型"
            bordered
          />
          <span class="search-divider" aria-hidden="true"></span>
          <div class="search-input-wrapper">
            <input
              v-model="searchKeyword"
              type="search"
              class="search-input"
              placeholder="搜索题目..."
              aria-label="搜索题目"
              @keyup.enter="handleSearch"
            />
            <button type="button" class="search-btn" aria-label="搜索" @click="handleSearch">
              <font-awesome-icon :icon="['fas', 'magnifying-glass']" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      <div class="nav-menu">
        <RouterLink to="/exam" class="nav-link">真题首页</RouterLink>
        <RouterLink to="/exam/classify" class="nav-link">真题分类</RouterLink>
        <RouterLink to="/mock" class="nav-link">模拟题</RouterLink>
        <span class="nav-link disabled" aria-disabled="true">资源</span>

        <Dropdown v-if="authStore.isAdmin()" trigger="hover" @command="handleManageCommand">
          <template #trigger>
            <span class="nav-link dropdown-trigger">
              管理
              <font-awesome-icon :icon="['fas', 'chevron-down']" class="ml-1.5 text-xs" aria-hidden="true" />
            </span>
          </template>
          <template #dropdown>
            <DropdownItem command="subject">科目管理</DropdownItem>
            <DropdownItem command="category">分类标签管理</DropdownItem>
            <DropdownItem command="exam">真题管理</DropdownItem>
            <DropdownItem command="mock">模拟题管理</DropdownItem>
            <DropdownItem command="compose">出题工作台</DropdownItem>
            <DropdownItem command="image">图片管理</DropdownItem>
            <DropdownItem command="exam-category">分类统计</DropdownItem>
          </template>
        </Dropdown>
      </div>

      <div class="nav-user">
        <template v-if="authStore.isLoggedIn()">
          <RouterLink to="/user/center" class="username">{{ authStore.userInfo?.username }}</RouterLink>
          <CustomButton size="sm" @click="handleLogout">退出</CustomButton>
        </template>
        <template v-else>
          <CustomButton size="sm" @click="goToLogin">登录</CustomButton>
          <CustomButton size="sm" type="primary" @click="goToRegister">注册</CustomButton>
        </template>
      </div>
    </div>

    <!-- 平板与移动端导航 -->
    <div class="mobile-bar">
      <RouterLink to="/exam" class="mobile-brand" @click="closeMobileMenu">408 题库</RouterLink>
      <div class="mobile-bar-actions">
        <span v-if="authStore.isLoggedIn()" class="mobile-username">{{ authStore.userInfo?.username }}</span>
        <button
          type="button"
          class="mobile-menu-button"
          :aria-expanded="mobileMenuOpen"
          aria-controls="mobile-navigation-panel"
          :aria-label="mobileMenuOpen ? '关闭导航菜单' : '打开导航菜单'"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <font-awesome-icon :icon="['fas', mobileMenuOpen ? 'times' : 'bars']" aria-hidden="true" />
        </button>
      </div>
    </div>

    <Transition name="mobile-menu">
      <div v-if="mobileMenuOpen" id="mobile-navigation-panel" class="mobile-panel scrollbar-stable">
        <div class="mobile-search" role="search">
          <Select
            v-model="searchType"
            class="mobile-search-type"
            :options="searchTypeOptions"
            size="sm"
            placeholder="类型"
            aria-label="搜索类型"
            bordered
          />
          <input
            v-model="searchKeyword"
            type="search"
            class="mobile-search-input"
            placeholder="搜索题目..."
            aria-label="搜索题目"
            @keyup.enter="handleSearch"
          />
          <button type="button" class="mobile-search-button" aria-label="搜索" @click="handleSearch">
            <font-awesome-icon :icon="['fas', 'magnifying-glass']" aria-hidden="true" />
          </button>
        </div>

        <div class="mobile-links" aria-label="主要导航">
          <RouterLink to="/exam" class="mobile-link" @click="closeMobileMenu">真题首页</RouterLink>
          <RouterLink to="/exam/classify" class="mobile-link" @click="closeMobileMenu">真题分类</RouterLink>
          <RouterLink to="/mock" class="mobile-link" @click="closeMobileMenu">模拟题</RouterLink>
          <span class="mobile-link disabled" aria-disabled="true">资源</span>
        </div>

        <section v-if="authStore.isAdmin()" class="mobile-manage" aria-labelledby="mobile-manage-title">
          <h2 id="mobile-manage-title">管理</h2>
          <div class="mobile-manage-grid">
            <button v-for="item in manageItems" :key="item.command" type="button" @click="handleManageCommand(item.command)">
              {{ item.label }}
            </button>
          </div>
        </section>

        <div class="mobile-user-actions">
          <template v-if="authStore.isLoggedIn()">
            <CustomButton block @click="goToUserCenter">个人中心</CustomButton>
            <CustomButton block type="danger" @click="handleLogout">退出登录</CustomButton>
          </template>
          <template v-else>
            <CustomButton block @click="goToLogin">登录</CustomButton>
            <CustomButton block type="primary" @click="goToRegister">注册</CustomButton>
          </template>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup lang="ts">
/**
 * 全局导航栏组件。
 * 桌面端展示完整导航，窄屏保持 60px 顶栏并将全部操作收纳到独立滚动面板。
 */
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import Select from '@/components/basic/Select.vue'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { showToast } = useToast()

const searchTypeOptions = [
  { label: '真题', value: 'exam' },
  { label: '模拟题', value: 'mock' },
]

const manageItems = [
  { command: 'subject', label: '科目管理' },
  { command: 'category', label: '分类标签管理' },
  { command: 'exam', label: '真题管理' },
  { command: 'mock', label: '模拟题管理' },
  { command: 'compose', label: '出题工作台' },
  { command: 'image', label: '图片管理' },
  { command: 'exam-category', label: '分类统计' },
] as const

type ManageCommand = typeof manageItems[number]['command']

const searchType = ref<'exam' | 'mock'>('exam')
const searchKeyword = ref('')
const mobileMenuOpen = ref(false)

const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}

const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    showToast('请输入搜索关键词', 'warning')
    return
  }

  const routeMap = {
    exam: '/manage/exam',
    mock: '/manage/mock',
  }

  closeMobileMenu()
  router.push({ path: routeMap[searchType.value], query: { keyword } })
}

const goToLogin = () => {
  closeMobileMenu()
  router.push('/login')
}

const goToRegister = () => {
  closeMobileMenu()
  router.push('/register')
}

const goToUserCenter = () => {
  closeMobileMenu()
  router.push('/user/center')
}

const handleManageCommand = (command: string | number) => {
  const routeMap: Record<ManageCommand, string> = {
    subject: '/manage/subject',
    category: '/manage/category',
    exam: '/manage/exam',
    mock: '/manage/mock',
    compose: '/manage/compose',
    image: '/manage/image',
    'exam-category': '/manage/exam-category',
  }
  const target = routeMap[command as ManageCommand]
  if (!target) return
  closeMobileMenu()
  router.push(target)
}

const handleLogout = () => {
  authStore.clearAuth()
  closeMobileMenu()
  showToast('已退出登录', 'success')
  router.push('/exam')
}

watch(() => route.fullPath, closeMobileMenu)
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

.nav-container {
  display: flex;
  width: 100%;
  max-width: 1400px;
  height: 60px;
  align-items: center;
  gap: 20px;
  margin: 0 auto;
  padding: 0 24px;
}

.nav-search {
  width: clamp(250px, 24vw, 340px);
  flex: 0 1 340px;
  min-width: 220px;
}

.search-container {
  display: flex;
  width: 100%;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  transition: box-shadow 0.2s ease;
}

.search-container:focus-within {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-accent) 12%, transparent);
}

.search-type-select {
  width: 82px;
  flex-shrink: 0;
}

.search-type-select :deep(.dropdown-control) {
  padding-right: 4px !important;
  padding-left: 8px !important;
}

.search-divider {
  width: 1px;
  height: 24px;
  flex-shrink: 0;
  margin: 0 8px;
  background: linear-gradient(to bottom, transparent, #d4c4a8, transparent);
}

.search-input-wrapper {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 6px;
}

.search-input {
  min-width: 0;
  height: 36px;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: #374151;
  font-size: 16px;
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-btn,
.mobile-menu-button,
.mobile-search-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  color: #8b6f47;
  cursor: pointer;
}

.search-btn {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 50%;
}

.search-btn:hover {
  background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
}

.search-btn:focus-visible,
.mobile-menu-button:focus-visible,
.mobile-search-button:focus-visible {
  outline: 2px solid #8b6f47;
  outline-offset: 2px;
}

.nav-menu {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  color: #374151;
  font-size: 15px;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.nav-link:not(.disabled):hover,
.nav-link.router-link-active:not(.disabled) {
  background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
  color: #6b5537;
}

.nav-link.disabled {
  color: #9ca3af;
  cursor: not-allowed;
}

.nav-user {
  display: flex;
  min-width: 170px;
  flex-shrink: 0;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.username {
  max-width: 110px;
  overflow: hidden;
  padding: 8px 10px;
  border-radius: 8px;
  color: #374151;
  text-overflow: ellipsis;
  text-decoration: none;
  white-space: nowrap;
}

.username:hover {
  background: color-mix(in srgb, var(--brand-accent) 8%, transparent);
  color: #8b6f47;
}

.mobile-bar,
.mobile-panel {
  display: none;
}

@media (max-width: 1279px) {
  .desktop-nav {
    display: none;
  }

  .mobile-bar {
    display: flex;
    height: 60px;
    align-items: center;
    justify-content: space-between;
    padding: 0 max(16px, env(safe-area-inset-right)) 0 max(16px, env(safe-area-inset-left));
  }

  .mobile-brand {
    color: #6b5537;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-decoration: none;
  }

  .mobile-bar-actions {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 10px;
  }

  .mobile-username {
    max-width: 120px;
    overflow: hidden;
    color: #6b7280;
    font-size: 13px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .mobile-menu-button {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: color-mix(in srgb, var(--brand-accent) 8%, transparent);
    font-size: 18px;
  }

  .mobile-panel {
    /* .navigation 带 backdrop-filter，会成为固定定位子元素的包含块，
       此时 bottom: 0 等于贴在导航栏底边，面板高度会被压成一条边，
       所以改为显式高度，保证面板铺满导航栏以下的可视区域。 */
    position: fixed;
    top: var(--app-nav-height);
    right: 0;
    left: 0;
    height: calc(100vh - var(--app-nav-height));
    display: block;
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 16px max(16px, env(safe-area-inset-right)) max(24px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
    border-top: 1px solid color-mix(in srgb, var(--brand-accent) 12%, transparent);
    background: #fbf7f2;
  }

  @supports (height: 100dvh) {
    .mobile-panel {
      height: calc(100dvh - var(--app-nav-height));
    }
  }

  .mobile-search {
    display: grid;
    grid-template-columns: 92px minmax(0, 1fr) 42px;
    align-items: center;
    gap: 8px;
    max-width: 720px;
    margin: 0 auto 16px;
  }

  .mobile-search-input {
    width: 100%;
    height: 42px;
    min-width: 0;
    padding: 0 12px;
    border: 1px solid #e6ddd3;
    border-radius: 10px;
    outline: 0;
    background: #fff;
    color: #374151;
    font-size: 16px;
  }

  .mobile-search-input:focus {
    border-color: #8b6f47;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-accent) 12%, transparent);
  }

  .mobile-search-button {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: #8b6f47;
    color: #fff;
  }

  .mobile-links {
    display: grid;
    max-width: 720px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin: 0 auto;
  }

  .mobile-link,
  .mobile-manage-grid button {
    display: flex;
    min-height: 44px;
    align-items: center;
    justify-content: center;
    padding: 10px 12px;
    border: 1px solid color-mix(in srgb, var(--brand-accent) 14%, transparent);
    border-radius: 10px;
    background: #fff;
    color: #374151;
    text-decoration: none;
  }

  .mobile-link.router-link-active {
    border-color: color-mix(in srgb, var(--brand-accent) 35%, transparent);
    background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
    color: #6b5537;
    font-weight: 600;
  }

  .mobile-link.disabled {
    color: #9ca3af;
  }

  .mobile-manage {
    max-width: 720px;
    margin: 20px auto 0;
    padding-top: 16px;
    border-top: 1px solid color-mix(in srgb, var(--brand-accent) 12%, transparent);
  }

  .mobile-manage h2 {
    margin: 0 0 10px;
    color: #6b5537;
    font-size: 14px;
    font-weight: 600;
  }

  .mobile-manage-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .mobile-manage-grid button {
    font-size: 14px;
    cursor: pointer;
  }

  .mobile-user-actions {
    display: grid;
    max-width: 720px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin: 20px auto 0;
    padding-top: 16px;
    border-top: 1px solid color-mix(in srgb, var(--brand-accent) 12%, transparent);
  }
}

@media (max-width: 420px) {
  .mobile-links,
  .mobile-manage-grid,
  .mobile-user-actions {
    grid-template-columns: 1fr;
  }
}

.mobile-menu-enter-active,
.mobile-menu-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.mobile-menu-enter-from,
.mobile-menu-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (prefers-reduced-motion: reduce) {
  .mobile-menu-enter-active,
  .mobile-menu-leave-active,
  .nav-link,
  .search-container {
    transition: none;
  }
}
</style>
