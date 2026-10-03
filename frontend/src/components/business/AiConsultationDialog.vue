<!-- AI 客服聊天窗：右下角非模态悬浮，收起保留会话；三类题目共用唯一窗口。 -->
<template>
  <Teleport to="body">
    <template v-if="target">
      <button
        v-if="!expanded"
        ref="launcherRef"
        type="button"
        class="ai-chat-launcher inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent px-4 py-3 text-sm font-medium text-white shadow-lg hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
        aria-controls="ai-consultation-panel"
        :aria-expanded="expanded"
        :aria-label="`展开 AI 咨询：${target.label}`"
        @click="expand"
      >
        <span class="flex h-6 w-6 items-center justify-center rounded-full bg-white/20 text-xs" aria-hidden="true">AI</span>
        <span>{{ busy ? 'AI 咨询 · ' + (liveStatus || '处理中') : 'AI 咨询' }}</span>
        <font-awesome-icon :icon="['fas', 'chevron-up']" aria-hidden="true" />
      </button>

      <aside
        v-show="expanded"
        id="ai-consultation-panel"
        ref="panelRef"
        class="ai-chat-panel flex min-h-0 flex-col overflow-hidden rounded-2xl border border-line bg-white shadow-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        tabindex="-1"
        aria-labelledby="ai-consultation-title"
        @keydown.esc.stop.prevent="collapse"
      >
        <header class="flex shrink-0 items-start gap-2 border-b border-line bg-surface px-4 py-3">
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent text-sm font-semibold text-white" aria-hidden="true">AI</span>
          <div class="min-w-0 flex-1">
            <h2 id="ai-consultation-title" class="m-0 text-sm font-semibold text-ink">AI 咨询</h2>
            <p class="m-0 mt-0.5 truncate text-xs text-ink-soft" :title="target.label">{{ target.label }}</p>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-md px-2 py-1 text-xs text-ink-soft hover:bg-accent/10 hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-label="结束会话并清空聊天"
            @click="endConversation"
          >结束</button>
          <button
            type="button"
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-ink-soft hover:bg-accent/10 hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            title="收起，保留聊天"
            aria-label="收起 AI 咨询，保留聊天"
            @click="collapse"
          >
            <font-awesome-icon :icon="['fas', 'times']" aria-hidden="true" />
          </button>
        </header>

        <div ref="listRef" class="scrollbar-stable flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto overscroll-contain px-4 py-3">
          <p v-if="session" class="m-0 text-xs leading-5 text-ink-soft">
            当前模型：{{ session.model.name }}。{{ session.contextNote }}
          </p>
          <p v-if="errorMessage" role="alert" class="m-0 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
            {{ errorMessage }}
          </p>
          <p v-if="phase === 'creating'" role="status" class="m-0 text-sm text-ink-soft">正在准备会话…</p>
          <div v-else-if="messages.length === 0 && session" class="my-auto py-5 text-center">
            <p class="m-0 text-sm font-medium text-ink">想问这道题的哪一步？</p>
            <p class="m-0 mt-2 text-xs leading-5 text-ink-soft">可以问解题思路、选项区别，或让 AI 解释某个知识点。</p>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="min-w-0 rounded-xl px-3 py-2"
            :class="message.role === 'user' ? 'ml-6 self-end border border-accent/20 bg-accent/5' : 'mr-2 border border-gray-100 bg-gray-50'"
          >
            <p class="m-0 mb-1 text-xs font-medium text-ink-soft">{{ message.role === 'user' ? '我的提问' : 'AI 回答' }}</p>
            <p v-if="message.role === 'user'" class="m-0 whitespace-pre-wrap break-words text-sm leading-6 text-ink">{{ message.text }}</p>
            <template v-else>
              <AiAnswerViewer v-if="message.text" :content="message.text" />
              <p v-if="message.status === 'streaming'" class="m-0 text-xs text-ink-soft">正在生成…</p>
              <p v-else-if="message.status === 'cancelled'" class="m-0 text-xs text-amber-700">已停止，本次回答不完整。需要继续请新建会话。</p>
              <p v-else-if="message.status === 'failed'" class="m-0 text-xs text-red-600">{{ message.errorMessage || '生成失败' }}</p>
            </template>
          </article>
        </div>

        <footer class="flex shrink-0 flex-col gap-2 border-t border-line bg-white px-4 py-3">
          <div v-if="canRestart" class="flex items-center justify-between gap-2">
            <p class="m-0 text-xs leading-5 text-ink-soft">新建会话后将清空本次聊天。</p>
            <button
              type="button"
              class="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-accent hover:bg-accent/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              @click="restartConversation"
            >新建会话</button>
          </div>
          <label class="sr-only" :for="inputId">向 AI 提问</label>
          <textarea
            :id="inputId"
            v-model="draft"
            :disabled="!canSend || switching"
            :maxlength="MAX_MESSAGE_CHARS"
            rows="2"
            class="ai-chat-input w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm leading-6 text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:bg-gray-100"
            placeholder="输入问题，Enter 发送，Shift+Enter 换行"
            @keydown="handleKeydown"
          ></textarea>
          <div class="flex items-center justify-between gap-2">
            <p class="m-0 text-xs leading-5 text-ink-soft">收起不停止生成；停止不退回已产生的费用。</p>
            <CustomButton v-if="phase === 'streaming'" type="warning" size="sm" @click="stop">停止</CustomButton>
            <CustomButton
              v-else
              type="primary"
              size="sm"
              :disabled="!canSend || switching || !draft.trim()"
              :loading="phase === 'creating' || phase === 'stopping' || switching"
              @click="submit"
            >{{ phase === 'stopping' ? '停止中' : '发送' }}</CustomButton>
          </div>
          <p class="m-0 text-[11px] leading-4 text-ink-mute">参考解析可能包含答案，AI 回答可能有误。聊天仅保留在当前页面。</p>
        </footer>
      </aside>
      <!-- 状态播报独立于正文，收起时仍可获知生成状态，不逐字朗读增量。 -->
      <p class="sr-only" role="status" aria-live="polite">{{ liveStatus }}</p>
    </template>
  </Teleport>
</template>

<script setup lang="ts">
/** 非模态窗口不锁滚动、不困住焦点；隐藏与结束会话分开，避免关闭后丢失聊天入口。 */
import { computed, nextTick, ref, watch } from 'vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import AiAnswerViewer from '@/components/basic/AiAnswerViewer.vue'
import { useAiConsultationPanel } from '@/composables/useAiConsultationPanel'

const MAX_MESSAGE_CHARS = 2000
const {
  target, expanded, switching, session, messages, phase, errorMessage, busy, canSend,
  send, stop, collapse, expand, endConversation, restartConversation,
} = useAiConsultationPanel()

const draft = ref('')
const listRef = ref<HTMLElement | null>(null)
const panelRef = ref<HTMLElement | null>(null)
const launcherRef = ref<HTMLButtonElement | null>(null)
let previouslyFocused: HTMLElement | null = null

const inputId = computed(() => `ai-consultation-input-${target.value?.questionKind}-${target.value?.questionId}`)
const canRestart = computed(() => !busy.value && !switching.value && (
  !session.value || messages.value[messages.value.length - 1]?.status === 'cancelled' ||
  messages.value[messages.value.length - 1]?.status === 'failed'
))
const liveStatus = computed(() => {
  if (phase.value === 'creating') return '正在准备会话'
  if (phase.value === 'stopping') return '正在停止生成'
  if (phase.value === 'streaming') return '正在生成回答'
  const last = messages.value[messages.value.length - 1]
  if (last?.status === 'completed') return '回答已完成'
  if (last?.status === 'cancelled') return '已停止生成'
  if (last?.status === 'failed') return '生成失败'
  return ''
})

/** 只滚动聊天列表，不移动题目阅读位置。 */
async function scrollToLatest(): Promise<void> {
  await nextTick()
  const list = listRef.value
  if (list && expanded.value) list.scrollTop = list.scrollHeight
}

/** 发送前清空草稿，重复发送仍由会话状态机拒绝。 */
async function submit(): Promise<void> {
  if (!canSend.value || switching.value || !draft.value.trim()) return
  const question = draft.value
  draft.value = ''
  await send(question)
}

/** 输入法确认候选词时不能误发送；Shift+Enter 保留换行。 */
function handleKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return
  event.preventDefault()
  void submit()
}

watch(target, current => {
  draft.value = ''
  if (!current) {
    const focused = previouslyFocused
    previouslyFocused = null
    if (focused?.isConnected) focused.focus({ preventScroll: true })
  }
})
watch(expanded, async visible => {
  if (visible && document.activeElement instanceof HTMLElement && document.activeElement !== launcherRef.value) {
    previouslyFocused = document.activeElement
  }
  await nextTick()
  if (visible !== expanded.value || !target.value) return
  if (visible) {
    // 聚焦窗口而不是输入框，避免手机展开时自动唤起软键盘遮住题目。
    panelRef.value?.focus({ preventScroll: true })
    await scrollToLatest()
  } else {
    launcherRef.value?.focus({ preventScroll: true })
  }
})
watch(() => [messages.value.length, messages.value[messages.value.length - 1]?.text.length ?? 0], scrollToLatest)
</script>

<style scoped>
.ai-chat-panel,
.ai-chat-launcher {
  position: fixed;
  z-index: 900;
  right: max(16px, env(safe-area-inset-right));
  bottom: max(16px, env(safe-area-inset-bottom));
}

.ai-chat-panel {
  width: min(400px, calc(100vw - 32px));
  height: min(620px, calc(var(--app-page-height) - 32px));
  max-height: calc(100dvh - var(--app-nav-height) - 32px);
  overflow-wrap: anywhere;
}

.ai-chat-input {
  max-height: 96px;
}

@media (max-width: 767px) {
  .ai-chat-panel {
    right: max(8px, env(safe-area-inset-right));
    bottom: max(8px, env(safe-area-inset-bottom));
    width: calc(100vw - 16px - env(safe-area-inset-right) - env(safe-area-inset-left));
    height: min(60dvh, 520px);
    max-height: calc(100dvh - var(--app-nav-height) - 16px);
  }
}
</style>
