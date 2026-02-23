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
/**
 * 题目条目卡片组件
 * 功能描述：整合 ExamItemHeader 与 ExamQuestionCard 的容器组件
 * 依赖组件：ExamItemHeader, ExamQuestionCard
 * 设计：遵循 KISS/YAGNI 原则，专注题目卡片展示与交互
 */
import ExamItemHeader from '@/components/business/ExamItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'

/**
 * Props 定义
 */
defineProps({
  /** 题目对象 */
  exam: {
    type: Object,
    required: true
  },
  /** 是否显示管理员操作按钮（编辑、删除） */
  isAdmin: {
    type: Boolean,
    default: false
  },
  /** 是否显示答案 */
  showAnswer: {
    type: Boolean,
    default: false
  },
  /** 紧凑密度：compact | comfortable */
  density: {
    type: String,
    default: 'compact'
  }
})

/**
 * Emits 定义
 * @property {Function} copy - 复制题目命令
 * @property {Function} edit - 编辑题目事件
 * @property {Function} delete - 删除题目事件
 * @property {Function} toggle-answer - 切换答案显示
 * @property {Function} answered - 用户作答事件
 */
defineEmits(['copy', 'edit', 'delete', 'toggle-answer', 'answered'])
</script>

<style scoped>
/**
 * 题目条目卡片样式
 * 主要使用Tailwind类名，保留必要的高亮动画效果
 */

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
