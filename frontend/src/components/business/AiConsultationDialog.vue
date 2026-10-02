<!-- AI 咨询面板：三类题目共用一套会话界面，回答使用独立安全渲染。 -->
<template>
  <ResponsiveDialog
    :visible="visible"
    :title="dialogTitle"
    width="760px"
    max-width="calc(100vw - 24px)"
    top="calc(60px + 16px)"
    @close="requestClose"
  >
    <div class="flex flex-col gap-3">
      <p v-if="session" class="m-0 rounded-lg bg-gray-50 px-3 py-2 text-xs leading-5 text-ink-soft">
        当前模型：{{ session.model.name }}。{{ session.contextNote }}
      </p>

      <p v-if="errorMessage" role="alert" class="m-0 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
        {{ errorMessage }}
      </p>

      <p v-if="phase === 'creating'" role="status" class="m-0 text-sm text-ink-soft">正在准备会话…</p>

      <p v-else-if="messages.length === 0" class="m-0 text-sm text-ink-soft">
        输入问题后点击发送，回答会显示在这里。会话只保留在本次页面内。
      </p>

      <div
        ref="listRef"
        class="flex max-h-[min(52dvh,420px)] flex-col gap-3 overflow-y-auto scrollbar-stable"
      >
        <article
          v-for="message in messages"
          :key="message.id"
          class="rounded-lg border px-3 py-2"
          :class="message.role === 'user' ? 'border-accent/30 bg-accent/5' : 'border-gray-200 bg-white'"
        >
          <p class="m-0 mb-1 text-xs font-medium text-ink-soft">
            {{ message.role === 'user' ? '我的提问' : 'AI 回答' }}
          </p>

          <p v-if="message.role === 'user'" class="m-0 whitespace-pre-wrap text-sm leading-6 text-ink">
            {{ message.text }}
          </p>

          <template v-else>
            <AiAnswerViewer v-if="message.text" :content="message.text" />

            <p v-if="message.status === 'streaming'" class="m-0 text-xs text-ink-soft">正在生成…</p>
            <p v-else-if="message.status === 'cancelled'" class="m-0 text-xs text-amber-700">
              已停止，本次回答不完整；需要继续请重新打开咨询。
            </p>
            <p v-else-if="message.status === 'failed'" class="m-0 text-xs text-red-600">
              {{ message.errorMessage || '生成失败' }}
            </p>
          </template>
        </article>
      </div>

      <!-- 流式状态播报与回答正文分离，避免整段回答被反复朗读。 -->
      <p class="sr-only" role="status" aria-live="polite">{{ liveStatus }}</p>
    </div>

    <template #footer>
      <div class="flex flex-col gap-2">
        <label class="sr-only" :for="inputId">向 AI 提问</label>
        <textarea
          :id="inputId"
          v-model="draft"
          :disabled="!canSend"
          :maxlength="MAX_MESSAGE_CHARS"
          rows="2"
          class="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm leading-6 text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:bg-gray-100"
          placeholder="输入问题，Enter 发送，Shift+Enter 换行"
          @keydown="handleKeydown"
        ></textarea>

        <div class="flex flex-wrap items-center justify-between gap-2">
          <p class="m-0 text-xs text-ink-soft">
            参考解析可能直接包含答案，回答由模型生成，可能有误。
          </p>
          <div class="flex shrink-0 items-center gap-2">
            <CustomButton
              v-if="phase === 'streaming'"
              type="warning"
              size="sm"
              @click="stop"
            >
              停止
            </CustomButton>
            <CustomButton
              v-else
              type="primary"
              size="sm"
              :disabled="!canSend || !draft.trim()"
              :loading="phase === 'creating' || phase === 'stopping'"
              @click="submit"
            >
              {{ phase === 'stopping' ? '停止中' : '发送' }}
            </CustomButton>
          </div>
        </div>
      </div>
    </template>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
/**
 * AI 咨询面板。
 * 三类题目共用一套面板：只提交题目归属，题干由后端按可信快照固定；
 * 关闭生成中的会话需要确认，避免静默丢弃已产生的生成与费用。
 */
import { computed, nextTick, onBeforeUnmount, ref, watch, type PropType } from 'vue'
import type { AiQuestionKind } from '@/api/aiSession'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import AiAnswerViewer from '@/components/basic/AiAnswerViewer.vue'
import { useAiConsultation } from '@/composables/useAiConsultation'
import { useConfirm } from '@/composables/useConfirm'

/** 与后端提问上限保持一致，超长输入在浏览器侧就截断。 */
const MAX_MESSAGE_CHARS = 2000

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  questionKind: {
    type: String as PropType<AiQuestionKind>,
    required: true
  },
  questionId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits<{ 'update:visible': [visible: boolean] }>()

const { showConfirm } = useConfirm()
const { session, messages, phase, errorMessage, busy, canSend, open, send, stop, close } = useAiConsultation()

const draft = ref('')
const listRef = ref<HTMLElement | null>(null)
const inputId = `ai-consultation-input-${props.questionKind}-${props.questionId}`

const dialogTitle = computed(() => 'AI 咨询')
/** 只在状态切换时播报一次，不把流式增量交给读屏器。 */
const liveStatus = computed(() => {
  if (phase.value === 'creating') return '正在准备会话'
  if (phase.value === 'stopping') return '正在停止生成'
  if (phase.value === 'streaming') return '正在生成回答'
  return ''
})

/** 新消息与增量到达后保持最新内容可见，滚动只作用于回答列表。 */
async function scrollToLatest(): Promise<void> {
  await nextTick()
  const list = listRef.value
  if (list) list.scrollTop = list.scrollHeight
}

/** 生成中不允许直接关闭：确认后才放弃会话。 */
async function requestClose(): Promise<void> {
  if (busy.value) {
    const confirmed = await showConfirm({
      title: '放弃本次咨询',
      message: '正在生成回答，关闭会放弃整个会话，已产生的费用不会退回。',
      confirmText: '放弃并关闭',
      type: 'warning'
    })
    if (!confirmed) return
  }
  await close()
  emit('update:visible', false)
}

/** 发送成功后清空草稿；被拒绝的输入由状态机再次拦截。 */
async function submit(): Promise<void> {
  if (!canSend.value || !draft.value.trim()) return
  const question = draft.value
  draft.value = ''
  await send(question)
}

/** Enter 发送、Shift+Enter 换行；输入法组合期间的 Enter 属于候选词确认，不能发送。 */
function handleKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return
  event.preventDefault()
  void submit()
}

watch(() => props.visible, visible => {
  if (visible) void open(props.questionKind, props.questionId)
}, { immediate: true })
watch(() => [messages.value.length, messages.value[messages.value.length - 1]?.text.length ?? 0], scrollToLatest)

// 卡片卸载等被动关闭也要通知服务端，不能把会话留在内存里继续计费。
onBeforeUnmount(() => { void close() })
</script>
