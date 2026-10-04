/**
 * AI 题目咨询与答案生成共用的会话状态机。
 * 会话与历史只存在于页面内存：不写数据库、localStorage 或 sessionStorage；收起不销毁，刷新或结束后不可恢复。
 * 只有真实成功的完整终态写入历史并允许追问；停止、失败与断流只把片段标记为不完整。
 */
import { computed, ref } from 'vue'
import {
  abortAiSession,
  closeAiSession,
  createAiRequestId,
  createAiSession,
  streamAiMessage,
  type AiQuestionKind,
  type AiSessionView,
  type AiTerminalStatus,
} from '@/api/aiSession'
import { AiSettingsError } from '@/api/aiGuards'
import type { AiAnswerDraft } from '@/types/aiAnswer'

export type AiChatRole = 'user' | 'assistant'
export type AiChatStatus = 'streaming' | 'completed' | 'cancelled' | 'failed'
export type AiConsultationPhase = 'idle' | 'creating' | 'streaming' | 'stopping'

export interface AiChatMessage {
  id: string
  role: AiChatRole
  text: string
  status: AiChatStatus
  /** 失败或断流时的公开提示；不携带上游原始错误。 */
  errorMessage?: string
}

/** 只展示可安全公开的消息，未知错误统一为通用提示。 */
function toMessage(error: unknown): string {
  return error instanceof AiSettingsError ? error.message : '模型服务请求失败，请稍后重试'
}

export function useAiConsultation() {
  const session = ref<AiSessionView | null>(null)
  const messages = ref<AiChatMessage[]>([])
  const phase = ref<AiConsultationPhase>('idle')
  const errorMessage = ref('')
  /** 当前在途提问的标识；停止与终态都必须绑定同一个标识。 */
  let activeRequestId = ''
  /** 仅用于组件卸载时中断本地读取，停止生成一律走 abort 接口。 */
  let readerAbort: AbortController | null = null
  /** 每次清理递增，旧会话的迟到响应不能更新新会话。 */
  let revision = 0

  /** 生成中：包含创建与停止确认阶段，期间禁止再次发送。 */
  const busy = computed(() => phase.value !== 'idle')

  /** 只有存在会话且上一轮为完整成功终态时才允许追问。 */
  const canSend = computed(() => {
    if (phase.value !== 'idle' || session.value === null) return false
    const last = messages.value[messages.value.length - 1]
    return !last || last.status === 'completed'
  })

  /** 清空页面内存中的会话与历史，不发任何模型请求。 */
  function reset(): void {
    revision += 1
    session.value = null
    messages.value = []
    errorMessage.value = ''
    phase.value = 'idle'
    activeRequestId = ''
    readerAbort = null
  }

  /** 普通咨询读取保存题面；答案生成可使用管理员编辑草稿，创建本身不调用模型。 */
  async function open(
    questionKind: AiQuestionKind, questionId: number, answerGeneration?: { draft?: AiAnswerDraft },
  ): Promise<void> {
    reset()
    const currentRevision = revision
    phase.value = 'creating'
    try {
      const created = await createAiSession(questionKind, questionId, undefined, answerGeneration)
      if (currentRevision !== revision) {
        // 即使创建期间已离开页面，也归还迟到的服务端会话。
        await closeAiSession(created.sessionId).catch(() => undefined)
        return
      }
      session.value = created
    } catch (error: unknown) {
      if (currentRevision === revision) errorMessage.value = toMessage(error)
    } finally {
      if (currentRevision === revision) phase.value = 'idle'
    }
  }

  /** 写入终态：成功采用完整回答，取消与失败保留已收到的片段并标记不完整。 */
  function applyTerminal(
    message: AiChatMessage,
    status: AiTerminalStatus,
    answer: string | null,
    failure?: string,
  ): void {
    if (status === 'completed' && answer) {
      message.text = answer
      message.status = 'completed'
      return
    }
    message.status = status === 'cancelled' ? 'cancelled' : 'failed'
    if (status !== 'cancelled') message.errorMessage = failure ?? '生成失败，请新建会话后重试'
  }

  /** 流读取异常按取消与失败区分，避免把断流显示成完成。 */
  function applyInterrupted(message: AiChatMessage, error: unknown): void {
    const cancelled = error instanceof AiSettingsError && error.cancelled
    message.status = cancelled ? 'cancelled' : 'failed'
    if (!cancelled) message.errorMessage = toMessage(error)
  }

  /** 发送一轮提问并消费增量；重复点击与无会话状态在此直接拒绝。 */
  async function send(text: string): Promise<void> {
    const current = session.value
    const question = text.trim()
    if (!current || !canSend.value || !question) return
    errorMessage.value = ''
    const requestId = createAiRequestId()
    const currentRevision = revision
    activeRequestId = requestId
    messages.value.push({ id: requestId, role: 'user', text: question, status: 'completed' })
    messages.value.push({ id: `${requestId}-answer`, role: 'assistant', text: '', status: 'streaming' })
    const answer = messages.value[messages.value.length - 1]
    const reader = new AbortController()
    readerAbort = reader
    phase.value = 'streaming'
    try {
      const done = await streamAiMessage(current.sessionId, requestId, question, {
        onDelta: (chunk: string) => {
          if (currentRevision === revision) answer.text += chunk
        },
      }, reader.signal)
      if (currentRevision === revision) applyTerminal(answer, done.status, done.answer, done.error?.message)
    } catch (error: unknown) {
      if (currentRevision === revision) applyInterrupted(answer, error)
    } finally {
      if (currentRevision === revision) {
        readerAbort = null
        activeRequestId = ''
        phase.value = 'idle'
      }
    }
  }

  /**
   * 停止当前提问。
   * 停止确认前保持 stopping 并拒绝新发送：不以本地取消作为上游停止与费用撤销的证明。
   */
  async function stop(): Promise<void> {
    const current = session.value
    if (!current || phase.value !== 'streaming' || !activeRequestId) return
    const currentRevision = revision
    const requestId = activeRequestId
    phase.value = 'stopping'
    try {
      await abortAiSession(current.sessionId, requestId)
    } catch (error: unknown) {
      // 停止未确认：保留 stopping，等待原流终态或由用户结束会话。
      if (currentRevision === revision && activeRequestId === requestId) errorMessage.value = toMessage(error)
    }
  }

  /** 关闭会话：先中断本地读取，再请求服务端释放原请求与内存历史。 */
  async function close(): Promise<void> {
    const current = session.value
    const pending = readerAbort
    reset()
    pending?.abort()
    if (!current) return
    try {
      await closeAiSession(current.sessionId)
    } catch {
      // 关闭失败不阻塞页面：服务端闲置回收仍会清理会话。
    }
  }

  return { session, messages, phase, errorMessage, busy, canSend, open, send, stop, close, reset }
}
