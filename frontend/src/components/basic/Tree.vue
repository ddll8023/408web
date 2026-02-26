<template>
  <div class="tree-container">
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

<script setup>
/**
 * Tree 树形组件
 * 功能：替代 Element Plus 的 el-tree，支持拖拽排序和自定义节点内容
 * 遵循 KISS 原则：简洁实现
 * 遵循 YAGNI 原则：只实现实际使用的功能
 */
import { computed } from 'vue'
import TreeItem from './TreeItem.vue'

const props = defineProps({
  // 树形数据
  data: {
    type: Array,
    default: () => []
  },
  // 节点唯一标识字段
  nodeKey: {
    type: String,
    default: 'id'
  },
  // 显示字段
  label: {
    type: String,
    default: 'name'
  },
  // 子节点字段
  childrenKey: {
    type: String,
    default: 'children'
  },
  // 已展开的节点ID数组
  expandedKeys: {
    type: Array,
    default: () => []
  },
  // 是否可拖拽
  draggable: {
    type: Boolean,
    default: false
  },
  // 放置规则函数
  allowDrop: {
    type: Function,
    default: () => true
  },
  // 拖拽规则函数
  allowDrag: {
    type: Function,
    default: () => true
  }
})

const emit = defineEmits(['update:expandedKeys', 'node-expand', 'node-collapse', 'node-drop'])

// 规范化数据
const normalizedData = computed(() => {
  return props.data || []
})

// 节点key
const nodeKey = computed(() => props.nodeKey)
const label = computed(() => props.label)
const childrenKey = computed(() => props.childrenKey)

// 处理展开/折叠
const handleToggleExpand = (nodeId) => {
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
const handleDragStart = (event, node) => {
  if (!props.allowDrag(node)) {
    event.preventDefault()
    return
  }
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('nodeId', node[props.nodeKey])
}

// 拖拽经过
const handleDragOver = (event, node) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

// 放置
const handleDrop = (event, targetNode, dropType) => {
  event.preventDefault()

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
const findNodeById = (nodes, id) => {
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
const onDragStart = (event, node) => handleDragStart(event, node)
const onDragOver = (event, node) => handleDragOver(event, node)
const onDrop = (event, node, dropType) => handleDrop(event, node, dropType)
</script>

<style scoped>
.tree-container {
  width: 100%;
}

.tree-node-wrapper {
  width: 100%;
}
</style>
