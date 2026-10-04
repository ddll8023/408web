<!-- 模拟题卡片：组合题目头部与题目正文，预留窄屏吸顶导航的锚点偏移，与 ExamEntryCard 保持样式一致。 -->
<template>
  <div
    ref="cardRef"
    class="mock-entry-card question-immersive-card rounded-xl border border-gray-200 bg-white p-3 md:p-4 scroll-mt-14 md:scroll-mt-8"
    :class="{ 'is-immersive': isImmersive }"
  >
    <!-- 题目头部 -->
    <MockItemHeader
      :mock="mock"
      :is-admin="isAdmin"
      :fullscreen-active="isActive"
      @copy="(cmd) => $emit('copy', cmd)"
      @edit="$emit('edit', mock)"
      @delete="(id) => $emit('delete', id)"
      @toggle-fullscreen="toggleFullscreen"
      @consult="openConsultation"
      @generate-answer="openAnswerGeneration"
    />
    <!-- 题目内容与答案 -->
    <div>
      <ExamQuestionCard
        :exam="mock"
        :show-answer="showAnswer"
        :density="density"
        @toggle-answer="$emit('toggle-answer')"
        @answered="(payload) => $emit('answered', payload)"
      />
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, type PropType } from 'vue'
import type { MockQuestion } from '@/types'
/**
 * 模拟题卡片组件
 * 功能描述：整合 MockItemHeader 与 ExamQuestionCard 的容器组件
 * 依赖组件：MockItemHeader, ExamQuestionCard
 * 设计：遵循 KISS/YAGNI 原则，专注模拟题卡片展示与交互
 */
import MockItemHeader from '@/components/business/MockItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'
import { useAiConsultationPanel } from '@/composables/useAiConsultationPanel'
import { useQuestionFullscreen } from '@/composables/useQuestionFullscreen'
import { useToast } from '@/composables/useToast'

/**
 * Props 定义
 */
const props = defineProps({
  /** 模拟题对象 */
  mock: {
    type: Object as PropType<MockQuestion>,
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
const emit = defineEmits<{ 'generate-answer': [question: MockQuestion]; copy: [command: string]; edit: [question: MockQuestion]; delete: [id: number]; 'toggle-answer': []; answered: [payload: { optionKey: string; correct: boolean }] }>()

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
  emit('generate-answer', props.mock)
}

/** 退出全屏或沉浸失败时不打开咨询，也不发起任何模型请求。 */
async function openConsultation(): Promise<void> {
  await exit()
  if (isActive.value) {
    showToast('请先手动退出全屏再打开 AI 咨询', 'warning')
    return
  }
  const mock = props.mock
  const number = mock.questionNumber != null ? `第${mock.questionNumber}题` : `#${mock.id}`
  await openQuestion('mock', mock.id, `模拟题 · ${mock.title || mock.source} · ${number}`)
}
</script>

<style scoped>
/*
 * 模拟题卡片样式。
 * 模块识别交给头部标题配色，卡片本身只保留统一的中性外框。
 */

/* 高亮效果（从管理页面跳转时） - 需要保留全局选择器样式 */
.mock-entry-card:global(.highlight-card) {
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

@media (max-width: 767px) {
  /* 响应式样式已通过 Tailwind 的 sm: 前缀处理 */
}
</style>
