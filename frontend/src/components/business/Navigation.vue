<template>
  <nav class="navigation fixed top-0 left-0 right-0 h-[60px] px-8 bg-[rgba(251,247,242,0.85)] backdrop-blur-md border-b border-black/[0.08] shadow-[0_2px_8px_rgba(0,0,0,0.1)] z-[1000]">
    <div class="nav-container h-full flex items-center justify-between px-8">
      <!-- 搜索区域 - 靠左 -->
      <div class="nav-search flex items-center justify-start relative bg-transparent">
        <Select
          v-model="searchType"
          class="w-[90px] flex-shrink-0"
          :options="searchTypeOptions"
          placeholder="类型"
        />
        <span class="search-divider w-px h-5 bg-black/[0.12] mx-2"></span>
        <div class="search-input-wrapper relative flex items-center flex-1">
          <input
            v-model="searchKeyword"
            type="text"
            class="w-full h-full bg-transparent border-none outline-none text-base text-gray-700 placeholder-gray-400"
            placeholder="搜索题目..."
            @keyup.enter="handleSearch"
          />
          <font-awesome-icon
            :icon="['fas', 'magnifying-glass']"
            class="search-icon text-gray-400 text-sm p-1.5 rounded-full transition-all duration-200 cursor-pointer hover:text-[#8B6F47] hover:bg-[rgba(139,111,71,0.1)] hover:scale-110 active:scale-95"
            @click="handleSearch"
          />
        </div>
      </div>

      <!-- 导航菜单 -->
      <div class="nav-menu flex items-center justify-center gap-8">
        <!-- 真题首页 - 独立导航 -->
        <span class="nav-link text-gray-800 no-underline text-base px-6 py-2.5 rounded transition-all duration-300 cursor-pointer select-none" @click="router.push('/exam')">真题首页</span>

        <!-- 真题分类 - 独立导航 -->
        <span class="nav-link text-gray-800 no-underline text-base px-6 py-2.5 rounded transition-all duration-300 cursor-pointer select-none" @click="router.push('/exam/classify')">真题分类</span>

        <!-- 模拟题 - 独立导航 -->
        <span class="nav-link text-gray-800 no-underline text-base px-6 py-2.5 rounded transition-all duration-300 cursor-pointer select-none" @click="router.push('/mock')">模拟题</span>

        <!-- 预留未来功能入口 -->
        <span class="nav-link disabled text-gray-400 cursor-not-allowed">资源</span>

        <!-- 管理菜单（仅ADMIN可见） -->
        <Dropdown v-if="authStore.isAdmin()" trigger="hover" @command="handleManageCommand">
          <template #trigger>
            <span class="nav-link dropdown-trigger inline-flex items-center cursor-pointer select-none text-gray-800 no-underline text-base px-6 py-2.5 rounded transition-all duration-300">
              管理
              <font-awesome-icon :icon="['fas', 'chevron-down']" class="ml-1.5 text-xs transition-transform duration-150" />
            </span>
          </template>

          <template #dropdown>
            <div class="dropdown-item" :data-command="'subject'">科目管理</div>
            <div class="dropdown-item" :data-command="'category'">分类标签管理</div>
            <div class="dropdown-item" :data-command="'exam'">真题管理</div>
            <div class="dropdown-item" :data-command="'mock'">模拟题管理</div>
            <div class="dropdown-item" :data-command="'image'">图片管理</div>
            <div class="dropdown-item" :data-command="'exam-category'">分类统计</div>
          </template>
        </Dropdown>
      </div>

      <!-- 用户信息区域 -->
      <div class="nav-user flex items-center justify-end gap-4">
        <template v-if="authStore.isLoggedIn()">
          <span class="username text-gray-800 text-sm cursor-pointer px-4 py-2 mr-2 rounded transition-all duration-300 select-none hover:bg-black/[0.05] hover:text-[#8B6F47]" @click="goToUserCenter">{{ authStore.userInfo?.username }}</span>
          <CustomButton size="sm" @click="handleLogout">退出</CustomButton>
        </template>
        <template v-else>
          <CustomButton size="sm" @click="goToLogin">登录</CustomButton>
          <CustomButton size="sm" type="primary" @click="goToRegister">注册</CustomButton>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
/**
 * 顶部导航栏组件
 * 功能：统一的导航菜单、用户信息展示、路由跳转
 * 遵循KISS原则：简洁的导航栏设计
 * 使用自定义Button组件替代Element Plus
 * 使用自定义Dropdown组件替代Element Plus
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import Select from '@/components/basic/Select.vue'

const router = useRouter()
const authStore = useAuthStore()

// 搜索类型选项
const searchTypeOptions = [
  { label: '真题', value: 'exam' },
  { label: '模拟题', value: 'mock' }
]

// 搜索相关状态
const searchType = ref('exam')  // 默认搜索真题
const searchKeyword = ref('')

/**
 * 显示消息提示
 * @param {string} message - 提示消息
 * @param {string} type - 消息类型 success/warning/error/info
 */
const showToast = (message, type = 'warning') => {
  const colors = {
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
    info: 'bg-blue-500'
  }

  const toast = document.createElement('div')
  toast.className = `fixed top-20 right-4 ${colors[type]} text-white px-4 py-2 rounded-lg shadow-lg z-[9999] transition-opacity duration-300`
  toast.textContent = message
  document.body.appendChild(toast)

  requestAnimationFrame(() => {
    toast.classList.remove('opacity-0')
  })

  setTimeout(() => {
    toast.classList.add('opacity-0')
    setTimeout(() => toast.remove(), 300)
  }, 3000)
}

/**
 * 处理搜索
 * 根据选择的类型跳转到对应的管理页面并带上keyword参数
 */
const handleSearch = () => {
  if (!searchKeyword.value.trim()) {
    showToast('请输入搜索关键词', 'warning')
    return
  }

  // 根据类型跳转到对应的管理页面
  const routeMap = {
    exam: '/manage/exam',
    mock: '/manage/mock'
  }

  router.push({
    path: routeMap[searchType.value],
    query: { keyword: searchKeyword.value.trim() }
  })
}

/**
 * 跳转到登录页
 */
const goToLogin = () => {
  router.push('/login')
}

/**
 * 跳转到注册页
 */
const goToRegister = () => {
  router.push('/register')
}

/**
 * 跳转到个人中心
 */
const goToUserCenter = () => {
  router.push('/user/center')
}

/**
 * 处理管理菜单选择
 * @param {string} command - 命令（subject/chapter/exam）
 */
const handleManageCommand = (command) => {
  if (command === 'subject') {
    router.push('/manage/subject')
  } else if (command === 'category') {
    router.push('/manage/category')
  } else if (command === 'exam') {
    router.push('/manage/exam')
  } else if (command === 'mock') {
    router.push('/manage/mock')
  } else if (command === 'image') {
    router.push('/manage/image')
  } else if (command === 'exam-category') {
    router.push('/manage/exam-category')
  }
}

/**
 * 退出登录
 */
const handleLogout = () => {
  authStore.clearAuth()
  showToast('已退出登录', 'success')
  router.push('/exam')
}
</script>

<style scoped>
/**
 * 导航栏组件样式
 */

/* 导航栏容器 */
.nav-container {
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}

/* 搜索区域 - 固定宽度防止挤压 */
.nav-search {
  flex-shrink: 0;
  width: 280px;
}

/* 导航菜单 - 自适应宽度 */
.nav-menu {
  flex: 1;
}

/* 用户区域 - 固定宽度防止挤压 */
.nav-user {
  flex-shrink: 0;
  width: 180px;
}

/* 搜索输入框容器 */
.search-input-wrapper {
  height: 42px;
}

/* 搜索输入框样式 */
.search-input-wrapper input {
  transition: all 0.3s;
}

.search-input-wrapper input:focus {
  outline: none;
}

.search-input-wrapper input::placeholder {
  color: #9ca3af;
}

/* 聚焦时展开 */
.search-input-wrapper:focus-within {
  width: 220px;
}

/* 导航链接样式 - 保留hover效果 */
.nav-link:not(.disabled):hover {
  background-color: rgba(0,0,0,0.05);
}

.nav-link.disabled {
  color: #999;
  cursor: not-allowed;
}

/* 激活状态 */
.nav-link.router-link-active:not(.disabled) {
  background-color: rgba(0,0,0,0.08);
  color: #333;
}

/* 下拉菜单触发器样式 */
.nav-link.dropdown-trigger .el-icon {
  margin-left: 6px;
  font-size: 12px;
  transition: transform 0.15s;
}

.nav-link.dropdown-trigger:hover .el-icon {
  transform: translateY(2px);
}

/* 用户名样式 - 使用Tailwind类名在template中已实现 */

/* 响应式布局 */
@media (max-width: 768px) {
  .nav-container {
    max-width: 100%;
    padding-left: 16px;
    padding-right: 16px;
    flex-wrap: wrap;
    height: auto;
    min-height: 60px;
    padding-top: 8px;
    padding-bottom: 8px;
  }

  .nav-search {
    order: 1;
    width: 100%;
    justify-content: center;
    margin-bottom: 8px;
  }

  .nav-menu {
    order: 2;
    justify-content: flex-start;
    flex: 1;
  }

  .nav-user {
    order: 3;
    justify-content: flex-end;
  }

  .search-input-wrapper {
    width: 120px;
  }

  .search-input-wrapper:focus-within {
    width: 150px;
  }

  .nav-menu {
    gap: 16px;
  }

  .nav-link {
    font-size: 14px;
    padding: 8px 16px;
  }

  .username {
    display: none;
  }

  .nav-user {
    gap: 8px;
  }
}
</style>

