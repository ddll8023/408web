<template>
  <!-- 模拟题头部组件：显示标题、题号、元数据、操作按钮 -->
  <div class="mock-item-header flex items-center justify-between mb-6 pb-4 border-b border-black/[0.03]">
    <div class="question-info flex-1">
      <h3 v-if="mock.questionNumber || mock.title" class="question-title m-0 text-lg text-gray-800 font-semibold flex items-center gap-2">
        <span v-if="mock.title">{{ mock.title }}</span>
        <span v-if="mock.questionNumber && mock.title" class="title-separator text-gray-400 font-normal">·</span>
        <span v-if="mock.questionNumber" class="question-number text-[#8B6F47] font-mono">第{{ mock.questionNumber }}题</span>
      </h3>
      <div class="question-meta flex gap-2 flex-wrap mt-2">
        <el-tag size="small" :type="mock.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ mock.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </el-tag>
        <el-tag v-if="mock.difficulty" size="small" :type="getDifficultyType(mock.difficulty)">
          {{ getDifficultyLabel(mock.difficulty) }}
        </el-tag>
        <el-tag
          v-for="cat in (Array.isArray(mock.category) ? mock.category : [])"
          :key="cat"
          size="small"
          type="info"
        >
          {{ cat }}
        </el-tag>
      </div>
    </div>
    <div class="question-actions flex gap-1 opacity-80 transition-opacity duration-200 hover:opacity-100 flex-shrink-0">
      <!-- 公共复制菜单组件 -->
      <QuestionCopyMenu :question="mock" @copy="(command) => $emit('copy', command)" />
      <!-- 管理员操作 -->
      <template v-if="isAdmin">
        <CustomButton size="small" type="text" @click="$emit('edit', mock)">编辑</CustomButton>
        <CustomButton size="small" type="text" @click="$emit('delete', mock.id)">删除</CustomButton>
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
 * 使用纯CSS样式，兼容Tailwind CSS 4
 */

/* 样式与 ExamItemHeader 保持一致 - 使用Tailwind类名在template中已实现 */

/* 响应式布局 */
@media (max-width: 768px) {
  .mock-item-header {
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
