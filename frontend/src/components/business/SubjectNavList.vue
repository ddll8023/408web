<!-- 科目分类导航列表：桌面科目侧栏与移动端目录抽屉共用的受控列表。 -->
<template>
  <div ref="listRoot" class="subject-list px-2">
    <div
      v-for="sub in subjects"
      :key="sub.id"
      class="subject-group mb-1"
    >
      <div
        class="subject-item w-full mx-0 mb-0.5 rounded-lg px-2 py-0 transition-colors duration-200"
        :class="{
          'active bg-accent/8': activeSubjectId === sub.id,
          'hover:bg-black/3': activeSubjectId !== sub.id
        }"
      >
        <div class="item-content flex items-center h-11 w-full">
          <button
            type="button"
            class="icon-area flex items-center justify-center w-6 h-6 mr-1 shrink-0 rounded border-0 bg-transparent p-0 cursor-pointer transition-colors duration-200 hover:bg-black/5"
            :aria-label="(expandedSubjectId === sub.id ? '收起 ' : '展开 ') + sub.name + '分类'"
            :aria-expanded="!collapsed && expandedSubjectId === sub.id"
            :aria-controls="`${listId}-categories-${sub.id}`"
            @click="emit('toggle-expand', sub)"
          >
            <font-awesome-icon
              :icon="['fas', expandedSubjectId === sub.id ? 'chevron-down' : 'chevron-right']"
              class="expand-icon text-sm text-gray-400 transition-transform duration-300 ease"
              :class="{ 'rotate-90': expandedSubjectId === sub.id }"
              aria-hidden="true"
            />
          </button>
          <button
            v-if="!collapsed"
            type="button"
            class="subject-select min-w-0 flex flex-1 items-center border-0 bg-transparent p-0 text-left cursor-pointer"
            :aria-label="'选择 ' + sub.name"
            :aria-current="activeSubjectId === sub.id ? 'page' : undefined"
            @click="emit('select-subject', sub)"
          >
            <transition name="fade" mode="out-in">
              <span v-if="!collapsed" class="item-label min-w-0 flex-1 text-base font-medium text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis">{{ sub.name }}</span>
            </transition>
            <transition name="fade" mode="out-in">
              <span v-if="!collapsed && (sub.questionCount ?? 0) > 0" class="count-badge text-xs text-gray-400 bg-black/5 px-1.5 py-0.5 rounded-full ml-auto">
                {{ sub.questionCount }}
              </span>
            </transition>
          </button>
        </div>
      </div>

      <!-- 多级分类树 -->
      <Transition name="collapse">
        <div
          v-if="getCategoryTree(sub.id).length > 0 && !collapsed && expandedSubjectId === sub.id"
          :id="`${listId}-categories-${sub.id}`"
          class="category-list py-0.5 px-0 mt-0.5"
          role="tree"
          :aria-label="`${sub.name}分类`"
        >
          <CategoryTreeItem
            v-for="cat in getCategoryTree(sub.id)"
            :key="cat.id"
            :category="cat"
            :level="0"
            :active-category="activeSubjectId === sub.id ? filterCategory : ''"
            :expanded-ids="expandedIds"
            :base-indent="38"
            :indent-step="14"
            @select="(categoryName) => emit('select-category', { subject: sub, category: categoryName })"
            @toggle-expand="toggleCategoryExpand"
          />
        </div>
      </Transition>
    </div>

    <div v-if="!loading && subjects.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-400">
      <font-awesome-icon :icon="['fas', 'folder-open']" class="text-3xl mb-2" aria-hidden="true" />
      <span class="text-sm">暂无科目</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 科目分类导航列表
 * 只渲染科目与分类树，展开状态由父组件通过 v-model:expandedIds 持有，
 * 使桌面侧栏与移动端目录抽屉共享同一份展开状态；名称命中分类树时自动展开祖先路径
 */
import type { PropType } from 'vue'
import type { CategoryTreeNode, Subject } from '@/types'
import { getCurrentInstance, onMounted, ref, watch } from 'vue'
import CategoryTreeItem from './CategoryTreeItem.vue'
import { findCategoryPath } from '@/utils/examCategoryGrouping'

const props = defineProps({
  // 科目列表
  subjects: {
    type: Array as PropType<Subject[]>,
    default: () => []
  },
  // 各科目的分类树 { subjectId: CategoryTreeNode[] }
  subjectCategories: {
    type: Object as PropType<Record<number, CategoryTreeNode[]>>,
    default: () => ({})
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
  },
  // 侧栏收起时只保留科目图标，抽屉内始终展开显示
  collapsed: {
    type: Boolean,
    default: false
  },
  // 是否在挂载后把当前分类滚入视口（抽屉每次打开都会重新挂载）
  autoScrollActive: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  'update:expandedIds': [ids: number[]]
  'select-subject': [subject: Subject]
  'toggle-expand': [subject: Subject]
  'select-category': [selection: { subject: Subject; category: string }]
}>()

const listRoot = ref<HTMLElement | null>(null)

// 桌面侧栏与抽屉可能同时存在于 DOM，分类面板 id 需按实例区分
const listId = `subject-nav-${getCurrentInstance()?.uid ?? 0}`

/** 获取当前科目的分类树。 */
const getCategoryTree = (subjectId: number) => {
  const categories = props.subjectCategories[subjectId]
  return Array.isArray(categories) ? categories : []
}

/**
 * 切换分类展开状态（支持多级分类同时展开）
 */
const toggleCategoryExpand = (categoryId: number) => {
  const ids = props.expandedIds
  const nextIds = ids.includes(categoryId)
    ? ids.filter(id => id !== categoryId)
    : [...ids, categoryId]
  emit('update:expandedIds', nextIds)
}

const ensureExpanded = (ids: number[]) => {
  if (ids.length === 0) return
  const merged = Array.from(new Set([...props.expandedIds, ...ids]))
  if (merged.length === props.expandedIds.length) return
  emit('update:expandedIds', merged)
}

// 激活分类变化时展开其祖先路径，保证在抽屉中能看到当前选中项
watch(
  [() => props.activeSubjectId, () => props.filterCategory, () => props.subjectCategories],
  () => {
    if (!props.filterCategory || props.activeSubjectId === null) return
    const tree = getCategoryTree(Number(props.activeSubjectId))
    const path = findCategoryPath(tree, props.filterCategory)
    ensureExpanded(path.slice(0, -1).map(node => node.id))
  },
  { immediate: true },
)

onMounted(() => {
  if (!props.autoScrollActive) return
  listRoot.value?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: 'nearest' })
})
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

/* 科目分类展开动画：只做合成层动画，避免与递归分类节点的布局变化叠加。 */
.collapse-enter-active,
.collapse-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
  will-change: opacity, transform;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* 旋转动画类 */
.rotate-90 {
  transform: rotate(90deg);
}

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active,
  .fade-leave-active,
  .collapse-enter-active,
  .collapse-leave-active {
    transition: none;
  }
}
</style>
