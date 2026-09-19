<!-- 年份题目导航列表：桌面年份侧栏与移动端目录抽屉共用的受控列表。 -->
<template>
  <div ref="listRoot" class="year-nav-list">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center h-32" role="status" aria-live="polite">
      <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-accent text-xl" aria-hidden="true" />
    </div>

    <template v-else>
      <div
        v-for="yearData in yearList"
        :key="yearData.year"
        class="year-group mb-1"
      >
        <!-- 年份标题 -->
        <div
          class="year-title-item px-2 mb-0.5 rounded-lg cursor-pointer transition-all duration-200"
          :class="{ active: activeYear === yearData.year }"
        >
          <div class="title-content flex items-center h-11 px-2 w-full">
            <button
              type="button"
              class="icon-area flex items-center justify-center w-6 h-6 mr-1 rounded border-0 bg-transparent p-0 transition-colors duration-200 hover:bg-black/[0.05]"
              :aria-label="(expandedYears.includes(yearData.year) ? '收起 ' : '展开 ') + yearData.year + '年题目'"
              :aria-expanded="expandedYears.includes(yearData.year)"
              @click="toggleYear(yearData.year)"
            >
              <font-awesome-icon
                :icon="['fas', 'chevron-right']"
                class="expand-icon text-sm transition-transform duration-300 text-gray-400"
                :class="{ 'is-expanded': expandedYears.includes(yearData.year) }"
                aria-hidden="true"
              />
            </button>
            <button
              type="button"
              class="year-text flex-1 border-0 bg-transparent text-left text-[15px] text-gray-800"
              :aria-current="activeYear === yearData.year ? 'page' : undefined"
              @click="emit('year-select', yearData.year)"
            >{{ yearData.year }}年</button>
            <span class="count-badge text-xs text-gray-400 bg-black/[0.05] px-1.5 py-0.5 rounded-full">{{ yearData.exams.length }}</span>
          </div>
        </div>

        <!-- 题目列表 -->
        <Transition name="expand">
          <div
            v-if="expandedYears.includes(yearData.year)"
            class="exam-sub-list mt-0.5 pb-1"
          >
            <button
              type="button"
              v-for="exam in yearData.exams"
              :key="exam.id"
              class="exam-sub-item flex items-center h-9 w-full px-3 pl-9 mb-0.5 rounded-md border-0 bg-transparent cursor-pointer text-left text-gray-500 text-[13px] transition-all duration-200"
              :class="{ active: activeExamId === exam.id }"
              :aria-current="activeExamId === exam.id ? 'page' : undefined"
              @click="emit('exam-select', exam)"
            >
              <font-awesome-icon :icon="['fas', 'file-lines']" class="exam-icon mr-2 text-sm opacity-70" aria-hidden="true" />
              <span class="exam-title flex-1 whitespace-nowrap overflow-hidden text-ellipsis">{{ getExamDisplayText(exam) }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- 空状态提示 -->
      <div v-if="yearList.length === 0" class="empty-state flex flex-col items-center justify-center gap-2 p-8 text-gray-400 text-xs">
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="text-lg text-orange-400" aria-hidden="true" />
        <span>暂无真题数据</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * 年份题目导航列表
 * 只负责渲染年份与题号，展开状态由父组件通过 v-model:expandedYears 持有，
 * 使桌面侧栏与移动端目录抽屉保持同一份展开状态
 */
import type { PropType } from 'vue'
import type { ExamNavQuestion, ExamNavYear } from '@/types'
import { onMounted, ref, watch } from 'vue'

const props = defineProps({
  // 年份导航数据，按年份从新到旧排列
  yearList: {
    type: Array as PropType<ExamNavYear[]>,
    default: () => []
  },
  // 当前激活的年份
  activeYear: {
    type: Number as PropType<number | null>,
    default: null
  },
  // 当前激活的题目 ID
  activeExamId: {
    type: [Number, String] as PropType<number | string | null>,
    default: null
  },
  // 已展开的年份
  expandedYears: {
    type: Array as PropType<number[]>,
    default: () => []
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  // 是否在挂载后把当前项滚入视口（抽屉每次打开都会重新挂载，侧栏不需要该行为）
  autoScrollActive: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  'update:expandedYears': [years: number[]]
  'year-select': [year: number]
  'exam-select': [exam: ExamNavQuestion]
}>()

const listRoot = ref<HTMLElement | null>(null)

/** 更新展开年份的唯一出口，避免多处直接改写父组件状态。 */
const setExpandedYears = (years: number[]) => {
  emit('update:expandedYears', years)
}

const ensureYearExpanded = (year: number | null | undefined) => {
  if (!year || props.expandedYears.includes(year)) return
  setExpandedYears([...props.expandedYears, year])
}

/**
 * 切换年份展开/折叠
 */
const toggleYear = (year: number) => {
  if (props.expandedYears.includes(year)) {
    setExpandedYears(props.expandedYears.filter(item => item !== year))
    return
  }
  setExpandedYears([...props.expandedYears, year])
}

/**
 * 获取题目显示文本
 */
const getExamDisplayText = (exam: ExamNavQuestion) => {
  if (exam.title) return exam.title
  if (exam.questionNumber) return `第 ${exam.questionNumber} 题`
  return exam.category?.join(' · ') || '真题'
}

// 激活年份或题目变化时自动展开，保证侧栏与抽屉都能定位到当前题目
watch(() => props.activeExamId, (newId) => {
  if (newId === null || newId === undefined) return
  const targetId = Number(newId)
  props.yearList.forEach((yearData) => {
    if (yearData.exams.some(exam => exam.id === targetId)) ensureYearExpanded(yearData.year)
  })
}, { immediate: true })

watch(() => props.activeYear, (newYear) => {
  ensureYearExpanded(newYear)
}, { immediate: true })

onMounted(() => {
  if (!props.autoScrollActive) return
  listRoot.value?.querySelector('[aria-current="page"]')?.scrollIntoView({ block: 'nearest' })
})
</script>

<style scoped>
/* 展开图标旋转 */
.year-title-item .expand-icon.is-expanded {
  transform: rotate(90deg);
}

/* 年份激活状态 */
.year-title-item.active {
  background-color: color-mix(in srgb, var(--brand-accent) 8%, transparent);
}

.year-title-item.active .year-text,
.year-title-item.active .count-badge,
.year-title-item.active .expand-icon {
  color: var(--brand-accent);
  font-weight: 600;
}

/* 题目项激活状态 */
.exam-sub-item.active {
  background-color: transparent;
  color: var(--brand-accent);
  font-weight: 500;
  position: relative;
}

.exam-sub-item.active .exam-icon {
  color: var(--brand-accent);
  opacity: 1;
}

/* 左侧指示条 */
.exam-sub-item.active::before {
  content: '';
  position: absolute;
  left: 24px;
  height: 14px;
  width: 2px;
  background-color: var(--brand-accent);
  border-radius: 1px;
}

/* 展开/折叠动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}

@media (prefers-reduced-motion: reduce) {
  .expand-enter-active,
  .expand-leave-active {
    transition: none;
  }
}
</style>
