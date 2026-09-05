import type { ExamQuestion, ExamQueryParams, ExamYearStat, ExamNavItem, ExamCategoryStats, ExamCreateRequest, ExamUpdateRequest, Paginated } from '@/types'
/**
 * 真题相关 API
 */
import request, { requestBlob } from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

const normalizeQuery = (params: ExamQueryParams = {}) => {
  const normalized = { ...params }
  if (normalized.pageSize === undefined && normalized.size !== undefined) {
    normalized.pageSize = normalized.size
  }
  delete normalized.size
  return convertKeysToSnake(normalized)
}

export function getExamList(params: ExamQueryParams = {}) {
  return request<Paginated<ExamQuestion>>({
    url: '/api/exam/query',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamYearStats(params: ExamQueryParams = {}) {
  return request<ExamYearStat[]>({
    url: '/api/exam/year-stats',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamNavIndex(params: ExamQueryParams = {}) {
  return request<ExamNavItem[]>({
    url: '/api/exam/nav-index',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamDetail(id: number) {
  return request<ExamQuestion>({
    url: `/api/exam/${id}/detail`,
    method: 'post'
  })
}

export function createExam(data: ExamCreateRequest) {
  return request<ExamQuestion>({
    url: '/api/exam',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function updateExam(id: number, data: ExamUpdateRequest) {
  return request<ExamQuestion>({
    url: `/api/exam/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function deleteExam(id: number) {
  return request<null>({
    url: `/api/exam/${id}/delete`,
    method: 'post'
  })
}

export function getExamByYear(year: number, params: ExamQueryParams = {}) {
  return request<ExamQuestion[]>({
    url: `/api/exam/year/${year}`,
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamCategoriesBySubject(subjectId: number) {
  return request<string[]>({
    url: `/api/exam/categories/${subjectId}`,
    method: 'post'
  })
}

export function getExamCategoryStats(subjectId?: number | null) {
  return request<ExamCategoryStats>({
    url: '/api/exam/category-stats',
    method: 'post',
    data: convertKeysToSnake({ subjectId })
  })
}

export function exportExamsBySubject(subjectId: number, format: 'markdown' = 'markdown') {
  return requestBlob({
    url: '/api/exam/export',
    method: 'post',
    responseType: 'blob',
    data: convertKeysToSnake({ subjectId, format })
  })
}
