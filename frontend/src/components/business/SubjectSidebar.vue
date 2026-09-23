<!-- 科目分类侧栏：桌面端展示科目与分类树，移动端由目录抽屉替代。 -->
<template>
  <aside
    class="sidebar-container flex flex-col flex-shrink-0 h-full border-r border-black/5 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] bg-surface"
    aria-label="科目导航"
    :class="{ 'w-16': isCollapsed, 'w-[260px]': !isCollapsed }"
  >
    <div class="sidebar-header flex items-center justify-between px-4 py-0 border-b border-black/3 flex-shrink-0 gap-2 h-14">
      <transition name="fade" mode="out-in">
        <span v-if="!isCollapsed" class="text-base font-semibold text-gray-900 whitespace-nowrap overflow-hidden flex-1 m-0">科目导航</span>
      </transition>
      <div class="header-actions flex items-center gap-2 flex-shrink-0">
        <button
          v-if="!isCollapsed"
          class="collapse-all-btn flex items-center gap-1 rounded border-0 bg-transparent px-2 py-1 cursor-pointer text-gray-400 text-xs transition-all whitespace-nowrap"
          type="button"
          aria-label="全部折叠科目分类"
          @click="collapseAll"
        >
          <font-awesome-icon :icon="['fas', 'chevron-down']" class="text-sm" aria-hidden="true" />
          <span>全部折叠</span>
        </button>
        <button
          class="toggle-btn w-7 h-7 flex items-center justify-center rounded border-0 bg-transparent cursor-pointer text-gray-400 transition-all flex-shrink-0"
          type="button"
          :aria-label="isCollapsed ? '展开科目导航' : '折叠科目导航'"
          @click="toggleCollapse"
        >
          <font-awesome-icon :icon="['fas', isCollapsed ? 'angle-right' : 'angle-left']" aria-hidden="true" />
        </button>
      </div>
    </div>

    <div class="sidebar-scroll scrollbar-stable flex-1 py-3 overflow-y-auto custom-scrollbar">
      <SubjectNavList
        :subjects="subjects"
        :subject-categories="subjectCategories"
        :active-subject-id="activeSubjectId"
        :expanded-subject-id="expandedSubjectId"
        :filter-category="filterCategory"
        :expanded-ids="expandedIds"
        :loading="loading"
        :collapsed="isCollapsed"
        @update:expanded-ids="(ids) => emit('update:expandedIds', ids)"
        @select-subject="(subject) => emit('select-subject', subject)"
        @toggle-expand="(subject) => emit('toggle-expand', subject)"
        @select-category="(selection) => emit('select-category', selection)"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
/**
 * 科目分类侧栏
 * 桌面端外壳：标题栏、折叠交互和滚动容器；列表渲染与分类展开状态交给 SubjectNavList，
 * 使移动端目录抽屉可以复用同一份数据和展开状态
 */
import type { PropType } from 'vue'
import type { CategoryTreeNode, Subject } from '@/types'
import SubjectNavList from './SubjectNavList.vue'

const props = defineProps({
  // 侧边栏是否折叠
  isCollapsed: {
    type: Boolean,
    default: false
  },
  // 科目列表
  subjects: {
    type: Array as PropType<Subject[]>,
    default: () => []
  },
  // 当前激活的科目 ID
  activeSubjectId: {
    type: [String, Number] as PropType<string | number | null>,
    default: null
  },
  // 当前展开的科目 ID
  expandedSubjectId: {
    type: [String, Number] as PropType<string | number | null>,
    default: null
  },
  // 各科目的分类数据 { subjectId: [categoryTree] }
  subjectCategories: {
    type: Object as PropType<Record<number, CategoryTreeNode[]>>,
    default: () => ({})
  },
  // 当前筛选的分类名称
  filterCategory: {
    type: String,
    default: ''
  },
  // 已展开的分类 ID
  expandedIds: {
    type: Array as PropType<number[]>,
    default: () => []
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  'update:isCollapsed': [value: boolean]
  'update:expandedIds': [ids: number[]]
  'select-subject': [subject: Subject]
  'toggle-expand': [subject: Subject | null]
  'select-category': [selection: { subject: Subject; category: string }]
}>()

/**
 * 切换侧边栏折叠状态
 */
const toggleCollapse = () => {
  emit('update:isCollapsed', !props.isCollapsed)
}

/**
 * 全部折叠：折叠所有科目并收起已展开的分类，由父组件同步状态
 */
const collapseAll = () => {
  emit('update:expandedIds', [])
  emit('toggle-expand', null)
}
</script>

<style scoped>
/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 自定义滚动条：预留滚动条槽位，展开分类时不改变内容可用宽度 */
.sidebar-scroll {
  scrollbar-gutter: stable;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.2);
}

/* 移动端改用顶部导航入口 + 底部目录抽屉，侧栏整体隐藏 */
@media (max-width: 767px) {
  .sidebar-container {
    display: none;
  }
}
</style>
