<template>
  <!-- 模拟题卡片组件：与 ExamEntryCard 保持样式一致 -->
  <div class="mock-entry-card">
    <!-- 题目头部 -->
    <MockItemHeader 
      :mock="mock"
      :is-admin="isAdmin"
      @copy="(cmd) => $emit('copy', cmd)"
      @edit="$emit('edit', mock)"
      @delete="(id) => $emit('delete', id)"
    />
    <!-- 题目内容与答案 -->
    <div class="mock-entry-content">
      <ExamQuestionCard
        :exam="mock"
        :show-answer="showAnswer"
        :density="density"
        @toggle-answer="$emit('toggle-answer')"
      />
    </div>
  </div>
</template>

<script setup>
/**
 * 模拟题卡片组件
 * 结构与 ExamEntryCard 一致
 * 使用 MockItemHeader 显示模拟题特有的标题格式
 */
import MockItemHeader from '@/components/business/MockItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'

defineProps({
  mock: { type: Object, required: true },
  isAdmin: { type: Boolean, default: false },
  showAnswer: { type: Boolean, default: false },
  density: { type: String, default: 'compact' }
})

defineEmits(['copy', 'edit', 'delete', 'toggle-answer'])
</script>

<style scoped>
/* 样式与 ExamEntryCard 保持一致 */
.mock-entry-card {
  padding: 24px;
  border-radius: 4px;
  border: 1px solid #dfe2e5;
  scroll-margin-top: 32px;
  transition: all 0.3s ease;
}

.mock-entry-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-color: rgba(139, 111, 71, 0.3);
}

/* 高亮效果（从管理页面跳转时） */
.mock-entry-card:global(.highlight-card) {
  animation: highlightPulse 2s ease-out;
  border-color: #8B6F47;
  box-shadow: 0 0 20px rgba(139, 111, 71, 0.3);
}

.mock-entry-card .mock-entry-content {
  margin-top: 24px;
}

@keyframes highlightPulse {
  0%, 100% { box-shadow: 0 0 20px rgba(139, 111, 71, 0.3); }
  50% { box-shadow: 0 0 30px rgba(139, 111, 71, 0.5); }
}

@media (max-width: 768px) {
  .mock-entry-card {
    padding: 16px;
  }
}
</style>
