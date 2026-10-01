<!-- 年份列表：桌面年份侧栏与窄屏目录抽屉共用，只负责年份选择。 -->
<template>
  <div class="year-nav-list">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex h-32 items-center justify-center" role="status" aria-live="polite">
      <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-accent text-xl" aria-hidden="true" />
    </div>

    <template v-else>
      <button
        v-for="yearData in yearList"
        :key="yearData.year"
        type="button"
        class="year-item"
        :class="{ active: activeYear === yearData.year }"
        :aria-current="activeYear === yearData.year ? 'page' : undefined"
        @click="emit('year-select', yearData.year)"
      >
        <font-awesome-icon :icon="['fas', 'calendar-days']" class="year-icon" aria-hidden="true" />
        <span class="year-text">{{ yearData.year }}年</span>
        <span class="count-badge">{{ yearData.exams.length }} 题</span>
      </button>

      <!-- 空状态提示 -->
      <div v-if="yearList.length === 0" class="flex flex-col items-center justify-center gap-2 p-8 text-gray-400 text-xs">
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="text-lg text-orange-400" aria-hidden="true" />
        <span>暂无真题数据</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * 年份列表
 * 只渲染年份与题量，题号导航由题目区右侧大纲承担；
 * 选中年份由父组件通过 activeYear 持有，使桌面侧栏与窄屏目录抽屉共用同一份状态
 */
import type { PropType } from 'vue'
import type { ExamNavYear } from '@/types'

defineProps({
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
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  'year-select': [year: number]
}>()
</script>

<style scoped>
/* 年份列表容器：纵向排列，供侧栏和抽屉复用 */
.year-nav-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 年份项：整行可点击，激活态取品牌色 */
.year-item {
  display: flex;
  min-height: 40px;
  width: 100%;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #1f2937;
  font-size: 15px;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.year-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.year-icon {
  flex: 0 0 auto;
  color: #9ca3af;
  font-size: 13px;
}

.year-text {
  min-width: 0;
  flex: 1;
}

.count-badge {
  flex: 0 0 auto;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  color: #6b7280;
  font-size: 12px;
}

/* 激活年份 */
.year-item.active {
  background-color: color-mix(in srgb, var(--brand-accent) 8%, transparent);
  color: var(--brand-accent);
  font-weight: 600;
}

.year-item.active .year-icon,
.year-item.active .count-badge {
  color: var(--brand-accent);
}
</style>
