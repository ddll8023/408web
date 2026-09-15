<!-- 出题工作台题目卡片：替代表格行展示单道模拟题。 -->
<template>
  <article
    class="question-card"
    :class="{ 'question-card--selected': selected }"
  >
    <div class="question-card__select">
      <input
        :checked="selected"
        type="checkbox"
        class="h-4 w-4 cursor-pointer rounded border-gray-300 text-[#8B6F47] focus:ring-2 focus:ring-[#8B6F47] focus:ring-offset-0"
        :aria-label="`选择${displayTitle}`"
        @change="handleSelectionChange"
      >
    </div>

    <div class="question-card__body">
      <div class="question-card__heading">
        <div class="min-w-0 flex-1">
          <button
            type="button"
            class="question-card__title"
            :title="displayTitle"
            @click="handlePreview"
          >
            {{ displayTitle }}
          </button>
        </div>

        <div class="question-card__tags">
          <Tag :type="question.questionType === 'CHOICE' ? 'success' : 'primary'" size="sm">
            {{ question.questionType === 'CHOICE' ? '选择题' : '主观题' }}
          </Tag>
          <Tag v-if="question.difficulty" :type="getDifficultyType(question.difficulty)" size="sm">
            {{ getDifficultyLabel(question.difficulty) }}
          </Tag>
          <Tag :type="question.isExamMarked ? 'success' : 'default'" size="sm">
            {{ question.isExamMarked ? '已出题' : '未出题' }}
          </Tag>
        </div>
      </div>

      <div class="question-card__meta">
        <span>{{ question.source }}</span>
        <span v-if="question.questionNumber != null">第{{ question.questionNumber }}题</span>
        <span v-if="question.updateTime">更新于 {{ formatDateTime(question.updateTime) }}</span>
        <span v-for="category in visibleCategories" :key="category" class="question-card__category">
          {{ category }}
        </span>
      </div>
    </div>

    <div class="question-card__actions">
      <MockExamActionMenu
        :question="question"
        :status-loading="question.examStatusLoading"
        @word-copied="handleWordCopied"
        @toggle-exam-status="handleToggleExamStatus"
      />
      <CustomButton type="text" size="sm" @click="handlePreview">预览</CustomButton>
      <CustomButton type="text-primary" size="sm" @click="emit('edit')">编辑</CustomButton>
    </div>
  </article>
</template>

<script setup lang="ts">
/**
 * 以紧凑索引卡展示单道模拟题，保留原有出题菜单和编辑入口。
 * 卡片只展示题目索引信息，完整 Markdown 内容通过预览抽屉按需渲染。
 */
import { computed, type PropType } from 'vue'
import type { MockQuestion } from '@/types'
import type { RichCopyResult } from '@/utils/questionCopy'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'
import { formatDateTime } from '@/utils/format'
import CustomButton from '@/components/basic/CustomButton.vue'
import Tag from '@/components/basic/Tag.vue'
import MockExamActionMenu from '@/components/business/MockExamActionMenu.vue'

type QuestionCardData = MockQuestion & { examStatusLoading?: boolean }

const props = defineProps({
  question: {
    type: Object as PropType<QuestionCardData>,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits<{
  select: [selected: boolean]
  preview: []
  edit: []
  'word-copied': [result: RichCopyResult]
  'toggle-exam-status': []
}>()

const displayTitle = computed(() => {
  if (props.question.title) return props.question.title
  const number = props.question.questionNumber == null ? '' : `第${props.question.questionNumber}题`
  return [props.question.source, number].filter(Boolean).join(' · ') || `模拟题 ID=${props.question.id}`
})

const visibleCategories = computed(() => {
  return Array.isArray(props.question.category)
    ? props.question.category.filter(Boolean).slice(0, 3)
    : []
})

const handleSelectionChange = (event: Event) => {
  if (!(event.target instanceof HTMLInputElement)) return
  emit('select', event.target.checked)
}

const handleWordCopied = (result: RichCopyResult) => {
  emit('word-copied', result)
}

const handleToggleExamStatus = () => {
  emit('toggle-exam-status')
}

const handlePreview = () => {
  emit('preview')
}
</script>

<style scoped>
.question-card {
  position: relative;
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  align-items: start;
  gap: 14px;
  overflow: hidden;
  border: 1px solid #e8e1d7;
  border-radius: 14px;
  background: rgba(255, 253, 248, 0.92);
  padding: 16px 18px;
  box-shadow: 0 5px 18px rgba(79, 63, 42, 0.05);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.question-card::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: transparent;
  content: '';
  transition: background-color 0.2s ease;
}

.question-card:hover {
  border-color: #d9c6a9;
  box-shadow: 0 9px 24px rgba(79, 63, 42, 0.09);
  transform: translateY(-1px);
}

.question-card--selected {
  border-color: rgba(139, 111, 71, 0.45);
  background: rgba(251, 247, 242, 0.8);
}

.question-card--selected::before {
  background: #8b6f47;
}

.question-card__select {
  display: flex;
  justify-content: center;
  padding-top: 3px;
}

.question-card__heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.question-card__title {
  display: block;
  max-width: 100%;
  overflow: hidden;
  color: #263238;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.5;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question-card__title:hover {
  color: #8b6f47;
}

.question-card__title:focus-visible {
  outline: 2px solid rgba(139, 111, 71, 0.6);
  outline-offset: 3px;
}

.question-card__tags {
  display: flex;
  align-self: center;
  flex: 0 0 auto;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 5px;
}

.question-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 12px;
  margin-top: 12px;
  color: #8a9292;
  font-size: 11px;
}

.question-card__category {
  border-radius: 999px;
  background: rgba(139, 111, 71, 0.08);
  padding: 2px 7px;
  color: #8b6f47;
}

.question-card__actions {
  display: flex;
  align-self: center;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .question-card {
    grid-template-columns: 28px minmax(0, 1fr);
  }

  .question-card__actions {
    grid-column: 2;
    justify-content: flex-start;
    border-top: 1px solid #eee8df;
    padding-top: 8px;
  }
}

@media (max-width: 560px) {
  .question-card {
    gap: 10px;
    padding: 13px;
  }

  .question-card__heading {
    display: block;
  }

  .question-card__tags {
    align-self: auto;
    justify-content: flex-start;
    margin-top: 8px;
  }
}
</style>
