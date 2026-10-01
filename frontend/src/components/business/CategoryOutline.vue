<!-- 分类大纲：展示当前父分类范围内的题目分组，支撑页内跳转；窄屏隐藏，改由目录抽屉提供同能力。 -->
<template>
  <aside
    class="order-first self-start xl:order-none xl:sticky xl:top-4"
    :class="props.hideBelowXl ? 'hidden xl:block' : 'max-md:hidden'"
    :aria-label="`${theme.label}${props.title}`"
  >
    <button
      type="button"
      class="flex w-full items-center justify-between rounded-xl border bg-white/80 px-4 py-3 text-left shadow-sm xl:hidden"
      :class="theme.border"
      :aria-expanded="isOpen"
      :aria-controls="outlineContentId"
      @click="isOpen = !isOpen"
    >
      <span class="flex min-w-0 items-center gap-2">
        <font-awesome-icon :icon="['fas', 'list']" :class="theme.icon" aria-hidden="true" />
        <span class="font-semibold text-[#33404A]">{{ props.title }}</span>
        <span v-if="props.showSummary" class="text-xs text-gray-400">{{ items.length }} 个分组</span>
      </span>
      <font-awesome-icon
        :icon="isOpen ? ['fas', 'chevron-up'] : ['fas', 'chevron-down']"
        class="shrink-0 text-gray-400"
        aria-hidden="true"
      />
    </button>

    <div
      :id="outlineContentId"
      class="mt-3 xl:mt-0"
      :class="isOpen ? 'block' : 'hidden xl:block'"
    >
      <div class="overflow-hidden rounded-xl border bg-white/75 shadow-sm" :class="theme.border">
        <div class="border-b px-4 py-3" :class="theme.headerSurface">
          <div class="flex items-center justify-between gap-3">
            <div class="flex min-w-0 items-center gap-2">
              <font-awesome-icon :icon="['fas', 'list']" :class="theme.icon" aria-hidden="true" />
              <h3 class="truncate text-sm font-semibold text-[#33404A]">{{ props.title }}</h3>
            </div>
            <span v-if="props.showSummary" class="shrink-0 text-xs text-gray-400">{{ items.length }} 个分组</span>
          </div>
          <p class="mt-1 text-xs text-gray-500">{{ props.description }}</p>
        </div>

        <nav
          class="scrollbar-stable overflow-y-auto px-2"
          :class="gridVariant ? 'max-h-[min(calc(100vh-8rem),760px)]' : 'max-h-[min(60vh,520px)]'"
          :aria-label="`${theme.label}${props.title}内容`"
        >
          <ol class="relative py-2" :class="gridVariant ? 'grid grid-cols-4 gap-1' : 'space-y-0.5'">
            <li
              v-for="item in items"
              :key="item.anchorId"
              class="relative"
              :class="gridVariant && isGroupItem(item) ? 'col-span-full' : ''"
            >
              <button
                type="button"
                class="group relative flex w-full items-center transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                :class="[buttonShapeClass(item), buttonColorClass(item)]"
                :style="buttonStyle(item)"
                :aria-label="item.label"
                :title="item.label"
                :aria-current="activeId === item.anchorId ? 'location' : undefined"
                @click="emit('jump', item.anchorId)"
              >
                <template v-if="!isGridNumberItem(item)">
                  <span
                    class="absolute inset-y-1 left-0 w-0.5 rounded-full transition-opacity"
                    :class="activeId === item.anchorId ? theme.accent : 'opacity-0'"
                    aria-hidden="true"
                  />
                  <span
                    class="h-1.5 w-1.5 shrink-0 rounded-full"
                    :class="activeId === item.anchorId ? theme.dot : 'bg-gray-300'"
                    aria-hidden="true"
                  />
                </template>
                <span
                  class="min-w-0 flex-1 truncate"
                  :class="isGridNumberItem(item) ? 'text-center' : ''"
                >{{ isGridNumberItem(item) ? (item.shortLabel ?? item.label) : item.label }}</span>
                <span v-if="item.count != null" class="shrink-0 text-xs" :class="activeId === item.anchorId ? theme.count : 'text-gray-400'">
                  {{ item.count }}题
                </span>
              </button>
            </li>
          </ol>
        </nav>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CategoryOutlineItem } from '@/types'

interface Props {
  items: readonly CategoryOutlineItem[]
  activeId: string
  kind: 'exam' | 'mock' | 'adaptation'
  hideBelowXl?: boolean
  /** 大纲标题，默认按分类场景展示 */
  title?: string
  /** 标题下的说明文案 */
  description?: string
  /** 是否显示「N 个分组」统计，题号导航等混合条目场景可关闭 */
  showSummary?: boolean
  /** 条目呈现：列表（默认）或紧凑题号网格 */
  variant?: 'list' | 'number-grid'
}

const props = withDefaults(defineProps<Props>(), {
  hideBelowXl: false,
  title: '分类大纲',
  description: '点击跳转到对应题目区域',
  showSummary: true,
  variant: 'list',
})
const emit = defineEmits<{ jump: [anchorId: string] }>()

let nextOutlineId = 0
const outlineContentId = `category-outline-content-${++nextOutlineId}`
const isOpen = ref(false)

const theme = computed(() => {
  if (props.kind === 'exam') {
    return {
      label: '真题',
      border: 'border-exam-border',
      headerSurface: 'bg-exam-surface',
      icon: 'text-exam-accent',
      accent: 'bg-exam-accent',
      dot: 'bg-exam-accent',
      active: 'bg-exam-surface text-exam-strong',
      count: 'text-exam-strong',
    }
  }

  if (props.kind === 'adaptation') {
    return {
      label: '改编题',
      border: 'border-accent/20',
      headerSurface: 'bg-accent/8',
      icon: 'text-accent',
      accent: 'bg-accent',
      dot: 'bg-accent',
      active: 'bg-accent/10 text-accent',
      count: 'text-accent',
    }
  }

  return {
    label: '模拟题',
    border: 'border-mock-border',
    headerSurface: 'bg-mock-surface',
    icon: 'text-mock-accent',
    accent: 'bg-mock-accent',
    dot: 'bg-mock-accent',
    active: 'bg-mock-surface text-mock-strong',
    count: 'text-mock-strong',
  }
})

const items = computed(() => props.items)
const activeId = computed(() => props.activeId)

// 是否使用紧凑题号网格排版
const gridVariant = computed(() => props.variant === 'number-grid')

/** 分组条目（分类名或题型名）：网格模式下独占整行。 */
const isGroupItem = (item: CategoryOutlineItem) => item.depth === 0

/** 网格模式下的题号条目：渲染为居中方块，不显示圆点与层级缩进。 */
const isGridNumberItem = (item: CategoryOutlineItem) => gridVariant.value && item.depth > 0

/** 条目形状：网格方块、分组标题或层级列表项。 */
const buttonShapeClass = (item: CategoryOutlineItem) => {
  if (isGridNumberItem(item)) return 'min-h-9 justify-center rounded-lg border text-sm font-normal'
  return `min-h-9 gap-2 rounded-lg pr-2 text-left text-sm ${item.depth === 0 ? 'font-medium' : 'font-normal'}`
}

/** 条目配色：网格方块用边框和背景表达状态，其余沿用列表配色。 */
const buttonColorClass = (item: CategoryOutlineItem) => {
  const isActive = activeId.value === item.anchorId
  if (isGridNumberItem(item)) {
    return isActive
      ? `${theme.value.active} border-transparent`
      : 'border-gray-200 bg-white text-gray-600 hover:bg-black/[0.04]'
  }
  return isActive ? theme.value.active : 'text-gray-600 hover:bg-black/[0.04]'
}

/** 网格方块不缩进，列表项按 depth 递进。 */
const buttonStyle = (item: CategoryOutlineItem) => (
  isGridNumberItem(item) ? {} : { paddingLeft: `${10 + item.depth * 16}px` }
)
</script>
