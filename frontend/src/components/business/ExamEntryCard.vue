<!-- 真题卡片：组合题目头部与题目正文，预留窄屏吸顶导航的锚点偏移。 -->
<template>
  <div
    ref="cardRef"
    class="exam-entry-card question-immersive-card rounded-xl border border-gray-200 bg-white p-3 md:p-4 scroll-mt-14 md:scroll-mt-8"
    :class="{ 'is-immersive': isImmersive }"
  >
    <!-- 题目头部：包含题号、元数据、操作按钮 -->
    <ExamItemHeader
      :exam="exam"
      :is-admin="isAdmin"
      :fullscreen-active="isActive"
      @copy="(cmd) => $emit('copy', cmd)"
      @edit="$emit('edit', exam)"
      @delete="(id) => $emit('delete', id)"
      @show-adaptations="$emit('show-adaptations', exam)"
      @toggle-fullscreen="toggleFullscreen"
      @consult="openConsultation"
      @generate-answer="openAnswerGeneration"
    />

    <!-- 题目内容与答案卡片 -->
    <div>
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

<script setup lang="ts">
import { ref, type PropType } from 'vue'
import type { ExamQuestion } from '@/types'
/**
 * 题目条目卡片组件
 * 功能描述：整合 ExamItemHeader 与 ExamQuestionCard 的容器组件
 * 依赖组件：ExamItemHeader, ExamQuestionCard
 * 设计：遵循 KISS/YAGNI 原则，专注题目卡片展示与交互
 */
import ExamItemHeader from '@/components/business/ExamItemHeader.vue'
import ExamQuestionCard from '@/components/business/ExamQuestionCard.vue'
import { useAiConsultationPanel } from '@/composables/useAiConsultationPanel'
import { useQuestionFullscreen } from '@/composables/useQuestionFullscreen'
import { useToast } from '@/composables/useToast'

/**
 * Props 定义
 */
const props = defineProps({
  /** 题目对象 */
  exam: {
    type: Object as PropType<ExamQuestion>,
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
const emit = defineEmits<{
  copy: [command: string]
  edit: [question: ExamQuestion]
  delete: [id: number]
  'show-adaptations': [question: ExamQuestion]
  'toggle-answer': []
  'generate-answer': [question: ExamQuestion]
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
  emit('generate-answer', props.exam)
}

/** 退出全屏或沉浸失败时不打开咨询，也不发起任何模型请求。 */
async function openConsultation(): Promise<void> {
  await exit()
  if (isActive.value) {
    showToast('请先手动退出全屏再打开 AI 咨询', 'warning')
    return
  }
  const exam = props.exam
  const label = exam.questionNumber != null
    ? `${exam.year}年 第${exam.questionNumber}题`
    : `${exam.year}年 真题 #${exam.id}`
  await openQuestion('exam', exam.id, label)
}
</script>

<style scoped>
/*
 * 真题卡片样式。
 * 模块识别交给头部标题配色，卡片本身只保留统一的中性外框。
 */

/* 从管理页面"查看"按钮跳转过来时的高亮效果 */
.exam-entry-card:global(.highlight-card) {
  animation: highlightPulse 2s ease-out;
  border-color: var(--brand-accent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--brand-accent) 30%, transparent);
}

/* 高亮脉冲动画 */
@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 0 20px color-mix(in srgb, var(--brand-accent) 30%, transparent);
  }
  50% {
    box-shadow: 0 0 30px color-mix(in srgb, var(--brand-accent) 50%, transparent);
  }
}
</style>
