import type { MockQuestion, MockQueryParams, MockCreateRequest, MockUpdateRequest, MockSources, MockSubjectStat, MockCategoryStats, Paginated } from '@/types'
/**
 * 模拟题 API 模块
 */
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

const normalizeQuery = (params: MockQueryParams = {}) => {
  const normalized = { ...params }
  if (normalized.pageSize === undefined && normalized.size !== undefined) {
    normalized.pageSize = normalized.size
  }
  delete normalized.size
  return convertKeysToSnake(normalized)
}

export function getMockQuestions(params: MockQueryParams = {}) {
  return request<Paginated<MockQuestion>>({
    url: '/api/mock/query',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getMockQuestionById(id: number) {
  return request<MockQuestion>({
    url: `/api/mock/${id}/detail`,
    method: 'post'
  })
}

export function createMockQuestion(data: MockCreateRequest) {
  return request<MockQuestion>({
    url: '/api/mock',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function updateMockQuestion(id: number, data: MockUpdateRequest) {
  return request<MockQuestion>({
    url: `/api/mock/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function deleteMockQuestion(id: number) {
  return request<null>({
    url: `/api/mock/${id}/delete`,
    method: 'post'
  })
}

export function getMockQuestionsBySource(source: string, params: MockQueryParams = {}) {
  return request<MockQuestion[]>({
    url: `/api/mock/source/${encodeURIComponent(source)}`,
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getAllMockSources() {
  return request<MockSources>({
    url: '/api/mock/sources',
    method: 'post'
  })
}

export function getMockCategoriesBySubject(subjectId: number) {
  return request<string[]>({
    url: `/api/mock/categories/${subjectId}`,
    method: 'post'
  })
}

export function getMockSubjectStats() {
  return request<MockSubjectStat[]>({
    url: '/api/mock/subject-stats',
    method: 'post'
  })
}

export function getMockCategoryStatsBySubject(subjectId: number) {
  return request<MockCategoryStats>({
    url: `/api/mock/category-stats/${subjectId}`,
    method: 'post'
  })
}

export function getMockTitlesBySource(source: string) {
  return request<string[]>({
    url: `/api/mock/titles/${encodeURIComponent(source)}`,
    method: 'post'
  })
}
