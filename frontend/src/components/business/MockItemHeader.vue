<template>
  <!-- 模拟题头部组件：显示标题、题号、元数据、操作按钮 -->
  <div class="flex items-center justify-between mb-6 pb-4 border-b border-black/[0.03]">
    <div class="flex-1">
      <h3 v-if="mock.questionNumber || mock.title" class="text-lg font-semibold text-gray-800 flex items-center gap-3 m-0">
        <span v-if="mock.title">{{ mock.title }}</span>
        <span v-if="mock.questionNumber && mock.title" class="title-separator text-gray-400 font-normal">·</span>
        <span v-if="mock.questionNumber" class="question-number text-[#8B6F47] font-mono">第{{ mock.questionNumber }}题</span>
      </h3>
      <div class="flex gap-2 flex-wrap mt-2">
        <Tag :variant="mock.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ mock.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </Tag>
        <Tag v-if="mock.difficulty" :variant="getDifficultyType(mock.difficulty)">
          {{ getDifficultyLabel(mock.difficulty) }}
        </Tag>
        <Tag
          v-for="cat in (Array.isArray(mock.category) ? mock.category : [])"
          :key="cat"
          variant="info"
        >
          {{ cat }}
        </Tag>
      </div>
    </div>
    <div class="flex gap-1 opacity-80 transition-opacity duration-200 hover:opacity-100">
      <!-- 公共复制菜单组件 -->
      <QuestionCopyMenu :question="mock" @copy="(command) => $emit('copy', command)" />
      <!-- 管理员操作 -->
      <template v-if="isAdmin">
        <CustomButton size="sm" type="text" @click="$emit('edit', mock)">编辑</CustomButton>
        <CustomButton size="sm" type="text" @click="$emit('delete', mock.id)">删除</CustomButton>
      </template>
    </div>
  </div>
</template>

<script setup>
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
  mock: { type: Object, required: true },
  isAdmin: { type: Boolean, default: false }
})

defineEmits(['copy', 'edit', 'delete'])
</script>

<style scoped>
/**
 * 模拟题头部组件样式
 * 与 ExamItemHeader 保持一致
 */

.question-title .question-subtitle {
  margin-left: 12px;
  font-size: 16px;
  font-weight: 400;
  color: #999;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .exam-item-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .question-title {
    font-size: 14px;
  }

  .question-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
