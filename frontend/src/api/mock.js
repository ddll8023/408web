/**
 * 模拟题 API 模块
 */
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

const normalizeQuery = (params = {}) => {
  const normalized = { ...params }
  if (normalized.page_size === undefined && normalized.size !== undefined) {
    normalized.page_size = normalized.size
  }
  delete normalized.size
  return convertKeysToSnake(normalized)
}

export function getMockQuestions(params = {}) {
  return request({
    url: '/api/mock/query',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getMockQuestionById(id) {
  return request({
    url: `/api/mock/${id}/detail`,
    method: 'post'
  })
}

export function createMockQuestion(data) {
  return request({
    url: '/api/mock',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function updateMockQuestion(id, data) {
  return request({
    url: `/api/mock/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function deleteMockQuestion(id) {
  return request({
    url: `/api/mock/${id}/delete`,
    method: 'post'
  })
}

export function getMockQuestionsBySource(source, params = {}) {
  return request({
    url: `/api/mock/source/${encodeURIComponent(source)}`,
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getAllMockSources() {
  return request({
    url: '/api/mock/sources',
    method: 'post'
  })
}

export function getMockCategoriesBySubject(subjectId) {
  return request({
    url: `/api/mock/categories/${subjectId}`,
    method: 'post'
  })
}

export function getMockSubjectStats() {
  return request({
    url: '/api/mock/subject-stats',
    method: 'post'
  })
}

export function getMockCategoryStatsBySubject(subjectId) {
  return request({
    url: `/api/mock/category-stats/${subjectId}`,
    method: 'post'
  })
}

export function getMockTitlesBySource(source) {
  return request({
    url: `/api/mock/titles/${encodeURIComponent(source)}`,
    method: 'post'
  })
}
