<template>
  <!-- 
    分类树节点递归组件
    功能：递归渲染多级分类树结构
    遵循KISS原则：单一职责，仅负责分类节点的渲染和交互
    遵循SOLID原则：开闭原则，通过props配置行为
  -->
  <div class="category-tree-item">
    <!-- 当前分类节点 -->
    <div
      class="category-item"
      :class="{ 
        active: isActive,
        expanded: isExpanded,
        'has-children': hasChildren
      }"
      :style="{ paddingLeft: `${baseIndent + level * indentStep}px` }"
      @click.stop="handleClick"
    >
      <!-- 展开/折叠图标（有子分类时显示） -->
      <span 
        v-if="hasChildren"
        class="expand-icon-wrapper"
        @click.stop="toggleExpand"
      >
        <el-icon class="category-expand-icon" :class="{ 'is-expanded': isExpanded }">
          <CaretRight />
        </el-icon>
      </span>
      <!-- 无子分类时显示圆点指示器 -->
      <span v-else class="dot-indicator" :class="{ small: level > 0 }"></span>
      
      <!-- 分类名称 -->
      <span class="category-label">{{ category.name }}</span>
      
      <!-- 题目数量标签 -->
      <span v-if="totalCount > 0" class="category-count">{{ totalCount }}</span>
    </div>

    <!-- 子分类列表（递归渲染） -->
    <el-collapse-transition>
      <div v-if="hasChildren && isExpanded" class="sub-category-list">
        <CategoryTreeItem
          v-for="child in category.children"
          :key="child.id"
          :category="child"
          :level="level + 1"
          :active-category="activeCategory"
          :expanded-ids="expandedIds"
          :base-indent="baseIndent"
          :indent-step="indentStep"
          @select="handleChildSelect"
          @toggle-expand="handleChildToggleExpand"
        />
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup>
/**
 * 分类树节点递归组件
 * 支持任意深度的分类树渲染
 * 
 * Props:
 * - category: 分类数据对象 { id, name, children?, questionCount? }
 * - level: 当前层级（0=顶级）
 * - activeCategory: 当前激活的分类名称
 * - expandedIds: 已展开的分类ID集合
 * - baseIndent: 基础缩进（px）
 * - indentStep: 每级缩进增量（px）
 * 
 * Events:
 * - select: 分类被选中时触发，参数为分类名称
 * - toggle-expand: 展开/折叠状态变化时触发，参数为分类ID
 */
import { computed } from 'vue'
import { CaretRight } from '@element-plus/icons-vue'

const props = defineProps({
  // 分类数据
  category: {
    type: Object,
    required: true
  },
  // 当前层级（0=顶级分类）
  level: {
    type: Number,
    default: 0
  },
  // 当前激活的分类名称
  activeCategory: {
    type: String,
    default: ''
  },
  // 已展开的分类ID集合
  expandedIds: {
    type: Set,
    default: () => new Set()
  },
  // 基础缩进（px）
  baseIndent: {
    type: Number,
    default: 12
  },
  // 每级缩进增量（px）
  indentStep: {
    type: Number,
    default: 16
  }
})

const emit = defineEmits(['select', 'toggle-expand'])

// 是否有子分类
const hasChildren = computed(() => {
  return props.category.children && props.category.children.length > 0
})

// 是否为激活状态
const isActive = computed(() => {
  return props.activeCategory === props.category.name
})

// 是否为展开状态
const isExpanded = computed(() => {
  return props.expandedIds.has(props.category.id)
})

// 计算总题目数（包含子分类）
const totalCount = computed(() => {
  return calculateTotalCount(props.category)
})

/**
 * 递归计算分类的总题目数（包含所有子分类）
 */
function calculateTotalCount(cat) {
  if (!cat || typeof cat !== 'object') return 0
  
  let total = cat.questionCount || 0
  if (cat.children && Array.isArray(cat.children)) {
    cat.children.forEach(child => {
      total += calculateTotalCount(child)
    })
  }
  return total
}

/**
 * 处理分类点击（选中分类）
 */
const handleClick = () => {
  emit('select', props.category.name)
}

/**
 * 切换展开/折叠状态
 */
const toggleExpand = () => {
  emit('toggle-expand', props.category.id)
}

/**
 * 处理子分类选中事件（向上冒泡）
 */
const handleChildSelect = (categoryName) => {
  emit('select', categoryName)
}

/**
 * 处理子分类展开/折叠事件（向上冒泡）
 */
const handleChildToggleExpand = (categoryId) => {
  emit('toggle-expand', categoryId)
}
</script>

<style lang="scss" scoped>
/* 分类树节点容器 - 作为递归结构的包装 */
.category-tree-item {
  width: 100%;
}

.category-item {
  display: flex;
  align-items: center;
  height: 36px;
  padding-right: 12px;
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
    flex-shrink: 0;
    
    &.small {
      width: 3px;
      height: 3px;
    }
  }
  
  .expand-icon-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    margin-right: 4px;
    border-radius: 3px;
    flex-shrink: 0;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.08);
    }
  }
  
  .category-expand-icon {
    font-size: 12px;
    transition: transform 0.3s ease;
    color: $color-text-secondary;
    
    &.is-expanded {
      transform: rotate(90deg);
    }
  }
  
  .category-label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .category-count {
    font-size: 11px;
    color: $color-text-secondary;
    background-color: rgba(0, 0, 0, 0.04);
    padding: 1px 5px;
    border-radius: 8px;
    margin-left: 4px;
    flex-shrink: 0;
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
    
    .category-expand-icon {
      color: $color-accent;
    }
  }
  
  // 有子分类的父分类样式
  &.has-children {
    font-weight: 500;
    
    &.expanded {
      color: $color-text-primary;
      
      .category-expand-icon {
        color: $color-accent;
      }
    }
  }
}

// 子分类列表容器
.sub-category-list {
  margin-top: 2px;
  padding-bottom: 4px;
}
</style>
