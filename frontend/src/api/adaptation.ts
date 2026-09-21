/**
 * 改编题相关 API：查询、详情、来源解析与反查、覆盖统计和管理端维护。
 * 所有请求走统一 request 封装，请求体统一转换下划线字段名。
 */
import type {
  AdaptationBySourceItem,
  AdaptationCoverageItem,
  AdaptationCreateRequest,
  AdaptationSourceUsageCheck,
  AdaptationQueryParams,
  AdaptationQuestion,
  AdaptationSourceLookupItem,
  AdaptationSourceRefInput,
  AdaptationSubjectStat,
  AdaptationUpdateRequest,
  Paginated
} from '@/types'
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

const normalizeQuery = (params: AdaptationQueryParams = {}) => {
  const normalized = { ...params }
  if (normalized.pageSize === undefined && normalized.size !== undefined) {
    normalized.pageSize = normalized.size
  }
  delete normalized.size
  return convertKeysToSnake(normalized)
}

/** 分页查询改编题 */
export function getAdaptationList(params: AdaptationQueryParams = {}) {
  return request<Paginated<AdaptationQuestion>>({
    url: '/api/adaptation/query',
    method: 'post',
    data: normalizeQuery(params)
  })
}

/** 查询改编题详情（含来源引用） */
export function getAdaptationDetail(id: number) {
  return request<AdaptationQuestion>({
    url: `/api/adaptation/${id}/detail`,
    method: 'post'
  })
}

/** 按科目统计改编题数量 */
export function getAdaptationSubjectStats() {
  return request<AdaptationSubjectStat[]>({
    url: '/api/adaptation/subject-stats',
    method: 'post'
  })
}

/** 查询科目下改编题实际使用的分类名称 */
export function getAdaptationCategoriesBySubject(subjectId: number) {
  return request<string[]>({
    url: `/api/adaptation/categories/${subjectId}`,
    method: 'post'
  })
}

/** 创建改编题 */
export function createAdaptation(data: AdaptationCreateRequest) {
  return request<AdaptationQuestion>({
    url: '/api/adaptation',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

/** 更新改编题 */
export function updateAdaptation(id: number, data: AdaptationUpdateRequest) {
  return request<AdaptationQuestion>({
    url: `/api/adaptation/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

/** 删除改编题 */
export function deleteAdaptation(id: number) {
  return request<null>({
    url: `/api/adaptation/${id}/delete`,
    method: 'post'
  })
}

/** 检查改编题来源是否已被其他题目引用。 */
export function checkAdaptationSourceUsage(data: {
  excludeId?: number | null
  sources?: AdaptationSourceRefInput[]
}) {
  return request<AdaptationSourceUsageCheck>({
    url: '/api/adaptation/check-source-usage',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

/** 批量解析来源引用的真题命中情况 */
export function lookupAdaptationSources(sources: AdaptationSourceRefInput[]) {
  return request<AdaptationSourceLookupItem[]>({
    url: '/api/adaptation/source-lookup',
    method: 'post',
    data: { sources: convertKeysToSnake(sources) }
  })
}

/** 按来源年份与题号反查改编题 */
export function findAdaptationsBySource(data: {
  sourceYear: number
  sourceQuestionNumber: number
  subjectId?: number | null
}) {
  return request<AdaptationBySourceItem[]>({
    url: '/api/adaptation/by-source',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

/** 统计真题改编覆盖情况 */
export function getAdaptationCoverage(data: { subjectId?: number | null; years?: number[] | null } = {}) {
  return request<AdaptationCoverageItem[]>({
    url: '/api/adaptation/source-coverage',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}
