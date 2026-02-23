<template>
  <!--
    分类树节点递归组件
    功能：递归渲染多级分类树结构
    遵循KISS原则：单一职责，仅负责分类节点的渲染和交互
    遵循SOLID原则：开闭原则，通过props配置行为
    设计风格：精致学术风 - 灵感来自古典书籍目录排版
  -->
  <div class="category-tree-item" :class="{ 'is-root': level === 0 }">
    <!-- 当前分类节点 -->
    <div
      class="category-item relative flex items-center h-9 pr-3 mb-0.5 rounded-lg cursor-pointer text-sm transition-all duration-300 ease-out"
      :class="itemClasses"
      :style="{ paddingLeft: `${baseIndent + level * indentStep}px` }"
      :tabindex="0"
      :role="hasChildren ? 'treeitem' : 'treeitem-leaf'"
      :aria-expanded="hasChildren ? isExpanded : undefined"
      :aria-selected="isActive"
      @click.stop="handleClick"
      @keydown.enter="handleClick"
      @keydown.space.prevent="toggleExpand"
      @keydown.arrow-right.prevent="hasChildren && !isExpanded && toggleExpand()"
      @keydown.arrow-left.prevent="hasChildren && isExpanded && toggleExpand()"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
    >
      <!-- 展开/折叠图标（有子分类时显示） -->
      <span
        v-if="hasChildren"
        class="expand-icon-wrapper flex shrink-0 items-center justify-center w-5 h-5 mr-1 rounded-md transition-all duration-300"
        :class="iconWrapperClasses"
        @click.stop="toggleExpand"
      >
        <svg
          class="category-expand-icon w-3.5 h-3.5 transition-transform duration-300 ease-out"
          :class="iconClasses"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      </span>

      <!-- 无子分类时显示精致圆点指示器 -->
      <span
        v-else
        class="dot-indicator flex shrink-0 mr-2 transition-all duration-300 rounded-full"
        :class="dotClasses"
      >
        <span class="dot-inner w-1.5 h-1.5 rounded-full transition-all duration-300"></span>
      </span>

      <!-- 分类图标（顶级分类显示） -->
      <span v-if="level === 0" class="category-icon mr-2 text-xs opacity-60">
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      </span>

      <!-- 分类名称 -->
      <span class="category-label flex-1 truncate" :class="labelClasses">
        {{ category.name }}
      </span>

      <!-- 题目数量标签 -->
      <transition name="count-fade">
        <span v-if="totalCount > 0" class="category-count flex shrink-0 ml-2 px-2 py-0.5 text-xs rounded-full transition-all duration-200" :class="countClasses">
          {{ totalCount }}
        </span>
      </transition>

      <!-- 激活指示器 -->
      <span v-if="isActive" class="active-indicator absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-[var(--theme-color)] rounded-r-full transition-all duration-300"></span>
    </div>

    <!-- 子分类列表（递归渲染） -->
    <Transition
      @before-enter="beforeEnter"
      @enter="enter"
      @leave="leave"
      :css="false"
    >
      <div
        v-show="hasChildren && isExpanded"
        class="sub-category-list mt-0.5 pb-1 overflow-hidden"
        :style="{ '--child-count': category.children?.length || 0 }"
        role="group"
      >
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
    </Transition>
  </div>
</template>

<script setup>
/**
 * 分类树节点递归组件
 * 支持任意深度的分类树渲染
 * 设计风格：精致学术风
 *
 * Props:
 * - category: 分类数据对象 { id, name, children?, questionCount? }
 * - level: 当前层级（0=顶级）
 * - activeCategory: 当前激活的分类名称
 * - expandedIds: 已展开的分类ID数组
 * - baseIndent: 基础缩进（px）
 * - indentStep: 每级缩进增量（px）
 *
 * Events:
 * - select: 分类被选中时触发，参数为分类名称
 * - toggle-expand: 展开/折叠状态变化时触发，参数为分类ID
 */
import { computed, ref } from 'vue'

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
  // 已展开的分类ID数组
  expandedIds: {
    type: Array,
    default: () => []
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

// 悬停状态
const isHovered = ref(false)

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
  return props.expandedIds.includes(props.category.id)
})

// 计算总题目数（包含子分类）
const totalCount = computed(() => {
  return calculateTotalCount(props.category)
})

/**
 * 动态类名计算
 */
// 节点主类名
const itemClasses = computed(() => {
  const classes = []

  if (isActive.value) {
    classes.push('bg-[rgba(139,111,71,0.08)]')
  } else if (isHovered.value) {
    classes.push('bg-black/[0.03]')
  }

  if (hasChildren.value && isExpanded.value) {
    classes.push('text-gray-900 font-medium')
  } else {
    classes.push('text-gray-600')
  }

  return classes.join(' ')
})

// 图标包装器类名
const iconWrapperClasses = computed(() => {
  if (isActive.value || (hasChildren.value && isExpanded.value)) {
    return 'bg-[rgba(139,111,71,0.1)] text-[#8B6F47]'
  }
  return 'text-gray-400 hover:bg-black/5'
})

// 图标类名
const iconClasses = computed(() => {
  if (isExpanded.value) {
    return 'rotate-90 text-[#8B6F47]'
  }
  return ''
})

// 圆点类名
const dotClasses = computed(() => {
  const base = 'dot-indicator'
  if (props.level > 0) {
    if (isActive.value) {
      return `${base} w-1 h-1 bg-[#8B6F47] opacity-100 scale-125`
    }
    return `${base} w-1 h-1 bg-gray-400 opacity-50`
  }
  if (isActive.value) {
    return `${base} w-1.5 h-1.5 bg-[#8B6F47] opacity-100 scale-110`
  }
  return `${base} w-1.5 h-1.5 bg-gray-400 opacity-60`
})

// 标签类名
const labelClasses = computed(() => {
  if (isActive.value) {
    return 'text-[#8B6F47] font-medium'
  }
  return ''
})

// 数量标签类名
const countClasses = computed(() => {
  if (isActive.value) {
    return 'bg-[rgba(139,111,71,0.15)] text-[#8B6F47]'
  }
  return 'bg-black/5 text-gray-400'
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
  if (hasChildren.value) {
    emit('toggle-expand', props.category.id)
  }
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

/**
 * 动画钩子 - 展开时
 */
const beforeEnter = (el) => {
  el.style.height = '0'
  el.style.opacity = '0'
  el.style.transform = 'translateY(-8px)'
}

const enter = (el, done) => {
  const childCount = el.style.getPropertyValue('--child-count') || 1
  const duration = Math.min(200 + childCount * 30, 400)

  el.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`
  el.style.height = `${el.scrollHeight}px`
  el.style.opacity = '1'
  el.style.transform = 'translateY(0)'

  setTimeout(done, duration)
}

const leave = (el, done) => {
  const duration = Math.min(150 + el.scrollHeight * 0.3, 300)

  el.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`
  el.style.height = '0'
  el.style.opacity = '0'
  el.style.transform = 'translateY(-8px)'

  setTimeout(done, duration)
}
</script>

<style scoped>
/* 主题色变量 */
.category-tree-item {
  --theme-color: #8B6F47;
  --theme-color-light: rgba(139, 111, 71, 0.08);
  --theme-color-lighter: rgba(139, 111, 71, 0.15);
}

/* 根节点特殊样式 */
.category-tree-item.is-root > .category-item {
  font-weight: 500;
}

/* 激活状态文字色 - 通过CSS类处理 */
.category-item:focus {
  outline: none;
}

.category-item:focus-visible {
  outline: 2px solid var(--theme-color);
  outline-offset: 2px;
}

/* 圆点内部元素动画 */
.dot-inner {
  display: block;
}

/* 激活时圆点放大效果 */
.dot-indicator.active .dot-inner {
  transform: scale(1.2);
}

/* 数量标签淡入淡出 */
.count-fade-enter-active,
.count-fade-leave-active {
  transition: all 0.2s ease;
}

.count-fade-enter-from,
.count-fade-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 旋转动画 */
.rotate-90 {
  transform: rotate(90deg);
}

/* 根节点缩进线效果 */
.category-tree-item.is-root::before {
  content: '';
  position: absolute;
  left: calc(var(--base-indent, 12px) - 8px);
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(
    to bottom,
    transparent,
    rgba(139, 111, 71, 0.15) 10%,
    rgba(139, 111, 71, 0.15) 90%,
    transparent
  );
}
</style>
