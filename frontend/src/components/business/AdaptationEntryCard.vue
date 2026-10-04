<!-- 改编题阅读卡片：展示改编题来源、元信息、题干、选项与答案。 -->
<template>
  <div
    ref="cardRef"
    class="adaptation-entry-card question-immersive-card rounded-xl border border-gray-200 bg-white p-3 md:p-4 scroll-mt-14 md:scroll-mt-8"
    :class="{ 'is-immersive': isImmersive }"
  >
    <AdaptationItemHeader
      :adaptation="adaptation"
      :is-admin="isAdmin"
      :delete-loading="deleteLoading"
      :fullscreen-active="isActive"
      @copy="(command) => $emit('copy', command)"
      @show-sources="$emit('show-sources', adaptation)"
      @edit="$emit('edit', adaptation)"
      @delete="(id) => $emit('delete', id)"
      @toggle-fullscreen="toggleFullscreen"
      @consult="openConsultation"
      @generate-answer="openAnswerGeneration"
    />

    <div>
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
import { ref, type PropType } from 'vue'
import type { AdaptationQuestion } from '@/types'
import AdaptationItemHeader from '@/components/business/AdaptationItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'
import { useAiConsultationPanel } from '@/composables/useAiConsultationPanel'
import { useQuestionFullscreen } from '@/composables/useQuestionFullscreen'
import { useToast } from '@/composables/useToast'

const props = defineProps({
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

const emit = defineEmits<{
  copy: [command: string]
  'show-sources': [question: AdaptationQuestion]
  edit: [question: AdaptationQuestion]
  delete: [id: number]
  'toggle-answer': []
  'generate-answer': [question: AdaptationQuestion]
  answered: [payload: { optionKey: string; correct: boolean }]
}>()

/** 卡片根元素，同时作为全屏目标 */
const cardRef = ref<HTMLElement | null>(null)

/** 单题全屏与沉浸状态 */
const { isActive, isImmersive, toggleFullscreen, exit } = useQuestionFullscreen(cardRef)

const { showToast } = useToast()

const { openQuestion } = useAiConsultationPanel()

/** 生成对比与编辑均使用普通视口；退出失败时不发起模型请求。 */
async function openAnswerGeneration(): Promise<void> {
  if (!props.isAdmin) return
  await exit()
  if (isActive.value) {
    showToast('请先手动退出全屏再生成答案', 'warning')
    return
  }
  emit('generate-answer', props.adaptation)
}

/** 退出全屏或沉浸失败时不打开咨询，也不发起任何模型请求。 */
async function openConsultation(): Promise<void> {
  await exit()
  if (isActive.value) {
    showToast('请先手动退出全屏再打开 AI 咨询', 'warning')
    return
  }
  const adaptation = props.adaptation
  await openQuestion('adaptation', adaptation.id, `改编题 #${adaptation.id} · ${adaptation.sourceSummary || '未标注来源'}`)
}
</script>

<style scoped>
/*
 * 改编题卡片样式。
 * 模块识别交给头部标题配色，卡片本身只保留统一的中性外框。
 */

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
