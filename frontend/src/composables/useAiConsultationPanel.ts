/**
 * 页面内唯一 AI 客服窗的协调器：题目卡片只提交咨询目标，收起保留会话，离页或账号变化时释放。
 * 不持久化聊天内容，不因展开窗口自动发送问题或调用模型。
 */
import { readonly, ref } from 'vue'
import type { AiQuestionKind } from '@/api/aiSession'
import { useAiConsultation } from '@/composables/useAiConsultation'
import { useConfirm } from '@/composables/useConfirm'

interface ConsultationTarget {
  questionKind: AiQuestionKind
  questionId: number
  label: string
}

const target = ref<ConsultationTarget | null>(null)
const expanded = ref(false)
const switching = ref(false)
const consultation = useAiConsultation()
const { showConfirm } = useConfirm()
/** 使离页前尚未完成的确认、关闭与创建流程失效。 */
let revision = 0

/** 同题恢复原会话；切题时关闭旧会话，生成中须先确认，防止把回答绑定到其他题目。 */
async function openQuestion(questionKind: AiQuestionKind, questionId: number, label: string): Promise<void> {
  if (switching.value) return
  if (target.value?.questionKind === questionKind && target.value.questionId === questionId) {
    expanded.value = true
    return
  }

  const currentRevision = ++revision
  switching.value = true
  try {
    if (consultation.busy.value) {
      const confirmed = await showConfirm({
        title: '切换咨询题目',
        message: '当前回答正在生成，切换会结束原会话，已产生的费用不会退回。',
        confirmText: '结束并切换',
        type: 'warning',
      })
      if (!confirmed || currentRevision !== revision) return
    }
    await consultation.close()
    if (currentRevision !== revision) return
    target.value = { questionKind, questionId, label }
    expanded.value = true
    await consultation.open(questionKind, questionId)
  } finally {
    if (currentRevision === revision) switching.value = false
  }
}

/** 收起只是隐藏窗口，后台生成与费用不会因此停止。 */
function collapse(): void {
  expanded.value = false
}

/** 重新展开只恢复界面，不创建新会话。 */
function expand(): void {
  if (target.value) expanded.value = true
}

/** 离开页面、账号变化或主动结束时立即清空界面，再归还服务端会话。 */
async function clear(): Promise<void> {
  revision += 1
  target.value = null
  expanded.value = false
  switching.value = false
  await consultation.close()
}

/** 主动结束生成中的咨询需确认；收起不走此流程。 */
async function endConversation(): Promise<void> {
  if (!target.value) return
  const currentRevision = revision
  if (consultation.busy.value) {
    const confirmed = await showConfirm({
      title: '结束本次咨询',
      message: '结束会清空本次聊天并停止当前请求，已产生的费用不会退回。只想隐藏窗口请使用收起。',
      confirmText: '结束会话',
      type: 'warning',
    })
    if (!confirmed || currentRevision !== revision) return
  }
  if (currentRevision === revision) await clear()
}

/** 非成功终态不能沿用服务端历史，保留题目归属但明确新建会话。 */
async function restartConversation(): Promise<void> {
  const current = target.value
  if (!current || switching.value || consultation.busy.value) return
  const currentRevision = ++revision
  switching.value = true
  try {
    await consultation.close()
    if (currentRevision !== revision) return
    target.value = { ...current }
    await consultation.open(current.questionKind, current.questionId)
  } finally {
    if (currentRevision === revision) switching.value = false
  }
}

/** 同一应用外壳与三类卡片共用一个窗口，不随单张卡片卸载销毁聊天。 */
export function useAiConsultationPanel() {
  return {
    target: readonly(target),
    expanded: readonly(expanded),
    switching: readonly(switching),
    session: consultation.session,
    messages: consultation.messages,
    phase: consultation.phase,
    errorMessage: consultation.errorMessage,
    busy: consultation.busy,
    canSend: consultation.canSend,
    send: consultation.send,
    stop: consultation.stop,
    openQuestion,
    collapse,
    expand,
    clear,
    endConversation,
    restartConversation,
  }
}
