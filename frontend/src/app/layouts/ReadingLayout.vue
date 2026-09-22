<!-- 阅读页面布局外壳：统一宽屏导航、窄屏导航和题目内容滚动容器。 -->
<template>
  <div class="app-viewport-page overflow-hidden flex flex-col bg-surface">
    <div class="flex-1 flex flex-col md:flex-row relative overflow-hidden">
      <slot name="wide-nav" />

      <div ref="contentRef" class="scrollbar-stable flex-1 w-full min-w-0 overflow-y-auto bg-surface md:w-0">
        <slot name="compact-nav" />
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 阅读页面布局外壳。
 * 只负责设备相关的页面骨架，题目查询、筛选、答案和内容渲染由业务页面负责。
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'

const emit = defineEmits<{
  'content-ready': [element: HTMLElement | null]
}>()

const contentRef = ref<HTMLElement | null>(null)

onMounted(() => {
  emit('content-ready', contentRef.value)
})

onBeforeUnmount(() => {
  emit('content-ready', null)
})
</script>
