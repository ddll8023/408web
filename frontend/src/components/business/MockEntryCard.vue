<template>
  <!-- 模拟题卡片组件：与 ExamEntryCard 保持样式一致 -->
  <div class="
    bg-white
    border border-gray-200
    rounded-lg
    shadow-sm
    p-4 sm:p-6
    cursor-pointer
    hover:shadow-md
    transition-all duration-300
    scroll-mt-8
  ">
    <!-- 题目头部 -->
    <MockItemHeader
      :mock="mock"
      :is-admin="isAdmin"
      @copy="(cmd) => $emit('copy', cmd)"
      @edit="$emit('edit', mock)"
      @delete="(id) => $emit('delete', id)"
    />
    <!-- 题目内容与答案 -->
    <div class="mt-6">
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
 * 功能描述：整合 MockItemHeader 与 ExamQuestionCard 的容器组件
 * 依赖组件：MockItemHeader, ExamQuestionCard
 * 设计：遵循 KISS/YAGNI 原则，专注模拟题卡片展示与交互
 */
import MockItemHeader from '@/components/business/MockItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'

/**
 * Props 定义
 */
defineProps({
  /** 模拟题对象 */
  mock: {
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
 */
defineEmits(['copy', 'edit', 'delete', 'toggle-answer'])
</script>

<style scoped>
/**
 * 模拟题卡片样式
 * 主要使用Tailwind类名，保留必要的高亮动画效果
 */

/* 高亮效果（从管理页面跳转时） - 需要保留全局选择器样式 */
.mock-entry-card:global(.highlight-card) {
  animation: highlightPulse 2s ease-out;
  border-color: #8B6F47;
  box-shadow: 0 0 20px rgba(139, 111, 71, 0.3);
}

@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(139, 111, 71, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba(139, 111, 71, 0.5);
  }
}

@media (max-width: 768px) {
  /* 响应式样式已通过 Tailwind 的 sm: 前缀处理 */
}
</style>
