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
      class="category-item flex items-center h-[36px] pr-3 mb-[2px] rounded-[6px] cursor-pointer text-[13px] text-gray-600 transition-all duration-200 relative hover:bg-black/5"
      :class="{
        'bg-gray-50 text-gray-900': isActive,
        'text-gray-900 font-medium': hasChildren && isExpanded,
        'text-[#8B6F47] font-medium': isActive
      }"
      :style="{ paddingLeft: `${baseIndent + level * indentStep}px` }"
      @click.stop="handleClick"
    >
      <!-- 展开/折叠图标（有子分类时显示） -->
      <span
        v-if="hasChildren"
        class="expand-icon-wrapper flex items-center justify-center w-4 h-4 mr-1 rounded-[3px] flex-shrink-0 hover:bg-black/5"
        @click.stop="toggleExpand"
      >
        <el-icon class="category-expand-icon text-[12px] transition-transform duration-300 text-gray-400" :class="{ 'rotate-90': isExpanded, 'text-[#8B6F47]': isActive || (hasChildren && isExpanded) }">
          <CaretRight />
        </el-icon>
      </span>
      <!-- 无子分类时显示圆点指示器 -->
      <span
        v-else
        class="dot-indicator w-1 h-1 rounded-full bg-gray-400 mr-2 transition-all duration-200 opacity-60 flex-shrink-0"
        :class="{ 'w-[3px] h-[3px]': level > 0, 'bg-[#8B6F47] scale-150 opacity-100': isActive }"
      ></span>

      <!-- 分类名称 -->
      <span class="category-label flex-1 truncate" :class="{ 'text-[#8B6F47]': isActive }">{{ category.name }}</span>

      <!-- 题目数量标签 -->
      <span v-if="totalCount > 0" class="category-count text-[11px] text-gray-400 bg-black/5 px-[5px] py-0.5 rounded-[8px] ml-1 flex-shrink-0">{{ totalCount }}</span>
    </div>

    <!-- 子分类列表（递归渲染） -->
    <el-collapse-transition>
      <div v-if="hasChildren && isExpanded" class="sub-category-list mt-[2px] pb-1">
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

<style scoped>
.rotate-90 {
  transform: rotate(90deg);
}
</style>
