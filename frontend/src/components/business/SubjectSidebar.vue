<template>
  <!-- 
    科目侧边栏组件（重构版）
    功能：展示科目列表和多级分类树
    遵循KISS原则：使用递归组件简化多级分类渲染
    遵循SOLID原则：分类树渲染逻辑委托给 CategoryTreeItem 组件
  -->
  <aside class="sidebar-container" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <transition name="fade">
        <h3 v-if="!isCollapsed">科目导航</h3>
      </transition>
      <div class="header-actions">
        <div class="collapse-all-btn" @click="collapseAll" v-if="!isCollapsed">
          <el-icon><Fold /></el-icon>
          <span>全部折叠</span>
        </div>
        <div class="toggle-btn" @click="toggleCollapse">
          <el-icon><component :is="isCollapsed ? 'Expand' : 'Fold'" /></el-icon>
        </div>
      </div>
    </div>
    
    <el-scrollbar class="sidebar-scroll">
      <div class="subject-list">
        <div
          v-for="sub in subjects"
          :key="sub.id"
          class="subject-group"
        >
          <div 
            class="subject-item"
            :class="{ 
              active: activeSubjectId === sub.id,
            }"
          >
            <div class="item-content" @click="onToggleExpand(sub)">
              <div class="icon-area">
                <el-icon class="expand-icon" :class="{ 'is-expanded': expandedSubjectId === sub.id }">
                  <CaretRight />
                </el-icon>
              </div>
              <transition name="fade">
                <span v-if="!isCollapsed" class="item-label">{{ sub.name }}</span>
              </transition>
              <transition name="fade">
                <span v-if="!isCollapsed && sub.questionCount > 0" class="count-badge">
                  {{ sub.questionCount }}
                </span>
              </transition>
            </div>
          </div>

          <!-- 多级分类树（使用递归组件） -->
          <el-collapse-transition>
            <div
              v-if="getCategoryTree(sub.id).length > 0 && !isCollapsed && expandedSubjectId === sub.id"
              class="category-list"
            >
              <!-- 旧版兼容：字符串分类 -->
              <template v-for="cat in getCategoryTree(sub.id)" :key="cat.id || cat">
                <div
                  v-if="typeof cat === 'string'"
                  class="category-item legacy-category"
                  :class="{ active: activeSubjectId === sub.id && filterCategory === cat }"
                  @click.stop="onCategorySelect(sub, cat)"
                >
                  <span class="dot-indicator"></span>
                  <span class="category-label">{{ cat }}</span>
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

<style lang="scss" scoped>
/* 侧边栏容器 */
.sidebar-container {
  width: 260px;
  height: 100%;
  background-color: $color-primary;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  z-index: 10;
  flex-shrink: 0;
  
  &.collapsed {
    width: 64px;
    
    .subject-item {
      justify-content: center;
      padding: 0;
      
      .item-content {
        justify-content: center;
      }
      
      .item-icon {
        margin-right: 0;
        font-size: 20px;
      }
    }
  }
}

.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
  flex-shrink: 0;
  gap: 8px;
  
  h3 {
    margin: 0;
    font-size: 16px;
    color: $color-text-primary;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    flex: 1;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }
  
  .collapse-all-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    color: $color-text-secondary;
    font-size: 13px;
    transition: all 0.2s;
    white-space: nowrap;
    
    .el-icon {
      font-size: 14px;
    }
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
      color: $color-accent;
    }
  }

  .toggle-btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    cursor: pointer;
    color: $color-text-secondary;
    transition: all 0.2s;
    flex-shrink: 0;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
      color: $color-primary;
    }
  }
}

.sidebar-scroll {
  flex: 1;
  padding: 12px 0;
}

.subject-list {
  padding: 0 8px;
}

.subject-group {
  margin-bottom: 4px;
}

.subject-item {
  padding: 0 8px;
  margin-bottom: 2px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  .item-content {
    display: flex;
    align-items: center;
    height: 44px;
    padding: 0 8px;
    width: 100%;
  }

  .icon-area {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    margin-right: 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }
  }
  
  .item-label {
    flex: 1;
    font-size: 15px;
    color: $color-text-primary;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .expand-icon {
    font-size: 14px;
    transition: transform 0.3s ease;
    color: $color-text-secondary;
    
    &.is-expanded {
      transform: rotate(90deg);
    }
  }

  .count-badge {
    font-size: 12px;
    color: $color-text-secondary;
    background-color: rgba(0,0,0,0.05);
    padding: 2px 6px;
    border-radius: 10px;
  }
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.03);
  }
  
  &.active {
    background-color: rgba($color-accent, 0.08);
    
    .item-label, .count-badge, .expand-icon {
      color: $color-accent;
      font-weight: 600;
    }
  }
}

/* 分类列表容器 */
.category-list {
  margin-top: 2px;
  padding: 2px 0 6px 0;
}

/* 旧版兼容：字符串分类样式 */
.category-item.legacy-category {
  display: flex;
  align-items: center;
  height: 36px;
  padding: 0 12px 0 38px;
  margin-bottom: 2px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: $color-text-regular;
  transition: all 0.2s ease;
  position: relative;
  
  .dot-indicator {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background-color: $color-text-secondary;
    margin-right: 8px;
    transition: all 0.2s;
    opacity: 0.6;
  }
  
  .category-label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.03);
    color: $color-text-primary;
    
    .dot-indicator {
      background-color: $color-text-secondary;
      transform: scale(1.2);
    }
  }
  
  &.active {
    background-color: transparent;
    color: $color-accent;
    font-weight: 500;
    
    .dot-indicator {
      background-color: $color-accent;
      transform: scale(1.5);
      opacity: 1;
    }
  }
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式布局 */
@include mobile {
  .sidebar-container {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    
    &.collapsed {
      width: 100%;
    }
    
    .sidebar-scroll {
      max-height: 300px; // Limit height on mobile
    }
  }
}
</style>
