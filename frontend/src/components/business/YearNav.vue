<!-- 年份导航侧栏：桌面端展示年份列表，窄屏由目录抽屉替代。 -->
<template>
  <div
    class="year-nav-container w-[280px] h-full bg-surface border-r border-black/[0.05] flex flex-col transition-all duration-300 flex-shrink-0 z-10"
    :class="{ collapsed: isCollapsed }"
    role="navigation"
    aria-label="年份导航"
  >
    <!-- 顶部标题栏 -->
    <div class="year-nav-header h-14 flex items-center justify-between px-4 border-b border-black/[0.05] flex-shrink-0 gap-2">
      <button
        type="button"
        class="toggle-btn w-8 h-8 flex items-center justify-center rounded-md border-0 bg-transparent cursor-pointer text-accent transition-all duration-200 flex-shrink-0 hover:bg-black/[0.05]"
        :aria-label="isCollapsed ? '展开年份导航' : '折叠年份导航'"
        @click="toggleCollapse"
      >
        <font-awesome-icon :icon="['fas', isCollapsed ? 'angle-right' : 'angle-left']" class="text-lg" aria-hidden="true" />
      </button>
      <transition name="fade">
        <span v-if="!isCollapsed" class="header-title font-semibold text-base text-accent whitespace-nowrap overflow-hidden flex-1">年份导航</span>
      </transition>
    </div>

    <!-- 年份列表 -->
    <div v-show="!isCollapsed" class="year-list-scroll scrollbar-stable flex-1 overflow-y-auto px-2 py-3">
      <YearNavList
        :year-list="yearList"
        :active-year="activeYear"
        :loading="loading"
        @year-select="(year) => emit('year-select', year)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 年份导航侧栏
 * 桌面端外壳：标题栏、折叠交互和滚动容器；年份列表渲染交给 YearNavList，
 * 使窄屏目录抽屉可以复用同一份数据和选中状态
 */
import type { PropType } from 'vue'
import type { ExamNavYear } from '@/types'
import { ref } from 'vue'
import YearNavList from './YearNavList.vue'

defineProps({
  // 年份数据，按年份从新到旧排列
  yearList: {
    type: Array as PropType<ExamNavYear[]>,
    default: () => []
  },
  // 当前激活的年份
  activeYear: {
    type: Number as PropType<number | null>,
    default: null
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  'year-select': [year: number]
  'collapse-change': [collapsed: boolean]
}>()

// 导航栏是否折叠
const isCollapsed = ref(false)

/**
 * 切换导航栏折叠状态
 */
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('collapse-change', isCollapsed.value)
}
</script>

<style scoped>
/**
 * 年份导航栏组件样式
 * 使用纯CSS样式，兼容Tailwind CSS 4
 */

.year-nav-container.collapsed {
  width: 56px;
}

.year-nav-container.collapsed .year-nav-header {
  justify-content: center;
  padding: 0;
}

.year-nav-container.collapsed .year-nav-header .toggle-btn {
  margin: 0;
}

/* 年份列表滚动容器：预留滚动条槽位，展开年份时不改变内容可用宽度 */
.year-list-scroll {
  scrollbar-gutter: stable;
}

.year-list-scroll::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.year-list-scroll::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.year-list-scroll::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

.year-list-scroll::-webkit-scrollbar-track {
  background-color: transparent;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 移动端改用顶部导航入口 + 底部目录抽屉，侧栏整体隐藏 */
@media (max-width: 767px) {
  .year-nav-container {
    display: none;
  }
}
</style>
