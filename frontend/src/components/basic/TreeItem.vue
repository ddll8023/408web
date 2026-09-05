<template>
  <div class="tree-item-wrapper">
    <!-- 节点内容 -->
    <div
      class="tree-item-content group flex items-center justify-between px-3 py-2 rounded-lg transition-all duration-200"
      :class="[
        contentClasses,
        { 'is-dragging': isDragging },
        { 'is-drop-target': isDropTarget }
      ]"
      :draggable="draggable"
      role="treeitem"
      :tabindex="0"
      :aria-expanded="hasChildren ? isExpanded : undefined"
      @click.stop="handleClick"
      @keydown.enter.prevent="handleClick"
      @keydown.space.prevent="handleClick"
      @keydown.arrow-right.prevent="hasChildren && !isExpanded ? toggleExpand() : undefined"
      @keydown.arrow-left.prevent="hasChildren && isExpanded ? toggleExpand() : undefined"
      @dragstart="handleDragStart"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      @dragend="handleDragEnd"
    >
      <!-- 左侧：展开图标 + 内容 -->
      <div class="flex items-center gap-2 flex-1 min-w-0">
        <!-- 展开/折叠图标 -->
        <span
          v-if="hasChildren"
          class="expand-icon flex items-center justify-center w-5 h-5 rounded cursor-pointer text-[#8B6F47] hover:bg-[rgba(139,111,71,0.1)] transition-all duration-200"
          :class="{ 'rotate-90': isExpanded }"
          @click.stop="toggleExpand"
        >
          <font-awesome-icon :icon="['fas', 'chevron-right']" class="text-xs" />
        </span>
        <!-- 无子节点时的占位 -->
        <span v-else class="w-5 h-5"></span>

        <!-- 节点内容插槽 -->
        <slot :node="node" :level="level">
          {{ node[label] }}
        </slot>
      </div>

      <!-- 右侧：操作区域（拖拽手柄） -->
      <div
        v-if="$slots.actions"
        class="tree-actions flex items-center gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
      >
        <slot name="actions" :node="node" />
      </div>
    </div>

    <!-- 子节点列表 -->
    <div
      v-if="hasChildren && isExpanded"
      class="tree-children pl-4 border-l border-[rgba(139,111,71,0.1)] ml-2.5"
      role="group"
    >
      <TreeItem
        v-for="child in node[childrenKey]"
        :key="child[nodeKey]"
        :node="child"
        :node-key="nodeKey"
        :label="label"
        :children-key="childrenKey"
        :expanded-keys="expandedKeys"
        :level="level + 1"
        :draggable="draggable"
        :allow-drop="allowDrop"
        :allow-drag="allowDrag"
        @toggle-expand="$emit('toggle-expand', $event)"
        @dragstart="(event, node) => emit('dragstart', event, node)"
        @dragover="(event, node) => emit('dragover', event, node)"
        @drop="(event, node, type) => emit('drop', event, node, type)"
        @dragend="handleDragEnd"
      >
        <template #default="{ node: childNode, level: childLevel }">
          <slot :node="childNode" :level="childLevel" />
        </template>
        <template #actions="{ node: childNode }">
          <slot name="actions" :node="childNode" />
        </template>
      </TreeItem>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T extends TreeShape<T>">
import { computed, ref } from 'vue'
import type { TreeShape, TreeDropType, TreeDrop, AllowDrop } from './types'
/**
 * TreeItem 树节点递归组件
 * 功能：渲染单个树节点，支持展开/折叠和拖拽
 * 遵循 KISS 原则：单一职责
 */

// 定义组件名称
defineOptions({
  name: 'TreeItem'
})


const props = withDefaults(defineProps<{
  node: T; level?: number
  nodeKey?: 'id'; label?: 'name'; childrenKey?: 'children'; expandedKeys?: number[]
  draggable?: boolean; allowDrop?: AllowDrop<T>; allowDrag?: (node: T) => boolean
}>(), { level: 0, nodeKey: 'id', label: 'name', childrenKey: 'children', expandedKeys: () => [], draggable: false, allowDrop: () => true, allowDrag: () => true })
const emit = defineEmits<{ click: [node: T]; 'toggle-expand': [id: number]; dragstart: [event: DragEvent, node: T]; dragover: [event: DragEvent, node: T]; dragleave: []; drop: [event: DragEvent, node: T, type: TreeDropType] }>()
defineSlots<{ default?: (props: { node: T; level: number }) => unknown; empty?: () => unknown; actions?: (props: { node: T }) => unknown }>()

// 拖拽状态
const isDragging = ref(false)
const isDropTarget = ref(false)

// 是否有子节点
const hasChildren = computed(() => {
  return props.node[props.childrenKey] && props.node[props.childrenKey].length > 0
})

// 是否展开
const isExpanded = computed(() => {
  return props.expandedKeys.includes(props.node[props.nodeKey])
})

// 内容区域样式
const contentClasses = computed(() => {
  const classes = []

  // 禁用状态
  if (props.node.enabled === false) {
    classes.push('opacity-60')
  }

  // 拖拽中
  if (isDragging.value) {
    classes.push('bg-[rgba(139,111,71,0.1)]', 'border-2', 'border-[#8B6F47]')
  }

  // 放置目标
  if (isDropTarget.value) {
    classes.push('bg-[rgba(139,111,71,0.15)]')
  }

  return classes.join(' ')
})

// 点击事件
const handleClick = () => {
  emit('click', props.node)
}

// 切换展开/折叠
const toggleExpand = () => {
  emit('toggle-expand', props.node[props.nodeKey])
}

// 拖拽开始
const handleDragStart = (event: DragEvent) => {
  isDragging.value = true
  emit('dragstart', event, props.node)
}

// 拖拽经过
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDropTarget.value = true
  emit('dragover', event, props.node)
}

// 拖拽离开
const handleDragLeave = () => {
  isDropTarget.value = false
}

// 放置
const handleDrop = (event: DragEvent) => {
  isDropTarget.value = false

  // 计算放置类型
  if (!(event.currentTarget instanceof HTMLElement)) return
  const rect = event.currentTarget.getBoundingClientRect()
  const midY = rect.top + rect.height / 2
  let dropType: TreeDropType = 'inner'

  if (event.clientY < midY - 10) {
    dropType = 'before'
  } else if (event.clientY > midY + 10) {
    dropType = 'after'
  }

  emit('drop', event, props.node, dropType)
}

// 拖拽结束
const handleDragEnd = () => {
  isDragging.value = false
  isDropTarget.value = false
}
</script>

<style scoped>
.tree-item-wrapper {
  width: 100%;
}

.tree-item-content {
  cursor: pointer;
}

.tree-item-content:hover {
  background-color: rgba(139, 111, 71, 0.04);
}

.expand-icon {
  transition: transform 0.2s ease;
}

.expand-icon.rotate-90 {
  transform: rotate(90deg);
}

/* 拖拽时的样式 */
.is-dragging {
  opacity: 0.5;
}

/* 放置目标样式 */
.is-drop-target {
  border-top: 2px solid #8B6F47;
  border-bottom: 2px solid #8B6F47;
}

/* 子节点缩进 */
.tree-children {
  margin-top: 0.25rem;
}
</style>
