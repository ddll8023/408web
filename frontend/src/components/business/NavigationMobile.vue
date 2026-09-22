<!-- 窄屏全局导航：只负责移动导航的布局和交互呈现，不承担路由业务逻辑。 -->
<template>
  <div class="mobile-bar">
    <RouterLink to="/exam" class="mobile-brand" @click="closeMenu">408 题库</RouterLink>
    <div class="mobile-bar-actions">
      <span v-if="isLoggedIn" class="mobile-username">{{ username }}</span>
      <button
        type="button"
        class="mobile-menu-button"
        :aria-expanded="menuOpen"
        aria-controls="mobile-navigation-panel"
        :aria-label="menuOpen ? '关闭导航菜单' : '打开导航菜单'"
        @click="toggleMenu"
      >
        <font-awesome-icon :icon="['fas', menuOpen ? 'times' : 'bars']" aria-hidden="true" />
      </button>
    </div>
  </div>

  <Transition name="mobile-menu">
    <div v-if="menuOpen" id="mobile-navigation-panel" class="mobile-panel scrollbar-stable">
      <div class="mobile-search" role="search">
        <Select
          v-model="searchTypeModel"
          class="mobile-search-type"
          :options="searchTypeOptions"
          size="sm"
          placeholder="类型"
          aria-label="搜索类型"
          bordered
        />
        <input
          :value="searchKeyword"
          type="search"
          class="mobile-search-input"
          placeholder="搜索题目..."
          aria-label="搜索题目"
          @input="handleKeywordInput"
          @keyup.enter="handleSearch"
        />
        <button type="button" class="mobile-search-button" aria-label="搜索" @click="handleSearch">
          <font-awesome-icon :icon="['fas', 'magnifying-glass']" aria-hidden="true" />
        </button>
      </div>

      <div class="mobile-links" aria-label="主要导航">
        <RouterLink to="/exam" class="mobile-link" @click="closeMenu">真题首页</RouterLink>
        <RouterLink to="/exam/classify" class="mobile-link" @click="closeMenu">真题分类</RouterLink>
        <RouterLink to="/mock" class="mobile-link" @click="closeMenu">模拟题</RouterLink>
        <RouterLink to="/adaptation" class="mobile-link" @click="closeMenu">改编题</RouterLink>
        <span class="mobile-link disabled" aria-disabled="true">资源</span>
      </div>

      <section v-if="isAdmin" class="mobile-manage" aria-labelledby="mobile-manage-title">
        <h2 id="mobile-manage-title">管理</h2>
        <div class="mobile-manage-grid">
          <button
            v-for="item in manageItems"
            :key="item.command"
            type="button"
            @click="handleManageCommand(item.command)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>

      <div class="mobile-user-actions">
        <template v-if="isLoggedIn">
          <CustomButton block @click="emit('user-center')">个人中心</CustomButton>
          <CustomButton block type="danger" @click="emit('logout')">退出登录</CustomButton>
        </template>
        <template v-else>
          <CustomButton block @click="emit('login')">登录</CustomButton>
          <CustomButton block type="primary" @click="emit('register')">注册</CustomButton>
        </template>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ManageCommand, ManageItem, SearchType, SearchTypeOption } from '@/composables/useNavigation'
import CustomButton from '@/components/basic/CustomButton.vue'
import Select from '@/components/basic/Select.vue'

interface Props {
  searchType: SearchType
  searchKeyword: string
  menuOpen: boolean
  searchTypeOptions: SearchTypeOption[]
  manageItems: readonly ManageItem[]
  isAdmin: boolean
  isLoggedIn: boolean
  username: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:searchType': [value: SearchType]
  'update:searchKeyword': [value: string]
  'update:menuOpen': [value: boolean]
  search: []
  'manage-command': [command: ManageCommand]
  login: []
  register: []
  'user-center': []
  logout: []
}>()

const searchTypeModel = computed<SearchType>({
  get: () => props.searchType,
  set: (value) => emit('update:searchType', value),
})

const menuOpen = computed(() => props.menuOpen)

const closeMenu = () => emit('update:menuOpen', false)
const toggleMenu = () => emit('update:menuOpen', !props.menuOpen)
const handleSearch = () => emit('search')

const handleKeywordInput = (event: Event) => {
  if (event.currentTarget instanceof HTMLInputElement) {
    emit('update:searchKeyword', event.currentTarget.value)
  }
}

const handleManageCommand = (command: ManageCommand) => {
  closeMenu()
  emit('manage-command', command)
}
</script>

<style scoped>
.mobile-bar,
.mobile-panel {
  display: none;
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

@media (max-width: 1279px) {
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
    display: inline-flex;
    width: 42px;
    height: 42px;
    align-items: center;
    justify-content: center;
    border: 0;
    border-radius: 10px;
    background: color-mix(in srgb, var(--brand-accent) 8%, transparent);
    color: #8b6f47;
    cursor: pointer;
    font-size: 18px;
  }

  .mobile-menu-button:focus-visible,
  .mobile-search-button:focus-visible {
    outline: 2px solid #8b6f47;
    outline-offset: 2px;
  }

  .mobile-panel {
    /* 导航栏的 backdrop-filter 会改变固定子元素的包含块，显式设置高度以铺满可视区域。 */
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
    display: inline-flex;
    width: 42px;
    height: 42px;
    align-items: center;
    justify-content: center;
    border: 0;
    border-radius: 10px;
    background: #8b6f47;
    color: #fff;
    cursor: pointer;
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

@media (prefers-reduced-motion: reduce) {
  .mobile-menu-enter-active,
  .mobile-menu-leave-active {
    transition: none;
  }
}
</style>
