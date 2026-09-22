<!-- 宽屏全局导航：只负责桌面导航的布局和交互呈现，不承担路由业务逻辑。 -->
<template>
  <div class="nav-container desktop-nav">
    <div class="nav-search" role="search">
      <div class="search-container">
        <Select
          v-model="searchTypeModel"
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
            :value="searchKeyword"
            type="search"
            class="search-input"
            placeholder="搜索题目..."
            aria-label="搜索题目"
            @input="handleKeywordInput"
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
      <RouterLink to="/adaptation" class="nav-link">改编题</RouterLink>
      <span class="nav-link disabled" aria-disabled="true">资源</span>

      <Dropdown v-if="isAdmin" trigger="hover" @command="handleManageCommand">
        <template #trigger>
          <span class="nav-link dropdown-trigger">
            管理
            <font-awesome-icon :icon="['fas', 'chevron-down']" class="ml-1.5 text-xs" aria-hidden="true" />
          </span>
        </template>
        <template #dropdown>
          <DropdownItem v-for="item in manageItems" :key="item.command" :command="item.command">
            {{ item.label }}
          </DropdownItem>
        </template>
      </Dropdown>
    </div>

    <div class="nav-user">
      <template v-if="isLoggedIn">
        <RouterLink to="/user/center" class="username">{{ username }}</RouterLink>
        <CustomButton size="sm" @click="emit('logout')">退出</CustomButton>
      </template>
      <template v-else>
        <CustomButton size="sm" @click="emit('login')">登录</CustomButton>
        <CustomButton size="sm" type="primary" @click="emit('register')">注册</CustomButton>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ManageCommand, ManageItem, SearchType, SearchTypeOption } from '@/composables/useNavigation'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import Select from '@/components/basic/Select.vue'

interface Props {
  searchType: SearchType
  searchKeyword: string
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
  search: []
  'manage-command': [command: ManageCommand]
  login: []
  register: []
  logout: []
}>()

const searchTypeModel = computed<SearchType>({
  get: () => props.searchType,
  set: (value) => emit('update:searchType', value),
})

const handleKeywordInput = (event: Event) => {
  if (event.currentTarget instanceof HTMLInputElement) {
    emit('update:searchKeyword', event.currentTarget.value)
  }
}

const handleSearch = () => emit('search')

const handleManageCommand = (command: string | number) => {
  if (typeof command !== 'string') return
  const item = props.manageItems.find((candidate) => candidate.command === command)
  if (item) emit('manage-command', item.command)
}
</script>

<style scoped>
.desktop-nav {
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

.search-btn {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #8b6f47;
  cursor: pointer;
}

.search-btn:hover {
  background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
}

.search-btn:focus-visible {
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

@media (max-width: 1279px) {
  .desktop-nav {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .nav-link,
  .search-container {
    transition: none;
  }
}
</style>
