<template>
  <nav class="navigation fixed top-0 left-0 right-0 h-[60px] px-8 bg-[rgba(251,247,242,0.85)] backdrop-blur-md border-b border-black/[0.08] shadow-[0_2px_8px_rgba(0,0,0,0.1)] z-[1000]">
    <div class="nav-container h-full flex items-center justify-between px-8">
      <!-- 搜索区域 - 靠左 -->
      <div class="nav-search flex items-center justify-start relative bg-transparent">
        <el-select
          v-model="searchType"
          class="search-type-select w-[90px]"
          placeholder="类型"
        >
          <el-option label="真题" value="exam" />
          <el-option label="模拟题" value="mock" />
        </el-select>
        <span class="search-divider w-px h-5 bg-black/[0.12] mx-2"></span>
        <el-input
          v-model="searchKeyword"
          class="search-input w-[180px] transition-all duration-300"
          placeholder="搜索题目..."
          clearable
          @keyup.enter="handleSearch"
        >
          <template #suffix>
            <el-icon class="search-icon text-gray-400 text-sm p-1.5 rounded-full transition-all duration-200 cursor-pointer hover:text-[#8B6F47] hover:bg-[rgba(139,111,71,0.1)] hover:scale-110 active:scale-95" @click="handleSearch"><Search /></el-icon>
          </template>
        </el-input>
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
        <el-dropdown v-if="authStore.isAdmin()" @command="handleManageCommand" trigger="hover">
          <span class="nav-link dropdown-trigger inline-flex items-center cursor-pointer select-none text-gray-800 no-underline text-base px-6 py-2.5 rounded transition-all duration-300">
            管理
            <el-icon class="el-icon--right ml-1.5 text-xs transition-transform duration-150"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="subject">科目管理</el-dropdown-item>
              <el-dropdown-item command="category">分类标签管理</el-dropdown-item>
              <el-dropdown-item command="exam">真题管理</el-dropdown-item>
              <el-dropdown-item command="mock">模拟题管理</el-dropdown-item>
              <el-dropdown-item command="image">图片管理</el-dropdown-item>
              <el-dropdown-item command="exam-category">分类统计</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
 * 
 * Source: Element Plus Dropdown 组件
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import CustomButton from '@/components/basic/CustomButton.vue'
import { ArrowDown, Search } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

// 搜索相关状态
const searchType = ref('exam')  // 默认搜索真题
const searchKeyword = ref('')

/**
 * 处理搜索
 * 根据选择的类型跳转到对应的管理页面并带上keyword参数
 */
const handleSearch = () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
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
  ElMessage.success('已退出登录')
  router.push('/exam')
}
</script>

<style scoped>
/**
 * 导航栏组件样式
 * 使用@apply提取公共样式，符合前端规范
 */

/* 导航栏容器 - 使用@apply提取 */
.nav-container {
  @apply max-w-[1400px] mx-auto;
}

/* 搜索区域 - 固定宽度防止挤压 */
.nav-search {
  @apply flex-shrink-0 w-[280px];
}

/* 导航菜单 - 自适应宽度 */
.nav-menu {
  @apply flex-1;
}

/* 用户区域 - 固定宽度防止挤压 */
.nav-user {
  @apply flex-shrink-0 w-[180px];
}

/* 搜索相关样式 - 需要保留的自定义样式 */
.nav-search .search-type-select :deep(.el-input__wrapper) {
  border: none;
  box-shadow: none;
  background: transparent;
  padding-left: 0;
}

.nav-search .search-type-select :deep(.el-input__inner) {
  font-size: 14px;
  color: #666;
}

.nav-search .search-type-select :deep(.el-input__inner)::placeholder {
  color: #999;
}

.nav-search .search-type-select :deep(.el-input__suffix) {
  color: #999;
}

.nav-search .search-type-select :deep(.el-select__caret) {
  color: #999;
  transition: all 0.15s;
}

.nav-search .search-type-select:hover :deep(.el-select__caret) {
  color: #8B6F47;
}

/* 输入框样式 */
.search-input :deep(.el-input__wrapper) {
  border: none;
  box-shadow: none;
  background: transparent;
  padding-right: 4px;
}

.search-input :deep(.el-input__inner) {
  font-size: 14px;
  color: #333;
}

.search-input :deep(.el-input__inner)::placeholder {
  color: #999;
  transition: all 0.15s;
}

/* 聚焦时展开 - 使用CSS类 */
.search-input:focus-within {
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

  .search-input {
    width: 120px;
  }

  .search-input:focus-within {
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

