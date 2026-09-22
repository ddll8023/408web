<!-- 分类管理科目筛选：桌面侧栏与窄屏底部抽屉共用的科目统计列表。 -->
<template>
  <div class="category-subject-filter rounded-xl border border-accent/8 bg-white p-6 shadow-sm">
    <h3 class="m-0 mb-4 flex items-center gap-2 border-b border-accent/10 pb-3 text-sm font-semibold text-accent">
      <font-awesome-icon :icon="['fas', 'folder']" class="text-base" />
      科目筛选
    </h3>
    <div class="flex flex-col gap-1">
      <button
        v-for="stat in stats"
        :key="stat.id"
        type="button"
        class="flex w-full items-center justify-between rounded-lg border-0 bg-transparent px-3 py-2.5 text-left transition-all duration-200"
        :class="[
          selectedId === stat.id ? 'bg-gradient-to-r from-accent/12 to-accent/6' : 'hover:bg-accent/6',
          { 'pointer-events-none opacity-60': disabled }
        ]"
        :aria-disabled="disabled"
        @click="emit('select', stat.id)"
        @keydown.enter.prevent="emit('select', stat.id)"
        @keydown.space.prevent="emit('select', stat.id)"
      >
        <span class="flex min-w-0 items-center gap-2.5">
          <span
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent/8 text-sm text-ink-mute transition-all duration-200"
            :class="{ '!bg-accent/15 !text-accent': selectedId === stat.id }"
          >
            <font-awesome-icon :icon="['fas', 'folder']" />
          </span>
          <span
            class="overflow-hidden text-ellipsis whitespace-nowrap text-sm text-ink transition-all duration-200"
            :class="{ '!font-semibold !text-accent': selectedId === stat.id }"
          >
            {{ stat.name }}
          </span>
          <CustomTooltip v-if="stat.enabledCount < stat.count" :content="`${stat.count - stat.enabledCount} 个分类已禁用`" placement="top">
            <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="ml-1 text-sm text-[#e6a23c]" />
          </CustomTooltip>
        </span>
        <span
          class="min-w-[36px] rounded-[10px] bg-accent/10 px-2 py-0.5 text-center text-xs font-semibold text-accent"
          :class="{ '!bg-accent !text-white': selectedId === stat.id }"
        >
          {{ stat.questionCount }}
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 分类管理的科目筛选列表。
 * 只负责统计项呈现和选择事件，不负责分类请求或当前筛选业务。
 */
import { toRefs } from 'vue'
import CustomTooltip from '@/components/basic/Tooltip.vue'

export interface CategorySubjectStat {
  id: number
  name: string
  count: number
  enabledCount: number
  questionCount: number
}

interface Props {
  stats: readonly CategorySubjectStat[]
  selectedId: number | null
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  select: [subjectId: number]
}>()

const { stats, selectedId, disabled } = toRefs(props)
</script>
