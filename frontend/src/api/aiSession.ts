/**
 * AI 题目咨询会话接口：创建、流式提问、停止与关闭。
 * axios 无法消费流式响应，增量转发使用 fetch + ReadableStream；base URL 与令牌仍取自
 * api/request.ts 与 utils/token 的既有出口，不新建 Axios 实例，也不回传原始上游错误。
 */
import type { ApiResponse } from '@/types'
import { API_BASE_URL } from './request'
import { getToken } from '@/utils/token'
import { convertKeysToSnake } from '@/utils/convertKeys'
import { aiRequest } from './ai'
import { AiSettingsError, boolean, integer, invalid, providerId, record, revision, string } from './aiGuards'

/** 三类题目共用一套咨询会话，题目归属由后端按认证账号重新读取。 */
export type AiQuestionKind = 'exam' | 'mock' | 'adaptation'
export type AiTerminalStatus = 'completed' | 'cancelled' | 'failed'

export interface AiSessionModelView { provider: string; id: string; name: string; supportsImages: boolean }
export interface AiSessionView {
  sessionId: string
  questionKind: AiQuestionKind
  questionId: number
  model: AiSessionModelView
  inputMode: 'text'
  contextNote: string
}
export interface AiStreamMetaView {
  sessionId: string
  requestId: string
  model: AiSessionModelView
  inputMode: 'text'
}
export interface AiStreamErrorView { code: number; message: string }
export interface AiStreamDoneView {
  requestId: string
  status: AiTerminalStatus
  answer: string | null
  error: AiStreamErrorView | null
}
/** 增量到达时的回调；终态由 streamAiMessage 的返回值描述，避免两处都能宣告成功。 */
export interface AiStreamHandlers { onMeta?: (meta: AiStreamMetaView) => void; onDelta: (text: string) => void }

/** 后端公开的流错误码集合，其他取值一律按格式错误处理。 */
const STREAM_ERROR_CODES = [409, 422, 429, 502, 503]

/** 增量文本可能只有换行或空格，因此只限制类型与长度，不做非空白校验。 */
function rawText(value: unknown, max = 65536): string {
  if (typeof value !== 'string' || value.length > max) return invalid()
  return value
}
/** 提取会话与流事件共用的模型标识，不猜测未声明的能力。 */
function parseModel(value: unknown): AiSessionModelView {
  const item = record(value)
  return { provider: providerId(item.provider), id: string(item.id), name: string(item.name),
    supportsImages: boolean(item.supports_images) }
}
/** 只接受文本输入模式，图像链路未实现前不把其他模式当作可用。 */
function requireTextMode(value: unknown): 'text' {
  if (value !== 'text') return invalid()
  return value
}
/** 解析会话创建结果，题目与型号都必须是后端已核对的公开字段。 */
function parseSession(value: unknown): AiSessionView {
  const item = record(value)
  const kind = item.question_kind
  if (kind !== 'exam' && kind !== 'mock' && kind !== 'adaptation') return invalid()
  return { sessionId: revision(item.session_id), questionKind: kind, questionId: integer(item.question_id),
    model: parseModel(item.model), inputMode: requireTextMode(item.input_mode), contextNote: string(item.context_note, 300) }
}
/** 解析首帧 meta；缺少 meta 时无法把增量绑定到本次提问。 */
function parseMeta(value: unknown): AiStreamMetaView {
  const item = record(value)
  return { sessionId: revision(item.session_id), requestId: revision(item.request_id),
    model: parseModel(item.model), inputMode: requireTextMode(item.input_mode) }
}
/** 解析流错误对象，拒绝未声明的错误码以免误报为可重试。 */
function parseStreamError(value: unknown): AiStreamErrorView {
  const item = record(value)
  const code = integer(item.code)
  if (!STREAM_ERROR_CODES.includes(code)) return invalid()
  return { code, message: string(item.message, 300) }
}
/** 校验唯一终态：成功必须带完整回答，取消与失败不得携带可被误认成成功的回答。 */
function parseDone(value: unknown): AiStreamDoneView {
  const item = record(value)
  const status = item.status
  if (status !== 'completed' && status !== 'cancelled' && status !== 'failed') return invalid()
  const answer = item.answer === null || item.answer === undefined ? null : rawText(item.answer)
  const error = item.error === null || item.error === undefined ? null : parseStreamError(item.error)
  if (status === 'completed' ? !answer?.trim() || error !== null : answer !== null) return invalid()
  return { requestId: revision(item.request_id), status, answer, error }
}

/** 生成一次发送意图的标识，停止接口据此只取消原请求。 */
export function createAiRequestId(): string {
  return crypto.randomUUID()
}

/**
 * 创建文本咨询会话：只提交题目归属，题干由后端按可信快照固定，创建时不调用模型。
 */
export async function createAiSession(
  questionKind: AiQuestionKind,
  questionId: number,
  signal?: AbortSignal,
): Promise<AiSessionView> {
  const response = await aiRequest('sessions/create', { questionKind, questionId }, signal)
  return parseSession(response.data)
}

/**
 * 发送一轮提问并消费增量，返回唯一终态。
 * 停止不使用 AbortSignal：停止要先经 abort 接口取消上游原请求，再由后端下发 cancelled 终态。
 */
export async function streamAiMessage(
  sessionId: string,
  requestId: string,
  message: string,
  handlers: AiStreamHandlers,
  signal?: AbortSignal,
): Promise<AiStreamDoneView> {
  const session = revision(sessionId)
  const request = revision(requestId)
  const url = `${API_BASE_URL}/api/ai/sessions/${session}/messages`
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(convertKeysToSnake({ requestId: request, inputMode: 'text', message })),
      signal,
    })
  } catch (error: unknown) {
    if (signal?.aborted || (error instanceof DOMException && error.name === 'AbortError')) {
      throw new AiSettingsError('请求已取消', undefined, true)
    }
    throw new AiSettingsError('模型服务连接中断，请检查网络后重试')
  }

  // 生成开始前失败仍返回统一 JSON 信封，不能按流解析。
  if (!response.ok) throw await toStreamError(response)
  if (!response.body) throw new AiSettingsError('模型服务未返回流式响应')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let done: AiStreamDoneView | null = null

  try {
    while (done === null) {
      const chunk = await reader.read()
      if (chunk.done) break
      buffer += decoder.decode(chunk.value, { stream: true })
      // SSE 以空行分隔帧；保留最后一段不完整内容等待下一次读取。
      const frames = buffer.split('\n\n')
      buffer = frames.pop() ?? ''
      for (const frame of frames) {
        const parsed = await handleFrame(frame, request, handlers)
        if (parsed) done = parsed
      }
    }
  } catch (error: unknown) {
    if (signal?.aborted || (error instanceof DOMException && error.name === 'AbortError')) {
      throw new AiSettingsError('请求已取消', undefined, true)
    }
    throw error instanceof AiSettingsError ? error : new AiSettingsError('模型服务连接中断，回答可能不完整')
  } finally {
    // 断流或终态后都不再读取，避免继续累积上游费用。
    await reader.cancel().catch(() => undefined)
  }

  if (!done) throw new AiSettingsError('回答未正常结束，本次内容不完整', 502)
  return done
}

/** 解析单个 SSE 帧，只处理声明过的事件名，其他帧直接忽略。 */
async function handleFrame(
  frame: string,
  requestId: string,
  handlers: AiStreamHandlers,
): Promise<AiStreamDoneView | null> {
  const event = parseFrame(frame)
  if (!event) return null
  const payload = parsePayload(event.data)
  if (event.name === 'meta') {
    const meta = parseMeta(payload)
    if (meta.requestId !== requestId) throw new AiSettingsError('模型服务返回了其他提问的增量')
    handlers.onMeta?.(meta)
    return null
  }
  if (event.name === 'delta') {
    if (revision(payload.request_id) !== requestId) throw new AiSettingsError('模型服务返回了其他提问的增量')
    handlers.onDelta(rawText(payload.text))
    return null
  }
  if (event.name === 'done') {
    const result = parseDone(payload)
    if (result.requestId !== requestId) throw new AiSettingsError('模型服务返回了其他提问的终态')
    return result
  }
  return null
}

/** 按 SSE 规范拼接 event 与多行 data；缺少任一字段的帧不构成事件。 */
function parseFrame(frame: string): { name: string; data: string } | null {
  let name = ''
  const data: string[] = []
  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) name = line.slice(6).trim()
    else if (line.startsWith('data:')) data.push(line.slice(5).trim())
  }
  if (!name || data.length === 0) return null
  return { name, data: data.join('\n') }
}

/** 事件载荷必须是 JSON 对象；解析失败按响应格式错误处理，不保留原始文本。 */
function parsePayload(data: string): Record<string, unknown> {
  try {
    return record(JSON.parse(data) as unknown)
  } catch (error: unknown) {
    if (error instanceof AiSettingsError) throw error
    return invalid()
  }
}

/** 读取失败响应中的公开消息，不回传原始响应体或上游错误。 */
async function toStreamError(response: Response): Promise<AiSettingsError> {
  let message = '模型服务请求失败，请稍后重试'
  try {
    const body = (await response.json()) as unknown
    if (typeof body === 'object' && body !== null && 'message' in body) {
      const value = (body as { message: unknown }).message
      if (typeof value === 'string' && value.trim()) message = value.slice(0, 500)
    }
  } catch {
    // 非 JSON 错误体只保留状态码，不把原始内容带出边界。
  }
  return new AiSettingsError(message, response.status)
}

/** 停止原提问：只取消绑定的 request_id，不影响同一会话的下一轮。 */
export async function abortAiSession(
  sessionId: string,
  requestId: string,
  signal?: AbortSignal,
): Promise<{ stopped: boolean; closed: boolean }> {
  return parseAction(await aiRequest(`sessions/${revision(sessionId)}/abort`, { requestId: revision(requestId) }, signal))
}

/** 关闭会话并放弃未完成的生成；配置已清除时仍允许归属账号关闭残留会话。 */
export async function closeAiSession(
  sessionId: string,
  signal?: AbortSignal,
): Promise<{ stopped: boolean; closed: boolean }> {
  return parseAction(await aiRequest(`sessions/${revision(sessionId)}/close`, {}, signal))
}

/** 停止与关闭只回传两个布尔状态，不把服务端附加字段带进组件。 */
function parseAction(response: ApiResponse<unknown>): { stopped: boolean; closed: boolean } {
  const item = record(response.data)
  return { stopped: boolean(item.stopped), closed: boolean(item.closed) }
}
