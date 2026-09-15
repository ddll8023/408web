<!-- 模拟题完整预览抽屉：只在查看时渲染完整 Markdown 内容。 -->
<template>
  <Teleport to="body">
    <Transition name="question-preview-drawer">
      <div
        v-if="visible && question"
        class="question-preview-drawer"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        @click.self="close"
        @keydown.esc.prevent="close"
      >
        <aside ref="panelRef" class="question-preview-drawer__panel" tabindex="-1">
          <header class="question-preview-drawer__header">
            <div class="min-w-0">
              <p class="question-preview-drawer__eyebrow">QUESTION PREVIEW</p>
              <h2 :id="titleId" class="question-preview-drawer__title">{{ displayTitle }}</h2>
              <div class="question-preview-drawer__meta">
                <span>{{ question.source }}</span>
                <span v-if="question.questionNumber != null">第{{ question.questionNumber }}题</span>
                <span v-for="category in categories" :key="category">{{ category }}</span>
              </div>
            </div>
            <button type="button" class="question-preview-drawer__close" aria-label="关闭预览" @click="close">
              <font-awesome-icon :icon="['fas', 'times']" aria-hidden="true" />
            </button>
          </header>

          <div class="question-preview-drawer__body">
            <section class="question-preview-drawer__section">
              <h3>题目</h3>
              <MarkdownViewer :content="question.content" variant="plain" :interactive="false" />
            </section>

            <section v-if="question.questionType === 'CHOICE' && optionEntries.length > 0" class="question-preview-drawer__section">
              <h3>选项</h3>
              <div class="question-preview-drawer__options">
                <div v-for="([key, value]) in optionEntries" :key="key" class="question-preview-drawer__option">
                  <span class="question-preview-drawer__option-key">{{ key }}</span>
                  <MarkdownViewer :content="value" variant="plain" content-role="option" :interactive="false" />
                </div>
              </div>
            </section>

            <section v-if="question.answer" class="question-preview-drawer__section question-preview-drawer__answer">
              <h3>{{ question.questionType === 'CHOICE' ? '答案与解析' : '参考答案' }}</h3>
              <MarkdownViewer :content="question.answer" variant="plain" :interactive="false" />
            </section>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * 展示单道模拟题完整内容的右侧抽屉。
 * 默认题目卡片不渲染正文，只有打开预览时才加载 Markdown、公式和选项。
 */
import { computed, nextTick, onBeforeUnmount, ref, watch, type PropType } from 'vue'
import type { MockQuestion } from '@/types'
import { parseQuestionOptions } from '@/utils/questionOptions'
import MarkdownViewer from '@/components/basic/MarkdownViewer.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  question: {
    type: Object as PropType<MockQuestion | null>,
    default: null,
  },
})

const emit = defineEmits<{
  'update:visible': [visible: boolean]
}>()

let nextDrawerId = 0
const titleId = `question-preview-title-${++nextDrawerId}`
const panelRef = ref<HTMLElement | null>(null)
let previousBodyOverflow = ''

const displayTitle = computed(() => {
  if (!props.question) return '题目预览'
  if (props.question.title) return props.question.title
  const number = props.question.questionNumber == null ? '' : `第${props.question.questionNumber}题`
  return [props.question.source, number].filter(Boolean).join(' · ') || `模拟题 ID=${props.question.id}`
})

const categories = computed(() => {
  return Array.isArray(props.question?.category)
    ? props.question.category.filter(Boolean)
    : []
})

const optionEntries = computed(() => {
  if (!props.question || props.question.questionType !== 'CHOICE') return []
  return Object.entries(parseQuestionOptions(props.question.options) || {})
})

const close = () => {
  emit('update:visible', false)
}

watch(() => props.visible, async visible => {
  if (typeof document === 'undefined') return
  if (visible) {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    await nextTick()
    panelRef.value?.focus()
  } else {
    document.body.style.overflow = previousBodyOverflow
    previousBodyOverflow = ''
  }
})

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') document.body.style.overflow = previousBodyOverflow
})
</script>

<style scoped>
.question-preview-drawer {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  justify-content: flex-end;
  background: rgba(27, 35, 35, 0.38);
}

.question-preview-drawer__panel {
  display: flex;
  width: min(680px, 92vw);
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  outline: none;
  background: #fffdf8;
  box-shadow: -18px 0 48px rgba(30, 42, 39, 0.18);
}

.question-preview-drawer__header {
  display: flex;
  flex: 0 0 auto;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  border-bottom: 1px solid #e6ded2;
  background: #fbf7f2;
  padding: 24px 26px 18px;
}

.question-preview-drawer__eyebrow {
  margin: 0 0 5px;
  color: #8b6f47;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.question-preview-drawer__title {
  margin: 0;
  color: #333;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.4;
}

.question-preview-drawer__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-top: 9px;
  color: #7f8c8a;
  font-size: 11px;
}

.question-preview-drawer__meta span + span {
  position: relative;
}

.question-preview-drawer__meta span + span::before {
  position: absolute;
  top: 50%;
  left: -8px;
  width: 3px;
  height: 3px;
  border-radius: 999px;
  background: #b7c4c0;
  content: '';
  transform: translateY(-50%);
}

.question-preview-drawer__close {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 10px;
  background: rgba(139, 111, 71, 0.08);
  color: #8b6f47;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.question-preview-drawer__close:hover,
.question-preview-drawer__close:focus-visible {
  background: rgba(139, 111, 71, 0.16);
  color: #704f2d;
  outline: none;
}

.question-preview-drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 26px 40px;
  scrollbar-gutter: stable;
}

.question-preview-drawer__section {
  border-bottom: 1px solid #ece5db;
  padding-bottom: 22px;
}

.question-preview-drawer__section + .question-preview-drawer__section {
  padding-top: 22px;
}

.question-preview-drawer__section:last-child {
  border-bottom: 0;
}

.question-preview-drawer__section h3 {
  margin: 0 0 12px;
  color: #8b6f47;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.question-preview-drawer__options {
  display: grid;
  gap: 9px;
}

.question-preview-drawer__option {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr);
  gap: 8px;
  align-items: start;
  border: 1px solid #e9e3d9;
  border-radius: 10px;
  background: #fff;
  padding: 10px 12px;
}

.question-preview-drawer__option-key {
  display: inline-flex;
  width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(139, 111, 71, 0.35);
  border-radius: 7px;
  color: #8b6f47;
  font-size: 12px;
  font-weight: 800;
}

.question-preview-drawer__answer {
  border-left: 3px solid #8b6f47;
  padding-left: 15px;
}

.question-preview-drawer-enter-active,
.question-preview-drawer-leave-active {
  transition: background-color 0.25s ease;
}

.question-preview-drawer-enter-active .question-preview-drawer__panel,
.question-preview-drawer-leave-active .question-preview-drawer__panel {
  transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.question-preview-drawer-enter-from,
.question-preview-drawer-leave-to {
  background: rgba(27, 35, 35, 0);
}

.question-preview-drawer-enter-from .question-preview-drawer__panel,
.question-preview-drawer-leave-to .question-preview-drawer__panel {
  transform: translateX(100%);
}

@media (max-width: 640px) {
  .question-preview-drawer__panel {
    width: 100vw;
  }

  .question-preview-drawer__header,
  .question-preview-drawer__body {
    padding-right: 18px;
    padding-left: 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .question-preview-drawer-enter-active,
  .question-preview-drawer-leave-active,
  .question-preview-drawer-enter-active .question-preview-drawer__panel,
  .question-preview-drawer-leave-active .question-preview-drawer__panel {
    transition: none;
  }
}
</style>
