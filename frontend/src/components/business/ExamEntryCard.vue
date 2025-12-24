<template>
  <div class="exam-entry-card">
    <!-- 题目头部：包含题号、元数据、操作按钮 -->
    <ExamItemHeader 
      :exam="exam"
      :is-admin="isAdmin"
      @copy="(cmd) => $emit('copy', cmd)"
      @edit="$emit('edit', exam)"
      @delete="(id) => $emit('delete', id)"
    />

    <!-- 题目内容与答案卡片 -->
    <div class="exam-entry-content">
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

<style lang="scss" scoped>
.exam-entry-card {
  padding: $spacing-md;
  border-radius: $border-radius-base;
  border: 1px solid $color-border-light;
  scroll-margin-top: $spacing-lg;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    border-color: rgba($color-accent, 0.3);
  }
  
  // 从管理页面"查看"按钮跳转过来时的高亮效果
  &:global(.highlight-card) {
    animation: highlightPulse 2s ease-out;
    border-color: $color-accent;
    box-shadow: 0 0 20px rgba($color-accent, 0.3);
  }

  .exam-entry-content {
    margin-top: $spacing-md;
  }
}

// 高亮脉冲动画
@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba($color-accent, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba($color-accent, 0.5);
  }
}

/* 移动端适配 */
@include mobile {
  .exam-entry-card {
    padding: $spacing-sm;
  }
}
</style>
