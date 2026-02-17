<template>
  <!--
    科目侧边栏组件（重构版）
    功能：展示科目列表和多级分类树
    遵循KISS原则：使用递归组件简化多级分类渲染
    遵循SOLID原则：分类树渲染逻辑委托给 CategoryTreeItem 组件
  -->
  <aside
    class="sidebar-container flex flex-col flex-shrink-0 h-full border-r border-black/5 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] bg-[#FBF7F2]"
    :class="{ 'w-16': isCollapsed, 'w-[260px]': !isCollapsed }"
  >
    <div class="sidebar-header flex items-center justify-between px-4 py-0 border-b border-black/3 flex-shrink-0 gap-2 h-14">
      <transition name="fade" mode="out-in">
        <h3 v-if="!isCollapsed" class="text-base font-semibold text-gray-900 whitespace-nowrap overflow-hidden flex-1 m-0">科目导航</h3>
      </transition>
      <div class="header-actions flex items-center gap-2 flex-shrink-0">
        <div
          class="collapse-all-btn flex items-center gap-1 px-2 py-1 rounded cursor-pointer text-gray-400 text-xs transition-all whitespace-nowrap"
          @click="collapseAll"
          v-if="!isCollapsed"
        >
          <el-icon class="text-sm"><Fold /></el-icon>
          <span>全部折叠</span>
        </div>
        <div
          class="toggle-btn w-7 h-7 flex items-center justify-center rounded cursor-pointer text-gray-400 transition-all flex-shrink-0"
          @click="toggleCollapse"
        >
          <el-icon><component :is="isCollapsed ? 'Expand' : 'Fold'" /></el-icon>
        </div>
      </div>
    </div>

    <el-scrollbar class="sidebar-scroll flex-1 py-3">
      <div class="subject-list px-2">
        <div
          v-for="sub in subjects"
          :key="sub.id"
          class="subject-group mb-1"
        >
          <div
            class="subject-item mx-0 mb-0.5 rounded-lg cursor-pointer transition-all duration-200 px-2 py-0"
            :class="{
              'active bg-[rgba(139,111,71,0.08)]': activeSubjectId === sub.id,
              'hover:bg-black/3': activeSubjectId !== sub.id
            }"
          >
            <div class="item-content flex items-center h-11 px-2 w-full" @click="onToggleExpand(sub)">
              <div class="icon-area flex items-center justify-center w-6 h-6 mr-1 rounded transition-colors duration-200">
                <el-icon
                  class="expand-icon text-sm text-gray-400 transition-transform duration-300 ease"
                  :class="{ 'rotate-90': expandedSubjectId === sub.id }"
                >
                  <CaretRight />
                </el-icon>
              </div>
              <transition name="fade" mode="out-in">
                <span v-if="!isCollapsed" class="item-label flex-1 text-base font-medium text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis">{{ sub.name }}</span>
              </transition>
              <transition name="fade" mode="out-in">
                <span v-if="!isCollapsed && sub.questionCount > 0" class="count-badge text-xs text-gray-400 bg-black/5 px-1.5 py-0.5 rounded-full ml-auto">
                  {{ sub.questionCount }}
                </span>
              </transition>
            </div>
          </div>

          <!-- 多级分类树（使用递归组件） -->
          <el-collapse-transition>
            <div
              v-if="getCategoryTree(sub.id).length > 0 && !isCollapsed && expandedSubjectId === sub.id"
              class="category-list py-0.5 px-0 mt-0.5"
            >
              <!-- 旧版兼容：字符串分类 -->
              <template v-for="cat in getCategoryTree(sub.id)" :key="cat.id || cat">
                <div
                  v-if="typeof cat === 'string'"
                  class="category-item legacy-category flex items-center h-9 px-3 py-0 mb-0.5 rounded cursor-pointer text-sm text-gray-500 relative transition-all duration-200"
                  :class="{ active: activeSubjectId === sub.id && filterCategory === cat }"
                  @click.stop="onCategorySelect(sub, cat)"
                >
                  <span class="dot-indicator w-1 h-1 rounded-full bg-gray-400 mr-2 transition-all duration-200 opacity-60"></span>
                  <span class="category-label flex-1 whitespace-nowrap overflow-hidden text-ellipsis">{{ cat }}</span>
                </div>
                <!-- 新版：使用递归组件渲染多级分类树 -->
                <CategoryTreeItem
                  v-else
                  :category="cat"
                  :level="0"
                  :active-category="activeSubjectId === sub.id ? filterCategory : ''"
                  :expanded-ids="expandedCategoryIds"
                  :base-indent="38"
                  :indent-step="14"
                  @select="(catName) => onCategorySelect(sub, catName)"
                  @toggle-expand="toggleCategoryExpand"
                />
              </template>
            </div>
          </el-collapse-transition>
        </div>
        <el-empty v-if="!loading && subjects.length === 0" description="暂无科目" :image-size="60" />
      </div>
    </el-scrollbar>
  </aside>
</template>

<script setup>
/**
 * 科目侧边栏组件
 * 功能：展示科目列表和多级分类树，支持展开/折叠和分类筛选
 * 遵循KISS原则：简洁的状态管理
 * 遵循SOLID原则：分类树渲染委托给 CategoryTreeItem 组件
 */
import { ref } from 'vue'
import { Expand, Fold, CaretRight } from '@element-plus/icons-vue'
import CategoryTreeItem from './CategoryTreeItem.vue'

// 已展开的分类ID集合（支持多级分类同时展开）
const expandedCategoryIds = ref(new Set())

const props = defineProps({
  // 侧边栏是否折叠
  isCollapsed: {
    type: Boolean,
    default: false
  },
  // 科目列表
  subjects: {
    type: Array,
    default: () => []
  },
  // 当前激活的科目ID
  activeSubjectId: {
    type: [String, Number],
    default: null
  },
  // 当前展开的科目ID
  expandedSubjectId: {
    type: [String, Number],
    default: null
  },
  // 各科目的分类数据 { subjectId: [categoryTree] }
  subjectCategories: {
    type: Object,
    default: () => ({})
  },
  // 当前筛选的分类名称
  filterCategory: {
    type: String,
    default: ''
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:isCollapsed', 'select-subject', 'toggle-expand', 'select-category'])

/**
 * 切换侧边栏折叠状态
 */
const toggleCollapse = () => {
  emit('update:isCollapsed', !props.isCollapsed)
}

/**
 * 选中科目
 */
const onSubjectSelect = (sub) => {
  emit('select-subject', sub)
}

/**
 * 切换科目展开状态
 */
const onToggleExpand = (sub) => {
  emit('toggle-expand', sub)
}

/**
 * 选中分类
 */
const onCategorySelect = (sub, cat) => {
  emit('select-category', { subject: sub, category: cat })
}

/**
 * 切换分类展开状态（支持多级分类）
 * 使用 Set 管理展开状态，允许多个分类同时展开
 */
const toggleCategoryExpand = (categoryId) => {
  const newSet = new Set(expandedCategoryIds.value)
  if (newSet.has(categoryId)) {
    newSet.delete(categoryId)
  } else {
    newSet.add(categoryId)
  }
  expandedCategoryIds.value = newSet
}

/**
 * 获取分类树（兼容旧版字符串数组和新版对象数组）
 */
const getCategoryTree = (subjectId) => {
  const cats = props.subjectCategories[subjectId]
  if (!cats || !Array.isArray(cats)) return []
  return cats
}

/**
 * 全部折叠：折叠所有展开的科目和分类
 */
const collapseAll = () => {
  // 清空所有展开的分类ID
  expandedCategoryIds.value = new Set()
  // 通知父组件折叠所有科目
  emit('toggle-expand', null)
}
</script>

<style scoped>
/* 动画效果 - 保留 transition 类用于 Vue transition 组件 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 旋转动画类 */
.rotate-90 {
  transform: rotate(90deg);
}

/* 响应式布局 - 移动端 */
@media (max-width: 768px) {
  .sidebar-container {
    width: 100% !important;
    height: auto;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }

  .sidebar-container.collapsed {
    width: 100% !important;
  }

  .sidebar-scroll {
    max-height: 300px;
  }
}
</style>
