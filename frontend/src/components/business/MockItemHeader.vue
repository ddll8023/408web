<!-- 模拟题头部：展示来源标题、题号、元信息和操作，复用题库阅读卡片的视觉层级。 -->
<template>
  <div class="mock-item-header flex items-start justify-between gap-4 mb-3 pb-3 border-b border-gray-100">
    <div class="min-w-0 flex-1">
      <h3 v-if="mock.questionNumber || mock.title" class="question-title m-0 flex flex-wrap items-baseline gap-x-2 gap-y-1 font-semibold">
        <span v-if="mock.title" class="min-w-0">{{ mock.title }}</span>
        <span v-if="mock.questionNumber && mock.title" class="title-separator text-gray-400 font-normal" aria-hidden="true">·</span>
        <span v-if="mock.questionNumber" class="question-number">第{{ mock.questionNumber }}题</span>
      </h3>
      <div class="question-metadata mt-2 flex flex-wrap gap-1.5">
        <Tag class="question-tag" size="sm" :type="mock.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ mock.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </Tag>
        <Tag v-if="mock.difficulty" class="question-tag" size="sm" :type="getDifficultyType(mock.difficulty)">
          {{ getDifficultyLabel(mock.difficulty) }}
        </Tag>
        <Tag
          v-for="cat in (Array.isArray(mock.category) ? mock.category : [])"
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
        type="text-primary"
        title="AI 咨询本题"
        aria-label="AI 咨询本题"
        @click="$emit('consult')"
      >
        AI 咨询
      </CustomButton>
      <CustomButton
        size="sm"
        type="text"
        :icon="['fas', fullscreenActive ? 'compress' : 'expand']"
        :title="fullscreenActive ? '退出全屏' : '全屏查看本题'"
        :aria-label="fullscreenActive ? '退出全屏' : '全屏查看本题'"
        @click="$emit('toggle-fullscreen')"
      />
      <template v-if="!fullscreenActive">
        <!-- 公共复制菜单组件 -->
        <QuestionCopyMenu :question="mock" @copy="(command) => $emit('copy', command)" />
        <!-- 管理员操作 -->
        <template v-if="isAdmin">
          <CustomButton size="sm" type="text" @click="$emit('edit', mock)">编辑</CustomButton>
          <CustomButton size="sm" type="text" @click="$emit('delete', mock.id)">删除</CustomButton>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { MockQuestion } from '@/types'
/**
 * 模拟题头部组件
 * 与 ExamItemHeader 保持样式一致，但标题格式适配模拟题
 * 格式: {title} · 第{questionNumber}题
 */
import CustomButton from '@/components/basic/CustomButton.vue'
import QuestionCopyMenu from '@/components/business/QuestionCopyMenu.vue'
import Tag from '@/components/basic/Tag.vue'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'

defineProps({
  mock: { type: Object as PropType<MockQuestion>, required: true },
  isAdmin: { type: Boolean, default: false },
  /** 当前卡片是否处于全屏或沉浸模式 */
  fullscreenActive: { type: Boolean, default: false }
})

defineEmits<{ copy: [command: string]; edit: [question: MockQuestion]; delete: [id: number]; 'toggle-fullscreen': []; consult: [] }>()
</script>

<style scoped>
.question-title {
  font-size: 18px;
  line-height: 1.5;
  /* 标题取模拟题主题色，与分类标题和卡片色条共同区分三个题库。 */
  color: var(--theme-mock-accent);
  overflow-wrap: anywhere;
}

/* 元信息使用中性底色，让来源标题和题干成为阅读重点。 */
.question-metadata :deep(.question-tag) {
  color: var(--brand-ink-soft);
  background-color: #f4f5f6;
}

.question-actions {
  max-width: 100%;
}

@media (max-width: 767px) {
  .mock-item-header {
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
