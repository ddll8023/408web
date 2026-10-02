/**
 * AI 模块共用的响应校验助手与错误类型。
 * 设置接口与会话接口共用同一套严格解析，避免安全校验出现两份实现后漂移；
 * 本文件只做结构校验，不引入 Axios、业务状态或任何网络行为。
 */

/** AI 接口错误：只保留安全消息、状态与取消标记，不携带配置、认证头或原始 cause。 */
export class AiSettingsError extends Error {
  /** 只保留安全消息、状态与取消标记，不能附带 Axios 配置、认证头或原始 cause。 */
  constructor(message: string, readonly status?: number, readonly cancelled = false) {
    super(message)
    this.name = 'AiSettingsError'
  }
}

/** 响应校验失败统一返回固定消息，不保留可能含敏感字段的响应对象。 */
export function invalid(): never { throw new AiSettingsError('模型服务响应格式错误，请重新加载') }
/** 只接收普通对象形态，后续解析显式提取声明的公开字段。 */
export function record(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return invalid()
  return value as Record<string, unknown>
}
/** 校验公开标识与名称的非空文本及长度，不做隐式类型转换。 */
export function string(value: unknown, max = 200): string {
  if (typeof value !== 'string' || !value.trim() || value.length > max) return invalid()
  return value
}
/** 响应开关只接受布尔值，不能把字符串真值当成有效状态。 */
export function boolean(value: unknown): boolean { return typeof value === 'boolean' ? value : invalid() }
/** 限制目录计数和能力数值为预算内的非负安全整数。 */
export function integer(value: unknown, max = Number.MAX_SAFE_INTEGER): number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 && value <= max ? value : invalid()
}
/** 校验配置修订或请求 UUID，防止无效标识被用于结果绑定。 */
export function revision(value: unknown): string {
  const result = string(value, 36)
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(result) ? result : invalid()
}
/** 校验供应商标识语法；接入支持与调用权限不能由语法推断。 */
export function providerId(value: unknown): string {
  const result = string(value, 100)
  return /^[a-z0-9][a-z0-9-]*$/.test(result) ? result : invalid()
}
