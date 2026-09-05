<template>
  <div class="tree-container" role="tree">
    <!-- 树形节点列表 -->
    <div
      v-for="node in normalizedData"
      :key="node[nodeKey]"
      class="tree-node-wrapper"
    >
      <TreeItem
        :node="node"
        :node-key="nodeKey"
        :label="label"
        :children-key="childrenKey"
        :expanded-keys="expandedKeys"
        :draggable="draggable"
        :allow-drop="allowDrop"
        :allow-drag="allowDrag"
        @toggle-expand="handleToggleExpand"
        @dragstart="onDragStart"
        @dragover="onDragOver"
        @drop="onDrop"
      >
        <!-- 自定义节点内容 -->
        <template #default="{ node: item, level }">
          <slot :node="item" :level="level">
            <span>{{ item[label] }}</span>
          </slot>
        </template>
        <template #actions="{ node: item }">
          <slot name="actions" :node="item" />
        </template>
      </TreeItem>
    </div>

    <!-- 空状态 -->
    <div v-if="normalizedData.length === 0" class="text-center py-8 text-gray-400">
      <slot name="empty">
        <span>暂无数据</span>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T extends TreeShape<T>">
import type { TreeShape, TreeDropType, TreeDrop, AllowDrop } from './types'
/**
 * Tree 树形组件
 * 功能：提供支持拖拽排序和自定义节点内容的树
 * 遵循 KISS 原则：简洁实现
 * 遵循 YAGNI 原则：只实现实际使用的功能
 */
import { computed } from 'vue'
import TreeItem from './TreeItem.vue'

const props = withDefaults(defineProps<{
  data?: T[]
  nodeKey?: 'id'; label?: 'name'; childrenKey?: 'children'; expandedKeys?: number[]
  draggable?: boolean; allowDrop?: AllowDrop<T>; allowDrag?: (node: T) => boolean
}>(), { data: () => [], nodeKey: 'id', label: 'name', childrenKey: 'children', expandedKeys: () => [], draggable: false, allowDrop: () => true, allowDrag: () => true })
const emit = defineEmits<{ 'update:expandedKeys': [keys: number[]]; 'node-expand': [node: { id: number }]; 'node-collapse': [node: { id: number }]; 'node-drop': [drop: TreeDrop<T>] }>()
defineSlots<{ default?: (props: { node: T; level: number }) => unknown; empty?: () => unknown; actions?: (props: { node: T }) => unknown }>()

// 规范化数据
const normalizedData = computed(() => {
  return props.data || []
})

// 节点key
const nodeKey = computed(() => props.nodeKey)
const label = computed(() => props.label)
const childrenKey = computed(() => props.childrenKey)

// 处理展开/折叠
const handleToggleExpand = (nodeId: number) => {
  const keys = [...props.expandedKeys]
  const index = keys.indexOf(nodeId)

  if (index > -1) {
    // 收起
    keys.splice(index, 1)
    emit('node-collapse', { id: nodeId })
  } else {
    // 展开
    keys.push(nodeId)
    emit('node-expand', { id: nodeId })
  }

  emit('update:expandedKeys', keys)
}

// 拖拽开始
const handleDragStart = (event: DragEvent, node: T) => {
  if (!props.allowDrag(node)) {
    event.preventDefault()
    return
  }
  if (!event.dataTransfer) return
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('nodeId', String(node[props.nodeKey]))
}

// 拖拽经过
const handleDragOver = (event: DragEvent, node: T) => {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
}

// 放置
const handleDrop = (event: DragEvent, targetNode: T, dropType: TreeDropType) => {
  event.preventDefault()

  if (!event.dataTransfer) return
  const draggingNodeId = parseInt(event.dataTransfer.getData('nodeId'))
  const targetNodeId = targetNode[props.nodeKey]

  // 调用放置规则
  const draggingNode = findNodeById(props.data, draggingNodeId)
  if (!draggingNode) return

  const canDrop = props.allowDrop({ data: draggingNode }, { data: targetNode }, dropType)
  if (!canDrop) return

  // 触发 drop 事件
  emit('node-drop', {
    draggingNode,
    targetNode,
    dropType
  })
}

// 根据ID查找节点
const findNodeById = (nodes: T[], id: number): T | null => {
  for (const node of nodes) {
    if (node[props.nodeKey] === id) {
      return node
    }
    if (node[props.childrenKey] && node[props.childrenKey].length > 0) {
      const found = findNodeById(node[props.childrenKey], id)
      if (found) return found
    }
  }
  return null
}

// 拖拽事件包装函数（解决模板中箭头函数参数作用域问题）
const onDragStart = (event: DragEvent, node: T) => handleDragStart(event, node)
const onDragOver = (event: DragEvent, node: T) => handleDragOver(event, node)
const onDrop = (event: DragEvent, node: T, dropType: TreeDropType) => handleDrop(event, node, dropType)
</script>

<style scoped>
.tree-container {
  width: 100%;
}

.tree-node-wrapper {
  width: 100%;
}
</style>
