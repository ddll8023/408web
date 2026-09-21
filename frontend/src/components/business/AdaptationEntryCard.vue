<!-- 改编题阅读卡片：展示改编题来源、元信息、题干、选项与答案。 -->
<template>
  <div class="adaptation-entry-card rounded-lg border border-gray-300 bg-white p-4 transition-all hover:border-accent/30 hover:shadow-md md:p-6 scroll-mt-14 md:scroll-mt-8">
    <AdaptationItemHeader
      :adaptation="adaptation"
      :is-admin="isAdmin"
      :delete-loading="deleteLoading"
      @copy="(command) => $emit('copy', command)"
      @show-sources="$emit('show-sources', adaptation)"
      @edit="$emit('edit', adaptation)"
      @delete="(id) => $emit('delete', id)"
    />

    <div class="mt-6">
      <ExamQuestionCard
        :exam="adaptation"
        :show-answer="showAnswer"
        :density="density"
        @toggle-answer="$emit('toggle-answer')"
        @answered="(payload) => $emit('answered', payload)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 改编题阅读卡片。
 * 头部只负责展示改编题元信息，题目内容与答案交给通用题目卡片渲染。
 */
import type { PropType } from 'vue'
import type { AdaptationQuestion } from '@/types'
import AdaptationItemHeader from '@/components/business/AdaptationItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'

defineProps({
  adaptation: {
    type: Object as PropType<AdaptationQuestion>,
    required: true
  },
  showAnswer: {
    type: Boolean,
    default: false
  },
  density: {
    type: String,
    default: 'compact'
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  deleteLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits<{
  copy: [command: string]
  'show-sources': [question: AdaptationQuestion]
  edit: [question: AdaptationQuestion]
  delete: [id: number]
  'toggle-answer': []
  answered: [payload: { optionKey: string; correct: boolean }]
}>()
</script>

<style scoped>
.adaptation-entry-card:global(.highlight-card) {
  animation: highlightPulse 2s ease-out;
  border-color: var(--brand-accent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--brand-accent) 30%, transparent);
}

@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 0 20px color-mix(in srgb, var(--brand-accent) 30%, transparent);
  }
  50% {
    box-shadow: 0 0 30px color-mix(in srgb, var(--brand-accent) 50%, transparent);
  }
}
</style>
