<!-- 出题工作台布局：宽屏展示章节、题目和出题篮三栏，窄屏改用顶部入口与底部抽屉。 -->
<template>
  <div class="question-compose-layout">
    <div v-if="isWide" class="compose-workspace">
      <slot name="chapter" />
      <slot name="content" />
      <div class="question-basket-slot">
        <slot name="basket" />
      </div>
    </div>

    <div v-else class="compose-mobile-shell">
      <div class="compose-mobile-toolbar" aria-label="出题工作台导航">
        <button type="button" class="compose-mobile-toolbar__button" @click="chapterVisible = true">
          <font-awesome-icon :icon="['fas', 'list']" aria-hidden="true" />
          <span class="min-w-0 flex-1 truncate">章节目录</span>
          <span class="compose-mobile-toolbar__value">{{ chapterTitle }}</span>
        </button>
        <button type="button" class="compose-mobile-toolbar__button" @click="basketVisible = true">
          <font-awesome-icon :icon="['fas', 'inbox']" aria-hidden="true" />
          <span>出题篮</span>
          <span class="compose-mobile-toolbar__badge">{{ selectedCount }}</span>
        </button>
      </div>

      <div class="compose-mobile-content">
        <slot name="content" />
      </div>

      <BottomSheet
        v-model:visible="chapterVisible"
        title="章节目录"
        max-height="min(82dvh, 760px)"
      >
        <slot name="chapter" />
      </BottomSheet>

      <BottomSheet
        v-model:visible="basketVisible"
        title="出题篮"
        max-height="min(82dvh, 760px)"
      >
        <div class="compose-mobile-basket">
          <slot name="basket" />
        </div>
      </BottomSheet>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 出题工作台布局外壳。
 * 宽屏保留三栏工作区，窄屏将章节目录和出题篮收纳到独立底部抽屉，题目内容逻辑由页面负责。
 */
import { computed, onDeactivated, ref, watch } from 'vue'
import BottomSheet from '@/components/basic/BottomSheet.vue'
import { MEDIA_QUERIES } from '@/shared/responsive/breakpoints'
import { useMediaQuery } from '@/shared/responsive/useViewport'

interface Props {
  chapterTitle?: string
  selectedCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  chapterTitle: '未选择章节',
  selectedCount: 0,
})

const isWide = useMediaQuery(MEDIA_QUERIES.wide)
const chapterVisible = ref(false)
const basketVisible = ref(false)

watch(isWide, (wide) => {
  if (wide) {
    chapterVisible.value = false
    basketVisible.value = false
  }
})

onDeactivated(() => {
  chapterVisible.value = false
  basketVisible.value = false
})

const chapterTitle = computed(() => props.chapterTitle)
const selectedCount = computed(() => props.selectedCount)
</script>

<style scoped>
.question-compose-layout {
  min-width: 0;
}

.compose-workspace {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr) 292px;
  align-items: start;
  gap: 0;
  padding: 0;
}

.compose-mobile-shell {
  min-width: 0;
}

.compose-mobile-toolbar {
  display: flex;
  gap: 8px;
  padding: 10px 0 12px;
}

.compose-mobile-toolbar__button {
  display: inline-flex;
  min-width: 0;
  min-height: 42px;
  flex: 1;
  align-items: center;
  gap: 7px;
  border: 1px solid color-mix(in srgb, var(--brand-accent) 18%, transparent);
  border-radius: 10px;
  background: color-mix(in srgb, var(--brand-accent) 6%, white);
  padding: 8px 10px;
  color: var(--brand-ink);
  font-size: 13px;
  text-align: left;
}

.compose-mobile-toolbar__button:focus-visible {
  outline: 2px solid var(--brand-accent);
  outline-offset: 2px;
}

.compose-mobile-toolbar__value {
  max-width: 42%;
  overflow: hidden;
  color: var(--brand-ink-soft);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compose-mobile-toolbar__badge {
  display: inline-flex;
  min-width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--brand-accent);
  color: white;
  font-size: 12px;
}

.compose-mobile-content {
  min-width: 0;
}

.compose-mobile-shell :deep(.chapter-panel) {
  position: static;
  max-height: none;
  overflow: visible;
  border-right: 0;
  padding: 0;
}

.compose-mobile-shell :deep(.chapter-panel__tree) {
  max-height: none;
}

.compose-mobile-shell :deep(.question-content) {
  max-height: none;
  overflow: visible;
  padding: 0;
}

.compose-mobile-basket :deep(.question-basket-slot) {
  border-left: 0;
  padding: 0;
}

@media (min-width: 1024px) and (max-width: 1279px) {
  .compose-workspace {
    grid-template-columns: 238px minmax(0, 1fr);
  }

  .compose-workspace :deep(.question-basket-slot) {
    grid-column: 1 / -1;
    border-top: 1px solid var(--compose-line, #e8ded3);
    border-left: 0;
    padding: 12px 0 0;
  }
}
</style>
