/** 个人模型服务 API：统一鉴权、字段转换及响应校验，错误不保留含 Key 的请求对象。 */
import axios from 'axios'
import type { ApiResponse } from '@/types'
import { convertKeysToSnake } from '@/utils/convertKeys'
import request from './request'
import { AiSettingsError, boolean, integer, invalid, providerId, record, revision, string } from './aiGuards'

// 错误类型随共用校验迁出，仍从本模块导出，既有引用点无需改动。
export { AiSettingsError } from './aiGuards'

/** 配置层的输入模式取值；本批运行时不读取该字段，是否带图按题目是否含图片自动判定。 */
export type AiInputMode = 'text' | 'text_image'
/** 自定义供应商可选的三种上游协议，与后端 ModelSpec 的协议取值一致。 */
export type AiProtocol = 'openai-completions' | 'openai-responses' | 'anthropic-messages'
export interface AiSettingsView {
  providerId: string
  modelId: string
  inputMode: AiInputMode
  enabled: boolean
  revision: string
}
export interface AiSettingsSaveRequest {
  providerId: string
  modelId: string
  inputMode: AiInputMode
  enabled: boolean
}
export interface AiProviderConfigView {
  providerId: string
  enabled: boolean
  hasApiKey: boolean
  revision: string
}
export interface AiProviderView {
  id: string
  name: string
  supported: boolean
  unsupportedReason: string | null
  baseUrls: string[]
  modelCount: number
  custom: boolean
  baseUrl: string | null
  protocol: AiProtocol | null
  configured: boolean
  enabled: boolean
  hasApiKey: boolean
  revision: string | null
}
export interface AiProviderSaveRequest { providerId: string; enabled: boolean; apiKey?: string }
export interface AiCustomProviderSaveRequest {
  providerId?: string
  name: string
  baseUrl: string
  protocol: AiProtocol
  enabled: boolean
  apiKey?: string
}
export interface AiCustomProviderView extends AiProviderConfigView {
  name: string
  baseUrl: string
  protocol: AiProtocol
  modelCount: number
}
export interface AiCustomModelSaveRequest {
  providerId: string
  modelId: string
  name: string
  supportsImages: boolean
  contextWindow: number
  maxTokens: number
}
export interface AiModelView { provider: string; id: string; name: string; supportsImages: boolean }
export interface AiCatalogModelView extends AiModelView {
  reasoning: boolean
  contextWindow: number
  maxTokens: number
  api: string
}
export interface AiModelsView {
  providerId: string
  models: AiCatalogModelView[]
  total: number
  offset: number
  limit: number
  source: 'bundled' | 'custom'
}
export interface AiModelsQueryRequest {
  providerId: string
  search?: string
  offset?: number
  limit?: number
  modelId?: string
}
export interface AiModelCheckRequest {
  providerId: string
  providerRevision: string
  modelId: string
  requestId: string
  confirmUsage: true
}
export interface AiModelCheckView { requestId: string; model: AiModelView; success: true }

/** 复用统一鉴权与字段转换；目录刷新和检测可延长超时，但不自动重试。 */
export async function aiRequest(path: string, data: unknown, signal?: AbortSignal, timeout = 15000): Promise<ApiResponse<unknown>> {
  try {
    return await request<unknown>({ url: `/api/ai/${path}`, method: 'post', data: convertKeysToSnake(data), signal, timeout })
  } catch (error: unknown) {
    if (axios.isCancel(error)) throw new AiSettingsError('请求已取消', undefined, true)
    if (axios.isAxiosError<unknown>(error)) {
      const body = error.response?.data
      const message = typeof body === 'object' && body !== null && 'message' in body && typeof body.message === 'string'
        ? body.message.slice(0, 500) : '模型服务请求失败，请检查网络或稍后重试'
      throw new AiSettingsError(message, error.response?.status)
    }
    throw new AiSettingsError('模型服务请求失败，请稍后重试')
  }
}
/** 只接受三种已知协议，拒绝把未知字符串当成可执行协议。 */
function parseProtocol(value: unknown): AiProtocol {
  if (value === 'openai-completions' || value === 'openai-responses' || value === 'anthropic-messages') return value
  return invalid()
}
/** 提取独立的默认咨询选择，允许尚未配置，不读取供应商凭据状态。 */
function parseSettings(value: unknown): AiSettingsView | null {
  if (value === null) return null
  const item = record(value)
  if (item.inputMode !== 'text' && item.inputMode !== 'text_image') return invalid()
  return { providerId: providerId(item.providerId), modelId: string(item.modelId), inputMode: item.inputMode,
    enabled: boolean(item.enabled), revision: revision(item.revision) }
}
/** 只提取保存后的供应商状态与修订，不将额外响应字段带入组件。 */
function parseProviderConfig(value: unknown): AiProviderConfigView {
  const item = record(value)
  return { providerId: providerId(item.providerId), enabled: boolean(item.enabled),
    hasApiKey: boolean(item.hasApiKey), revision: revision(item.revision) }
}
/** 合并解析目录接入说明和账号保存状态，二者均不代表真实检测成功。 */
function parseProvider(value: unknown): AiProviderView {
  const item = record(value)
  if (!Array.isArray(item.baseUrls) || item.baseUrls.length > 8) return invalid()
  const custom = boolean(item.custom)
  return {
    id: providerId(item.id), name: string(item.name), supported: boolean(item.supported),
    unsupportedReason: item.unsupportedReason === null ? null : string(item.unsupportedReason, 300),
    baseUrls: item.baseUrls.map(value => string(value, 1000)), modelCount: integer(item.modelCount),
    custom, baseUrl: custom ? string(item.baseUrl, 2048) : null,
    protocol: custom ? parseProtocol(item.protocol) : null,
    configured: boolean(item.configured), enabled: boolean(item.enabled), hasApiKey: boolean(item.hasApiKey),
    revision: item.revision === null ? null : revision(item.revision),
  }
}
/** 解析自定义供应商保存结果，除公开状态外还返回可编辑的接口信息。 */
function parseCustomProvider(value: unknown): AiCustomProviderView {
  const item = record(value)
  return { ...parseProviderConfig(item), name: string(item.name), baseUrl: string(item.baseUrl, 2048),
    protocol: parseProtocol(item.protocol), modelCount: integer(item.modelCount) }
}
/** 提取模型归属、实际 ID、名称和图像能力，不保存内部请求配置。 */
function parseModel(value: unknown): AiModelView {
  const item = record(value)
  return { provider: providerId(item.provider), id: string(item.id), name: string(item.name), supportsImages: boolean(item.supportsImages) }
}
/** 在公开模型字段上校验推理、上下文与协议元数据，不猜测未声明能力。 */
function parseCatalogModel(value: unknown): AiCatalogModelView {
  const item = record(value)
  return { ...parseModel(item), reasoning: boolean(item.reasoning), contextWindow: integer(item.contextWindow),
    maxTokens: integer(item.maxTokens), api: string(item.api, 100) }
}
/** 校验目录来源、分页预算与模型归属，拒绝混入其他供应商的条目。 */
function parseModels(value: unknown): AiModelsView {
  const item = record(value)
  if (!Array.isArray(item.models) || item.models.length > 100) return invalid()
  if (item.source !== 'bundled' && item.source !== 'custom') return invalid()
  const id = providerId(item.providerId)
  const models = item.models.map(parseCatalogModel)
  const limit = integer(item.limit, 100)
  const total = integer(item.total)
  if (!limit || models.length > limit || total < models.length || models.some(model => model.provider !== id)) return invalid()
  return { providerId: id, models, total, offset: integer(item.offset), limit, source: item.source }
}

/** 查询内置与账号自建供应商及其保存状态，不隐式调用模型。 */
export async function queryAiProviders(signal?: AbortSignal): Promise<ApiResponse<{ providers: AiProviderView[] }>> {
  const response = await aiRequest('providers/query', {}, signal)
  const item = record(response.data)
  if (!Array.isArray(item.providers) || item.providers.length > 100) return invalid()
  return { ...response, data: { providers: item.providers.map(parseProvider) } }
}
/** 保存一个内置供应商的局部凭据表单；返回公开状态，保存成功不等于调用权限检测。 */
export async function saveAiProvider(data: AiProviderSaveRequest, signal?: AbortSignal): Promise<ApiResponse<AiProviderConfigView>> {
  const response = await aiRequest('providers/save', data, signal)
  return { ...response, data: parseProviderConfig(response.data) }
}
/** 清除本站内置供应商凭据及必要默认引用，不撤销上游 Key，不重试删除。 */
export async function deleteAiProvider(providerId: string, signal?: AbortSignal): Promise<ApiResponse<null>> {
  const response = await aiRequest('providers/delete', { providerId }, signal)
  if (response.data !== null) return invalid()
  return { ...response, data: null }
}
/** 新建或更新账号自建供应商；空 Key 表示保留旧值，保存同样不探测调用权限。 */
export async function saveAiCustomProvider(data: AiCustomProviderSaveRequest, signal?: AbortSignal): Promise<ApiResponse<AiCustomProviderView>> {
  const response = await aiRequest('custom-providers/save', data, signal)
  return { ...response, data: parseCustomProvider(response.data) }
}
/** 删除账号自建供应商及其型号与默认引用，不撤销上游 Key。 */
export async function deleteAiCustomProvider(providerId: string, signal?: AbortSignal): Promise<ApiResponse<null>> {
  const response = await aiRequest('custom-providers/delete', { providerId }, signal)
  if (response.data !== null) return invalid()
  return { ...response, data: null }
}
/** 手工录入或更新账号自建型号的能力声明，不向上游探测。 */
export async function saveAiCustomModel(data: AiCustomModelSaveRequest, signal?: AbortSignal): Promise<ApiResponse<AiCatalogModelView>> {
  const response = await aiRequest('custom-models/save', data, signal)
  return { ...response, data: parseCatalogModel(response.data) }
}
/** 删除账号自建型号；默认选择指向它时由服务端一并清除。 */
export async function deleteAiCustomModel(providerId: string, modelId: string, signal?: AbortSignal): Promise<ApiResponse<null>> {
  const response = await aiRequest('custom-models/delete', { providerId, modelId }, signal)
  if (response.data !== null) return invalid()
  return { ...response, data: null }
}
/** 查询当前账号独立默认选择，空状态不会自动补选型号。 */
export async function queryAiSettings(signal?: AbortSignal): Promise<ApiResponse<AiSettingsView | null>> {
  const response = await aiRequest('settings/query', {}, signal)
  return { ...response, data: parseSettings(response.data) }
}
/** 保存用户明确选择的默认型号及状态，不携带 Key 或发送检测请求。 */
export async function saveAiSettings(data: AiSettingsSaveRequest, signal?: AbortSignal): Promise<ApiResponse<AiSettingsView>> {
  const response = await aiRequest('settings/save', data, signal)
  const result = parseSettings(response.data)
  if (!result) return invalid()
  return { ...response, data: result }
}
/** 只清除默认咨询选择，保留各供应商凭据并校验空响应。 */
export async function deleteAiSettings(signal?: AbortSignal): Promise<ApiResponse<null>> {
  const response = await aiRequest('settings/delete', {}, signal)
  if (response.data !== null) return invalid()
  return { ...response, data: null }
}
/** 离线查询目录的搜索页或精确型号，目录元数据不表示账号有调用权限。 */
export async function queryAiModels(data: AiModelsQueryRequest, signal?: AbortSignal): Promise<ApiResponse<AiModelsView>> {
  const response = await aiRequest('models/query', data, signal)
  return { ...response, data: parseModels(response.data) }
}
/** 发一次已确认额度的短文本检测并核对原 UUID 和型号，取消只表示停止等待。 */
export async function checkAiModel(data: AiModelCheckRequest, signal?: AbortSignal): Promise<ApiResponse<AiModelCheckView>> {
  const response = await aiRequest('models/check', data, signal, 45000)
  const item = record(response.data)
  const model = parseModel(item.model)
  if (item.success !== true || item.requestId !== data.requestId || model.provider !== data.providerId || model.id !== data.modelId) return invalid()
  return { ...response, data: { requestId: revision(item.requestId), model, success: true } }
}
