<!-- 答案生成对比窗：打开只展示原答案，手动开始才调用模型；采用只交给编辑框，不直接保存题库。 -->
<template>
  <ResponsiveDialog
    :visible="visible"
    title="AI 生成答案 · 对比后采用"
    width="1380px"
    max-width="1500px"
    max-height="88dvh"
    @update:visible="handleVisibility"
  >
    <div class="answer-review" :aria-busy="working || busy">
      <p class="m-0 mb-2 text-sm font-medium text-ink">{{ questionKind === 'exam' ? '真题' : questionKind === 'mock' ? '模拟题' : '改编题' }} #{{ questionId }}</p>
      <p class="m-0 mb-3 text-sm text-gray-500">点击“开始生成”后才会调用模型，仅发送题面，不提供原答案；生成可能消耗模型额度。采用后仍需在编辑框点击保存。</p>
      <p v-if="session" class="m-0 mb-3 text-xs text-gray-500">{{ session.model.name }} · {{ session.contextNote }}</p>
      <p v-if="failure" class="mb-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{{ failure }}</p>
      <p v-if="stale" class="mb-3 rounded-md bg-amber-50 p-3 text-sm text-amber-800" role="status">题面或原答案已变化，请重新生成后再采用。</p>
      <div class="review-columns">
        <section class="review-pane">
          <header class="review-label"><span>{{ draft ? '当前编辑答案' : '题库原答案' }}</span><span class="review-caption">保留至你确认保存</span></header>
          <div class="review-content">
            <AiGeneratedAnswerViewer v-if="baseline?.answer" :content="baseline.answer" />
            <p v-else class="text-sm text-gray-400">暂无原答案</p>
          </div>
        </section>
        <section class="review-pane review-pane--candidate">
          <header class="review-label"><span>AI 新答案</span><span class="review-caption" role="status" aria-live="polite">{{ statusText }}</span></header>
          <div class="review-content">
            <AiGeneratedAnswerViewer
              v-if="answerMessage?.text"
              :content="answerMessage.text"
              :render-svg="answerMessage.status === 'completed'"
              @validity-change="svgValid = $event"
            />
            <p v-else class="text-sm text-gray-400">{{ working || busy ? '正在生成，等待模型返回…' : hasAttempted ? '暂无新答案，可重新生成' : '尚未生成，请点击“开始生成”' }}</p>
          </div>
        </section>
      </div>
      <p v-if="formatError" class="mt-3 text-sm text-amber-800" role="status">{{ formatError }}</p>
      <p v-if="!svgValid && answerMessage?.status === 'completed'" class="mt-3 text-sm text-amber-800" role="status">图示格式不符合安全预览要求，已显示源码；请重新生成。</p>
    </div>
    <template #footer>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <span class="text-xs text-gray-500">格式检查不能保证答案正确，请核对推导与图示。</span>
        <div class="flex flex-wrap gap-2">
          <CustomButton @click="handleVisibility(false)">保留原答案</CustomButton>
          <CustomButton v-if="working || busy" :disabled="phase !== 'streaming'" @click="stop">{{ phase === 'stopping' ? '正在停止' : '停止生成' }}</CustomButton>
          <CustomButton v-else @click="generate">{{ hasAttempted ? '重新生成' : '开始生成' }}</CustomButton>
          <CustomButton type="primary" :disabled="!canAdopt" @click="adopt">采用新答案</CustomButton>
        </div>
      </div>
    </template>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import type { AiQuestionKind } from '@/api/aiSession'
import type { AiAnswerCandidate, AiAnswerSource } from '@/types/aiAnswer'
import { useAiConsultation } from '@/composables/useAiConsultation'
import { useAuthStore } from '@/stores/auth'
import { useConfirm } from '@/composables/useConfirm'
import { answerSourceError, answerSourceKey, generatedAnswerError } from '@/utils/aiAnswer'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import AiGeneratedAnswerViewer from '@/components/basic/AiGeneratedAnswerViewer.vue'

const props = defineProps<{
  visible: boolean
  questionKind: AiQuestionKind
  questionId: number
  source: AiAnswerSource
  draft?: boolean
}>()
const emit = defineEmits<{ 'update:visible': [visible: boolean]; adopt: [candidate: AiAnswerCandidate] }>()
const { session, messages, phase, errorMessage, busy, open, send, stop, close } = useAiConsultation()
const { showConfirm } = useConfirm()
const auth = useAuthStore()
const working = ref(false)
const hasAttempted = ref(false)
const baseline = ref<AiAnswerSource | null>(null)
const originalKey = ref('')
const svgValid = ref(true)
const localError = ref('')
let revision = 0

const answerMessage = computed(() => messages.value.find(message => message.role === 'assistant'))
const stale = computed(() => originalKey.value !== '' && originalKey.value !== answerSourceKey(props.source))
const failure = computed(() => localError.value || errorMessage.value || answerMessage.value?.errorMessage || '')
const formatError = computed(() => answerMessage.value?.status === 'completed' && baseline.value
  ? generatedAnswerError(answerMessage.value.text, baseline.value.questionType) : '')
const canAdopt = computed(() => !working.value && !busy.value && !stale.value && svgValid.value
  && !failure.value && !formatError.value && baseline.value !== null && answerMessage.value?.status === 'completed'
  && auth.isAdmin())
const statusText = computed(() => {
  if (phase.value === 'stopping') return '正在停止'
  if (working.value || busy.value) return '生成中'
  if (answerMessage.value?.status === 'completed') return '生成完成 · 尚未保存'
  if (answerMessage.value?.status === 'cancelled') return '已停止 · 答案不完整'
  return failure.value ? '生成失败' : '尚未生成'
})

/** 每次重建独立会话，不沿用旧候选或咨询历史；迟到创建不得触发发送。 */
async function generate(): Promise<void> {
  if (working.value || busy.value || !props.visible || !auth.isAdmin()) return
  const currentRevision = ++revision
  hasAttempted.value = true
  const source = structuredClone({ ...props.source, options: props.source.options ? { ...props.source.options } : null })
  originalKey.value = answerSourceKey(source)
  baseline.value = source
  localError.value = props.draft ? answerSourceError(source) : ''
  if (localError.value) return
  working.value = true
  svgValid.value = true
  try {
    await close()
    if (currentRevision !== revision || !props.visible) return
    const { answer: _originalAnswer, ...draft } = source
    await open(props.questionKind, props.questionId, props.draft ? { draft } : {})
    if (currentRevision !== revision || !props.visible || !session.value) return
    const actual = session.value.answerSource
    if (!actual) { localError.value = '缺少生成来源，请重新生成'; return }
    baseline.value = props.draft ? { ...actual, answer: source.answer } : actual
    await send('请生成本题的完整答案解析。')
  } finally {
    if (currentRevision === revision) working.value = false
  }
}

async function handleVisibility(visible: boolean): Promise<void> {
  if (visible) return
  const currentRevision = revision
  if (working.value || busy.value) {
    const confirmed = await showConfirm({ title: '结束答案生成',
      message: '关闭会停止当前生成并丢弃候选答案，已产生的费用不会退回。',
      confirmText: '结束并关闭', type: 'warning' })
    if (!confirmed || currentRevision !== revision) return
  }
  emit('update:visible', false)
}

function adopt(): void {
  if (!canAdopt.value || !baseline.value || !answerMessage.value) return
  emit('adopt', { questionKind: props.questionKind, questionId: props.questionId,
    source: baseline.value, answer: answerMessage.value.text.trim() })
  emit('update:visible', false)
}

/** 打开只初始化展示，不创建会话或发送请求；只有生成按钮能调用 generate。 */
watch(() => props.visible, visible => {
  revision += 1
  working.value = false
  hasAttempted.value = false
  originalKey.value = ''
  localError.value = ''
  svgValid.value = true
  if (visible) {
    baseline.value = structuredClone({ ...props.source,
      options: props.source.options ? { ...props.source.options } : null })
  } else {
    baseline.value = null
    void close()
  }
}, { immediate: true })
watch(() => [auth.token, auth.userInfo?.username, auth.userInfo?.role], () => {
  revision += 1
  working.value = false
  void close()
  emit('update:visible', false)
})
onBeforeUnmount(() => {
  revision += 1
  void close()
  // 权限变化或离页卸载后不能保留打开意图，避免重新挂载时自动调用模型。
  emit('update:visible', false)
})
</script>

<style scoped>
.review-columns { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; }
.review-pane { min-width: 0; border: 1px solid #e5e7eb; border-radius: .65rem; overflow: hidden; }
.review-pane--candidate { border-color: var(--brand-accent, #866349); }
.review-label { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: .5rem; padding: .85rem 1rem; border-bottom: 1px solid #e5e7eb; background: #f8f9fa; font-size: .875rem; font-weight: 600; }
.review-pane--candidate .review-label { color: var(--brand-accent, #866349); }
.review-caption { font-size: .75rem; font-weight: 400; color: #6b7280; }
.review-content { padding: 1rem; }
@media (max-width: 767px) { .review-columns { grid-template-columns: minmax(0, 1fr); } }
</style>
