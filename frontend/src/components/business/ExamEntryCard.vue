<template>
  <div class="bg-white rounded-lg border border-gray-300 p-4 md:p-6 scroll-mt-8 transition-all hover:shadow-md hover:border-[rgba(139,111,71,0.3)]">
    <!-- 题目头部：包含题号、元数据、操作按钮 -->
    <ExamItemHeader
      :exam="exam"
      :is-admin="isAdmin"
      @copy="(cmd) => $emit('copy', cmd)"
      @edit="$emit('edit', exam)"
      @delete="(id) => $emit('delete', id)"
    />

    <!-- 题目内容与答案卡片 -->
    <div class="mt-6">
      <ExamQuestionCard
        :exam="exam"
        :show-answer="showAnswer"
        :density="density"
        @toggle-answer="$emit('toggle-answer')"
        @answered="(payload) => $emit('answered', payload)"
      />
    </div>
  </div>
</template>

<script setup>
import ExamItemHeader from '@/components/business/ExamItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'

defineProps({
  exam: {
    type: Object,
    required: true
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  showAnswer: {
    type: Boolean,
    default: false
  },
  showHeader: {
    type: Boolean,
    default: true
  },
  density: {
    type: String,
    default: 'compact'
  }
})

defineEmits(['copy', 'edit', 'delete', 'toggle-answer', 'answered'])
</script>

<style scoped>
/* 从管理页面"查看"按钮跳转过来时的高亮效果 */
.exam-entry-card:global(.highlight-card) {
  animation: highlightPulse 2s ease-out;
  border-color: #8B6F47;
  box-shadow: 0 0 20px rgba(139, 111, 71, 0.3);
}

/* 高亮脉冲动画 */
@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(139, 111, 71, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba(139, 111, 71, 0.5);
  }
}
</style>
