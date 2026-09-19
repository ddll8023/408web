<!-- 出题工作台章节树：按科目章节层级展示题目范围和已选数量。 -->
<template>
  <div class="question-chapter-tree" :role="level === 0 ? 'tree' : 'group'">
    <div
      v-for="node in nodes"
      :key="node.id"
      class="question-chapter-tree__node"
    >
      <div
        class="question-chapter-tree__item"
        :class="{
          'question-chapter-tree__item--active': activeId === node.id,
          'question-chapter-tree__item--root': level === 0,
        }"
        :style="{ paddingLeft: `${12 + level * 18}px` }"
        role="treeitem"
        :aria-level="level + 1"
        :aria-expanded="hasChildren(node) ? isExpanded(node.id) : undefined"
        :aria-selected="activeId === node.id"
        tabindex="0"
        @click="emit('select', node)"
        @keydown.enter.prevent="emit('select', node)"
        @keydown.space.prevent="emit('select', node)"
        @keydown.arrow-right.prevent="hasChildren(node) && !isExpanded(node.id) && toggleExpand(node.id)"
        @keydown.arrow-left.prevent="hasChildren(node) && isExpanded(node.id) && toggleExpand(node.id)"
      >
        <button
          v-if="hasChildren(node)"
          type="button"
          class="question-chapter-tree__expand"
          :aria-label="isExpanded(node.id) ? `收起${node.name}` : `展开${node.name}`"
          @click.stop="toggleExpand(node.id)"
        >
          <font-awesome-icon
            :icon="['fas', 'chevron-right']"
            :class="{ 'rotate-90': isExpanded(node.id) }"
            aria-hidden="true"
          />
        </button>
        <span v-else class="question-chapter-tree__leaf" aria-hidden="true"></span>

        <span class="question-chapter-tree__marker" :class="{ 'question-chapter-tree__marker--root': level === 0 }" aria-hidden="true"></span>
        <span class="min-w-0 flex-1 truncate" :title="node.name">{{ node.name }}</span>

        <span v-if="selectedCount(node.id) > 0" class="question-chapter-tree__selected-count">
          {{ selectedCount(node.id) }}选
        </span>
        <span v-if="totalCount(node) > 0" class="question-chapter-tree__total-count">
          {{ totalCount(node) }}
        </span>
      </div>

      <Transition name="chapter-tree-children">
        <div
          v-if="hasChildren(node) && isExpanded(node.id)"
          class="question-chapter-tree__children"
          role="group"
        >
          <QuestionChapterTree
            :nodes="node.children"
            :level="level + 1"
            :active-id="activeId"
            :selected-counts="selectedCounts"
            @select="handleChildSelect"
          />
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 出题工作台章节树。
 * 树节点只负责章节定位，题目选择由右侧题目卡片完成，避免把完整题目内容挤进树结构。
 */
import { ref } from 'vue'
import type { CategoryTreeNode } from '@/types'

defineOptions({ name: 'QuestionChapterTree' })

interface Props {
  nodes: CategoryTreeNode[]
  level?: number
  activeId?: number | null
  selectedCounts?: Record<number, number>
}

const props = withDefaults(defineProps<Props>(), {
  level: 0,
  activeId: null,
  selectedCounts: () => ({}),
})

const emit = defineEmits<{
  select: [node: CategoryTreeNode]
}>()

const expandedIds = ref<number[]>([])

const hasChildren = (node: CategoryTreeNode) => node.children.length > 0
const isExpanded = (nodeId: number) => expandedIds.value.includes(nodeId)
const selectedCount = (nodeId: number) => props.selectedCounts[nodeId] || 0
const totalCount = (node: CategoryTreeNode) => node.subtreeQuestionCount ?? node.questionCount ?? 0

const toggleExpand = (nodeId: number) => {
  expandedIds.value = isExpanded(nodeId)
    ? expandedIds.value.filter(id => id !== nodeId)
    : [...expandedIds.value, nodeId]
}

const handleChildSelect = (node: CategoryTreeNode) => {
  emit('select', node)
}
</script>

<style scoped>
.question-chapter-tree__item {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 38px;
  gap: 7px;
  margin: 2px 0;
  padding-top: 7px;
  padding-right: 10px;
  padding-bottom: 7px;
  border-radius: 10px;
  color: #647078;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.question-chapter-tree__item:hover {
  background: color-mix(in srgb, var(--brand-accent) 6%, transparent);
  color: #33404a;
}

.question-chapter-tree__item:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--brand-accent) 65%, transparent);
  outline-offset: 2px;
}

.question-chapter-tree__item--active {
  background: linear-gradient(90deg, color-mix(in srgb, var(--brand-accent) 14%, transparent), color-mix(in srgb, var(--brand-accent) 4%, transparent));
  box-shadow: inset 3px 0 0 #8b6f47;
  color: #704f2d;
  font-weight: 650;
}

.question-chapter-tree__item--root {
  color: #3b464b;
  font-weight: 600;
}

.question-chapter-tree__expand,
.question-chapter-tree__leaf {
  display: inline-flex;
  flex: 0 0 20px;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #a0a7a8;
}

.question-chapter-tree__expand {
  cursor: pointer;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.question-chapter-tree__expand:hover {
  background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
  color: #8b6f47;
}

.question-chapter-tree__expand svg {
  transition: transform 0.2s ease;
  font-size: 10px;
}

.question-chapter-tree__marker {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 999px;
  background: #c5cccb;
}

.question-chapter-tree__marker--root {
  width: 8px;
  height: 8px;
  flex-basis: 8px;
  background: #8b6f47;
}

.question-chapter-tree__item--active .question-chapter-tree__marker {
  background: #8b6f47;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-accent) 12%, transparent);
}

.question-chapter-tree__selected-count,
.question-chapter-tree__total-count {
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 2px 6px;
  font-size: 10px;
  line-height: 1.2;
}

.question-chapter-tree__selected-count {
  background: color-mix(in srgb, var(--brand-accent) 12%, transparent);
  color: #8b6f47;
  font-weight: 700;
}

.question-chapter-tree__total-count {
  min-width: 22px;
  background: rgba(36, 50, 59, 0.06);
  color: #8a9292;
  text-align: center;
}

.question-chapter-tree__children {
  margin-left: 15px;
  border-left: 1px solid color-mix(in srgb, var(--brand-accent) 14%, transparent);
  padding-left: 4px;
}

.chapter-tree-children-enter-active,
.chapter-tree-children-leave-active {
  overflow: hidden;
  transition: opacity 0.2s ease, max-height 0.25s ease;
}

.chapter-tree-children-enter-from,
.chapter-tree-children-leave-to {
  max-height: 0;
  opacity: 0;
}

.chapter-tree-children-enter-to,
.chapter-tree-children-leave-from {
  max-height: 1000px;
  opacity: 1;
}

.rotate-90 {
  transform: rotate(90deg);
}
</style>
