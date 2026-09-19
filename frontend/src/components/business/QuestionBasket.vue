<!-- 出题工作台出题篮：展示已选顺序并提供批量 Word 复制。 -->
<template>
  <aside class="question-basket" aria-label="出题篮">
    <header class="question-basket__header">
      <div>
        <p class="question-basket__eyebrow">临时出题篮</p>
        <h2 class="question-basket__title">出题篮</h2>
      </div>
      <span class="question-basket__count">{{ questions.length }}</span>
    </header>

    <div v-if="questions.length === 0" class="question-basket__empty">
      <span class="question-basket__empty-mark" aria-hidden="true">+</span>
      <p>从章节题目中勾选内容</p>
      <span>选中顺序会作为复制顺序</span>
    </div>

    <div v-else class="question-basket__items">
      <div
        v-for="(question, index) in questions"
        :key="question.id"
        class="question-basket__item"
      >
        <span class="question-basket__index">{{ String(index + 1).padStart(2, '0') }}</span>
        <span class="question-basket__item-title" :title="getQuestionLabel(question)">
          {{ getQuestionLabel(question) }}
        </span>
        <div class="question-basket__item-actions">
          <button
            type="button"
            class="question-basket__icon-button"
            :disabled="index === 0"
            aria-label="上移题目"
            @click="emit('move', question.id, -1)"
          >
            <font-awesome-icon :icon="['fas', 'chevron-up']" aria-hidden="true" />
          </button>
          <button
            type="button"
            class="question-basket__icon-button"
            :disabled="index === questions.length - 1"
            aria-label="下移题目"
            @click="emit('move', question.id, 1)"
          >
            <font-awesome-icon :icon="['fas', 'chevron-down']" aria-hidden="true" />
          </button>
          <button
            type="button"
            class="question-basket__icon-button question-basket__icon-button--danger"
            aria-label="移除题目"
            @click="emit('remove', question.id)"
          >
            <font-awesome-icon :icon="['fas', 'times']" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>

    <footer class="question-basket__footer">
      <div class="question-basket__footer-meta">
        <span>共 {{ questions.length }} 题</span>
        <button
          type="button"
          class="question-basket__clear"
          :disabled="questions.length === 0 || disabled"
          @click="emit('clear')"
        >
          清空
        </button>
      </div>
      <span v-if="questions.length > maxCount" class="question-basket__warning">
        单次最多复制 {{ maxCount }} 题
      </span>
      <div class="question-basket__copy">
        <QuestionBatchCopyMenu
          :questions="questions"
          :disabled="disabled || questions.length > maxCount"
          @word-copied="handleWordCopied"
        />
      </div>
    </footer>
  </aside>
</template>

<script setup lang="ts">
/**
 * 出题篮组件。
 * 仅负责已选题目的顺序展示和事件转发，选择状态仍由页面 composable 持有。
 */
import { type PropType } from 'vue'
import type { MockQuestion } from '@/types'
import type { RichCopyResult } from '@/utils/questionCopy'
import QuestionBatchCopyMenu from '@/components/business/QuestionBatchCopyMenu.vue'

type QuestionRow = MockQuestion & { examStatusLoading?: boolean }

const props = defineProps({
  questions: {
    type: Array as PropType<QuestionRow[]>,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  maxCount: {
    type: Number,
    default: 100,
  },
})

const emit = defineEmits<{
  clear: []
  move: [questionId: number, direction: -1 | 1]
  remove: [questionId: number]
  'word-copied': [result: RichCopyResult, questionIds: number[]]
}>()

const getQuestionLabel = (question: MockQuestion) => {
  const number = question.questionNumber == null ? '' : `第${question.questionNumber}题`
  return [question.source, question.title, number].filter(Boolean).join(' · ') || `模拟题 ID=${question.id}`
}

const handleWordCopied = (result: RichCopyResult, questionIds: number[]) => {
  emit('word-copied', result, questionIds)
}
</script>

<style scoped>
.question-basket {
  position: sticky;
  top: 16px;
  display: flex;
  min-height: 420px;
  max-height: calc(var(--app-page-height) - 48px);
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #eadfd4;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-basket__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  border-bottom: 1px solid #eadfd4;
  background: #fbf7f2;
  padding: 16px 17px 14px;
}

.question-basket__eyebrow {
  margin: 0 0 3px;
  color: #8b6f47;
  font-size: 12px;
  font-weight: 600;
}

.question-basket__title {
  margin: 0;
  color: #333;
  font-size: 18px;
  font-weight: 750;
}

.question-basket__count {
  display: inline-flex;
  min-width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #8b6f47;
  color: white;
  font-size: 14px;
  font-weight: 800;
}

.question-basket__empty {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 32px 20px;
  color: #999;
  text-align: center;
}

.question-basket__empty-mark {
  display: inline-flex;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border: 1px dashed #d4c4a8;
  border-radius: 12px;
  color: #8b6f47;
  font-size: 25px;
  font-weight: 300;
}

.question-basket__empty p {
  margin: 0 0 5px;
  color: #6f5738;
  font-size: 13px;
  font-weight: 700;
}

.question-basket__empty span:last-child {
  font-size: 11px;
}

.question-basket__items {
  flex: 1;
  overflow-y: auto;
  scrollbar-gutter: stable;
  padding: 9px;
}

.question-basket__item {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px;
  min-height: 48px;
  border-bottom: 1px solid #f0ebe4;
  padding: 8px 4px;
}

.question-basket__index {
  color: #8b6f47;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px;
  font-weight: 800;
}

.question-basket__item-title {
  min-width: 0;
  overflow: hidden;
  color: #666;
  font-size: 12px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question-basket__item-actions {
  display: flex;
  gap: 1px;
}

.question-basket__icon-button {
  display: inline-flex;
  width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #a08c72;
  cursor: pointer;
  font-size: 10px;
}

.question-basket__icon-button:hover:not(:disabled) {
  background: rgba(139, 111, 71, 0.1);
  color: #8b6f47;
}

.question-basket__icon-button--danger:hover:not(:disabled) {
  background: rgba(180, 80, 64, 0.1);
  color: #b45040;
}

.question-basket__icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.3;
}

.question-basket__footer {
  border-top: 1px solid #eadfd4;
  background: #fbf7f2;
  padding: 12px;
}

.question-basket__footer-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #7e8e8a;
  font-size: 11px;
}

.question-basket__clear {
  border: 0;
  background: transparent;
  color: #a25f50;
  cursor: pointer;
  font-size: 11px;
}

.question-basket__clear:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.question-basket__warning {
  display: block;
  margin-bottom: 7px;
  color: #b56d32;
  font-size: 11px;
}

.question-basket__copy :deep(button) {
  width: 100%;
}

@media (max-width: 1279px) {
  .question-basket {
    position: static;
    min-height: 0;
    max-height: none;
  }

  .question-basket__items {
    max-height: 260px;
  }
}
</style>
