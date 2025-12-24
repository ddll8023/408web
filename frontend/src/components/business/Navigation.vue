<template>
  <nav class="navigation">
    <div class="nav-container">
      <!-- 搜索区域 - 靠左 -->
      <div class="nav-search">
        <el-select 
          v-model="searchType" 
          class="search-type-select"
          placeholder="类型"
        >
          <el-option label="真题" value="exam" />
          <el-option label="模拟题" value="mock" />
        </el-select>
        <span class="search-divider"></span>
        <el-input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索题目..."
          clearable
          @keyup.enter="handleSearch"
        >
          <template #suffix>
            <el-icon class="search-icon" @click="handleSearch"><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 导航菜单 -->
      <div class="nav-menu">
        <!-- 真题首页 - 独立导航 -->
        <span class="nav-link" @click="router.push('/exam')">真题首页</span>
        
        <!-- 真题分类 - 独立导航 -->
        <span class="nav-link" @click="router.push('/exam/classify')">真题分类</span>
        
        <!-- 模拟题 - 独立导航 -->
        <span class="nav-link" @click="router.push('/mock')">模拟题</span>
        
        <!-- 预留未来功能入口 -->
        <span class="nav-link disabled">资源</span>
        
        <!-- 管理菜单（仅ADMIN可见） -->
        <el-dropdown v-if="authStore.isAdmin()" @command="handleManageCommand" trigger="hover">
          <span class="nav-link dropdown-trigger">
            管理
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
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
      <div class="nav-user">
        <template v-if="authStore.isLoggedIn()">
          <span class="username" @click="goToUserCenter">{{ authStore.userInfo?.username }}</span>
          <CustomButton size="small" @click="handleLogout">退出</CustomButton>
        </template>
        <template v-else>
          <CustomButton size="small" @click="goToLogin">登录</CustomButton>
          <CustomButton size="small" type="primary" @click="goToRegister">注册</CustomButton>
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

<style lang="scss" scoped>
/**
 * 导航栏组件样式
 * 使用Sass变量和mixins统一管理主题
 * 注：变量和mixins已通过Vite全局注入，无需手动导入
 */

/* 导航栏容器 */
.navigation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: $nav-height;
  // 毛玻璃效果：使用主色调半透明背景 + 背景模糊
  background: rgba(251, 247, 242, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px); // Safari 浏览器兼容
  // 微妙的底部边框，增强层次感
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: $box-shadow-base;
  z-index: $z-index-nav;
}

/* 导航内容容器 */
.nav-container {
  max-width: $container-width-xl;
  height: 100%;
  margin: 0 auto;
  padding: 0 $spacing-lg;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 搜索区域 - 靠左 */
.nav-search {
  display: flex;
  align-items: center;
  position: relative;
  background: transparent;
  flex-shrink: 0; // 防止被压缩
  
  .search-type-select {
    width: 90px;
    
    :deep(.el-input__wrapper) {
      border: none;
      box-shadow: none !important;
      background: transparent;
      padding-left: 0;
      
      .el-input__inner {
        color: $color-text-regular;
        font-size: $font-size-base;
        
        &::placeholder {
          color: $color-text-secondary;
        }
      }
      
      .el-input__suffix {
        color: $color-text-secondary;
      }
    }
    
    :deep(.el-select__caret) {
      color: $color-text-secondary;
      transition: $transition-fast;
    }
    
    &:hover :deep(.el-select__caret) {
      color: $color-accent;
    }
  }
  
  // 分隔线
  .search-divider {
    width: 1px;
    height: 20px;
    background: rgba(0, 0, 0, 0.12);
    margin: 0 $spacing-xs;
  }
  
  .search-input {
    width: 180px;
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    :deep(.el-input__wrapper) {
      border: none;
      box-shadow: none !important;
      background: transparent;
      padding-right: 4px;
      
      .el-input__inner {
        color: $color-text-primary;
        font-size: $font-size-base;
        
        &::placeholder {
          color: $color-text-secondary;
          transition: $transition-fast;
        }
      }
    }
    
    // 聚焦时展开
    &:focus-within {
      width: 220px;
    }
  }
  
  .search-icon {
    cursor: pointer;
    color: $color-text-secondary;
    font-size: 16px;
    padding: 6px;
    border-radius: 50%;
    transition: all 0.2s ease;
    
    &:hover {
      color: $color-accent;
      background: $color-accent-light;
      transform: scale(1.1);
    }
    
    &:active {
      transform: scale(0.95);
    }
  }
}

/* 导航菜单 - 居中 */
.nav-menu {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-lg;
  flex: 1; // 占据中间空间实现居中
}

/* 导航链接 */
.nav-link {
  color: $color-text-primary;
  text-decoration: none;
  font-size: $font-size-medium;
  padding: $spacing-xs + 2px $spacing-md; // 增加内边距
  border-radius: $border-radius-base;
  transition: $transition-base;
  cursor: pointer;
  @include no-select;
  
  &:not(.disabled):hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  &.disabled {
    color: $color-disabled;
    cursor: not-allowed;
  }
  
  /* 激活状态 */
  &.router-link-active:not(.disabled) {
    background-color: rgba(0, 0, 0, 0.08);
    color: $color-text-primary;
  }
  
  /* 下拉菜单触发器样式 */
  &.dropdown-trigger {
    display: inline-flex;
    align-items: center;
    cursor: pointer;
    @include no-select;
    
    .el-icon {
      margin-left: 6px; // 增加图标间距
      font-size: 12px;
      transition: transform $transition-fast;
    }
    
    &:hover .el-icon {
      transform: translateY(1px);
    }
  }
}

/* 用户信息区域 - 靠右 */
.nav-user {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-shrink: 0; // 防止被压缩
}

.username {
  color: $color-text-primary;
  font-size: $font-size-base;
  cursor: pointer;
  padding: $spacing-xs $spacing-sm; // 增加内边距
  margin-right: $spacing-xs; // 与按钮保持间距
  border-radius: $border-radius-base;
  transition: $transition-base;
  @include no-select;
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
    color: $color-accent;
  }
}

/* 响应式布局 */
@include mobile {
  .nav-container {
    padding: 0 $spacing-sm;
  }

  .nav-search {
    margin: 0 $spacing-sm;
    
    .search-input {
      width: 120px;
      
      &:focus-within {
        width: 150px;
      }
    }
  }

  .nav-menu {
    gap: $spacing-sm;
  }

  .nav-link {
    font-size: $font-size-base;
    padding: $spacing-xs $spacing-sm;
  }

  .username {
    display: none;
  }
  
  .nav-user {
    gap: $spacing-xs;
  }
}
</style>

