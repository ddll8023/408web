<template>
  <aside
    class="order-first self-start xl:order-none xl:sticky xl:top-4"
    :aria-label="`${theme.label}分类大纲`"
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
        <span class="font-semibold text-[#33404A]">分类大纲</span>
        <span class="text-xs text-gray-400">{{ items.length }} 个分组</span>
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
              <h3 class="truncate text-sm font-semibold text-[#33404A]">分类大纲</h3>
            </div>
            <span class="shrink-0 text-xs text-gray-400">{{ items.length }} 个分组</span>
          </div>
          <p class="mt-1 text-xs text-gray-500">点击跳转到对应题目区域</p>
        </div>

        <nav class="max-h-[min(60vh,520px)] overflow-y-auto p-2" :aria-label="`${theme.label}分类大纲内容`">
          <ol class="relative space-y-0.5">
            <li v-for="item in items" :key="item.anchorId" class="relative">
              <button
                type="button"
                class="group relative flex min-h-9 w-full items-center gap-2 rounded-lg pr-2 text-left text-sm transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47]"
                :class="[
                  activeId === item.anchorId ? theme.active : 'text-gray-600 hover:bg-black/[0.04]',
                  item.depth === 0 ? 'font-medium' : 'font-normal'
                ]"
                :style="{ paddingLeft: `${10 + item.depth * 16}px` }"
                :aria-current="activeId === item.anchorId ? 'location' : undefined"
                @click="emit('jump', item.anchorId)"
              >
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
                <span class="min-w-0 flex-1 truncate" :title="item.label">{{ item.label }}</span>
                <span class="shrink-0 text-xs" :class="activeId === item.anchorId ? theme.count : 'text-gray-400'">
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
  kind: 'exam' | 'mock'
}

const props = defineProps<Props>()
const emit = defineEmits<{ jump: [anchorId: string] }>()

let nextOutlineId = 0
const outlineContentId = `category-outline-content-${++nextOutlineId}`
const isOpen = ref(false)

const theme = computed(() => {
  if (props.kind === 'exam') {
    return {
      label: '真题',
      border: 'border-[#C9D8E2]',
      headerSurface: 'bg-[#EEF4F8]',
      icon: 'text-[#56738A]',
      accent: 'bg-[#56738A]',
      dot: 'bg-[#56738A]',
      active: 'bg-[#EEF4F8] text-[#486B84]',
      count: 'text-[#486B84]',
    }
  }

  return {
    label: '模拟题',
    border: 'border-[#CBE1D9]',
    headerSurface: 'bg-[#EFF7F4]',
    icon: 'text-[#3F8576]',
    accent: 'bg-[#3F8576]',
    dot: 'bg-[#3F8576]',
    active: 'bg-[#EFF7F4] text-[#347465]',
    count: 'text-[#347465]',
  }
})

const items = computed(() => props.items)
const activeId = computed(() => props.activeId)
</script>
