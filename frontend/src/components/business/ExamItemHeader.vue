<!-- 真题题目头部：展示题目元信息、复制、过程图片和管理员操作。 -->
<template>
  <div class="exam-item-header flex items-start justify-between gap-4 mb-3 pb-3 border-b border-gray-100">
    <div class="min-w-0 flex-1">
      <h3 class="question-title m-0 font-semibold">
        {{ exam.year }}年 第 {{ exam.questionNumber }} 题
      </h3>
      <div class="question-metadata mt-2 flex flex-wrap gap-1.5">
        <Tag class="question-tag" size="sm" :type="exam.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ exam.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </Tag>
        <Tag v-if="exam.difficulty" class="question-tag" size="sm" :type="getDifficultyType(exam.difficulty)">
          {{ getDifficultyLabel(exam.difficulty) }}
        </Tag>
        <Tag
          v-for="cat in (Array.isArray(exam.category) ? exam.category : [])"
          :key="cat"
          class="question-tag"
          size="sm"
          type="info"
        >
          {{ cat }}
        </Tag>
      </div>
    </div>
    <div class="question-actions flex shrink-0 flex-wrap items-center gap-1">
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', fullscreenActive ? 'compress' : 'expand']"
        :title="fullscreenActive ? '退出全屏' : '全屏查看本题'"
        :aria-label="fullscreenActive ? '退出全屏' : '全屏查看本题'"
        @click="$emit('toggle-fullscreen')"
      />
      <template v-if="!fullscreenActive">
        <CustomButton
          v-if="exam.questionNumber != null"
          size="sm"
          type="text-primary"
          title="查看关联改编题"
          @click="$emit('show-adaptations', exam)"
        >
          改编
        </CustomButton>
        <QuestionCopyMenu :question="exam" @copy="(command) => $emit('copy', command)" />
        <ExamProcessMenu :exam="exam" :is-admin="isAdmin" />
        <template v-if="isAdmin">
          <CustomButton size="sm" type="text" @click="$emit('edit', exam)">编辑</CustomButton>
          <CustomButton size="sm" type="text" @click="$emit('delete', exam.id)">删除</CustomButton>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { ExamQuestion } from '@/types'
/**
 * 题目头部组件
 * 功能描述：显示题目年份、题号、类型/难度/分类标签和操作按钮
 * 依赖组件：CustomButton, QuestionCopyMenu, ExamProcessMenu, Tag
 */

// 1. 子组件导入
import CustomButton from '@/components/basic/CustomButton.vue'
import QuestionCopyMenu from '@/components/business/QuestionCopyMenu.vue'
import ExamProcessMenu from '@/components/business/ExamProcessMenu.vue'
import Tag from '@/components/basic/Tag.vue'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'

// 2. Props 定义
defineProps({
  exam: {
    type: Object as PropType<ExamQuestion>,
    required: true
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  /** 当前卡片是否处于全屏或沉浸模式 */
  fullscreenActive: {
    type: Boolean,
    default: false
  }
})

// 3. Emits 定义
defineEmits<{
  copy: [command: string]
  edit: [question: ExamQuestion]
  delete: [id: number]
  'show-adaptations': [question: ExamQuestion]
  'toggle-fullscreen': []
}>()
</script>

<style scoped>
.question-title {
  font-size: 18px;
  line-height: 1.5;
  /* 标题取题目所属题库的主题色，与分类标题和卡片色条共同区分三个题库。 */
  color: var(--theme-exam-accent);
  overflow-wrap: anywhere;
}

/* 元信息使用中性底色，让年份题号和题干成为阅读重点。 */
.question-metadata :deep(.question-tag) {
  color: var(--brand-ink-soft);
  background-color: #f4f5f6;
}

.question-actions {
  max-width: 100%;
}

@media (max-width: 767px) {
  .exam-item-header {
    flex-direction: column;
    gap: 12px;
  }

  .question-title {
    font-size: 16px;
  }

  .question-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
