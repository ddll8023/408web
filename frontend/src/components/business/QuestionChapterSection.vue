<!-- 出题工作台章节分组：以章节卡片承载题目卡片列表。 -->
<template>
  <section :id="`chapter-section-${section.id}`" class="question-chapter-section">
    <header class="question-chapter-section__header">
      <div class="min-w-0">
        <p v-if="section.path.length > 1" class="question-chapter-section__path">
          {{ section.path.slice(0, -1).join(' / ') }}
        </p>
        <h2 class="question-chapter-section__title">{{ section.name }}</h2>
      </div>
      <div class="question-chapter-section__summary">
        <span>{{ section.questions.length }} 题</span>
        <span v-if="selectedInSection > 0" class="question-chapter-section__selected">
          已选 {{ selectedInSection }}
        </span>
        <CustomButton
          type="text"
          size="sm"
          :disabled="section.questions.length === 0"
          @click="handleSelectAll"
        >
          {{ allSelected ? '取消本组' : '全选当前组' }}
        </CustomButton>
      </div>
    </header>

    <div class="question-chapter-section__list">
      <QuestionCard
        v-for="question in section.questions"
        :key="question.id"
        :question="question"
        :selected="selectedSet.has(question.id)"
        @select="selected => handleQuestionSelect(question, selected)"
        @preview="handleQuestionPreview(question)"
        @edit="handleQuestionEdit(question)"
        @word-copied="result => handleQuestionWordCopied(question, result)"
        @toggle-exam-status="handleQuestionStatusToggle(question)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
/**
 * 章节题目分组组件。
 * 负责章节头部、组内全选和题目卡片事件转发，不管理跨章节选择状态。
 */
import { computed, type PropType } from 'vue'
import type { MockQuestion } from '@/types'
import type { RichCopyResult } from '@/utils/questionCopy'
import CustomButton from '@/components/basic/CustomButton.vue'
import QuestionCard from '@/components/business/QuestionCard.vue'

type QuestionRow = MockQuestion & { examStatusLoading?: boolean }

interface QuestionChapterSectionData {
  id: number
  name: string
  path: string[]
  questions: QuestionRow[]
}

const props = defineProps({
  section: {
    type: Object as PropType<QuestionChapterSectionData>,
    required: true,
  },
  selectedIds: {
    type: Array as PropType<readonly number[]>,
    default: () => [],
  },
})

const emit = defineEmits<{
  'select-question': [question: QuestionRow, selected: boolean]
  'preview': [question: QuestionRow]
  'edit': [question: QuestionRow]
  'word-copied': [question: QuestionRow, result: RichCopyResult]
  'toggle-exam-status': [question: QuestionRow]
}>()

const selectedSet = computed(() => new Set(props.selectedIds))
const selectedInSection = computed(() => props.section.questions.filter(question => selectedSet.value.has(question.id)).length)
const allSelected = computed(() => {
  return props.section.questions.length > 0 && selectedInSection.value === props.section.questions.length
})

const handleSelectAll = () => {
  if (props.section.questions.length === 0) return
  const selected = !allSelected.value
  props.section.questions.forEach(question => emit('select-question', question, selected))
}

const handleQuestionSelect = (question: QuestionRow, selected: boolean) => {
  emit('select-question', question, selected)
}

const handleQuestionPreview = (question: QuestionRow) => {
  emit('preview', question)
}

const handleQuestionEdit = (question: QuestionRow) => {
  emit('edit', question)
}

const handleQuestionWordCopied = (question: QuestionRow, result: RichCopyResult) => {
  emit('word-copied', question, result)
}

const handleQuestionStatusToggle = (question: QuestionRow) => {
  emit('toggle-exam-status', question)
}
</script>

<style scoped>
.question-chapter-section {
  border: 1px solid #e6ded2;
  border-radius: 18px;
  background: rgba(255, 253, 248, 0.68);
  padding: 16px;
}

.question-chapter-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  border-bottom: 1px solid #eee7dc;
  padding: 2px 3px 13px;
}

.question-chapter-section__path {
  margin: 0 0 3px;
  color: #9a8a76;
  font-size: 11px;
  line-height: 1.3;
}

.question-chapter-section__title {
  margin: 0;
  color: #344047;
  font-size: 17px;
  font-weight: 750;
  letter-spacing: 0.01em;
}

.question-chapter-section__summary {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
  color: #88908f;
  font-size: 12px;
}

.question-chapter-section__selected {
  border-radius: 999px;
  background: rgba(139, 111, 71, 0.12);
  padding: 3px 8px;
  color: #8b6f47;
  font-weight: 700;
}

.question-chapter-section__list {
  display: grid;
  gap: 10px;
  padding-top: 13px;
}

@media (max-width: 640px) {
  .question-chapter-section__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .question-chapter-section__summary {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
