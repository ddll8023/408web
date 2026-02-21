<template>
  <div class="exam-item-header flex items-center justify-between mb-6 pb-4 border-b border-black/[0.03]">
    <div class="question-info flex-1">
      <h3 class="question-title m-0 text-lg text-gray-800 font-semibold flex items-center gap-3">
        <span class="question-number text-[#8B6F47] font-mono">{{ exam.year }}年 第 {{ exam.questionNumber }} 题</span>
      </h3>
      <div class="question-meta flex gap-2 flex-wrap mt-2">
        <el-tag size="small" :type="exam.questionType === 'CHOICE' ? 'success' : 'primary'">
          {{ exam.questionType === 'CHOICE' ? '选择题' : '主观题' }}
        </el-tag>
        <el-tag
          v-for="cat in (Array.isArray(exam.category) ? exam.category : [])"
          :key="cat"
          size="small"
          type="info"
        >
          {{ cat }}
        </el-tag>
      </div>
    </div>
    <div class="question-actions flex gap-1 opacity-80 transition-opacity duration-200 hover:opacity-100">
      <!-- 公共复制菜单组件 -->
      <QuestionCopyMenu :question="exam" @copy="(command) => $emit('copy', command)" />
      <template v-if="isAdmin">
        <CustomButton size="sm" type="text" @click="$emit('edit', exam)">编辑</CustomButton>
        <CustomButton size="sm" type="text" @click="$emit('delete', exam.id)">删除</CustomButton>
      </template>
    </div>
  </div>
</template>

<script setup>
import CustomButton from '@/components/basic/CustomButton.vue'
import QuestionCopyMenu from '@/components/business/QuestionCopyMenu.vue'

defineProps({
  exam: {
    type: Object,
    required: true
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

defineEmits(['copy', 'edit', 'delete'])
</script>

<style scoped>
/**
 * 题目头部组件样式
 * 使用纯CSS样式，兼容Tailwind CSS 4
 */

/* 头部容器 - 使用Tailwind类名在template中已实现 */

/* 标题 - 使用Tailwind类名在template中已实现 */

.question-title .question-subtitle {
  margin-left: 12px;
  font-size: 16px;
  font-weight: 400;
  color: #999;
}

/* 元数据 - 使用Tailwind类名在template中已实现 */

/* 操作按钮 - 使用Tailwind类名在template中已实现 */

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
