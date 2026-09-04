/**
 * 真题相关 API
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

export function getExamList(params = {}) {
  return request({
    url: '/api/exam/query',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamYearStats(params = {}) {
  return request({
    url: '/api/exam/year-stats',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamIndex(params = {}) {
  return request({
    url: '/api/exam/index',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamNavIndex(params = {}) {
  return request({
    url: '/api/exam/nav-index',
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamDetail(id) {
  return request({
    url: `/api/exam/${id}/detail`,
    method: 'post'
  })
}

export function createExam(data) {
  return request({
    url: '/api/exam',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function updateExam(id, data) {
  return request({
    url: `/api/exam/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export function deleteExam(id) {
  return request({
    url: `/api/exam/${id}/delete`,
    method: 'post'
  })
}

export function getExamByYear(year, params = {}) {
  return request({
    url: `/api/exam/year/${year}`,
    method: 'post',
    data: normalizeQuery(params)
  })
}

export function getExamCategoriesBySubject(subjectId) {
  return request({
    url: `/api/exam/categories/${subjectId}`,
    method: 'post'
  })
}

export function getExamCategoryStats(subjectId) {
  return request({
    url: '/api/exam/category-stats',
    method: 'post',
    data: convertKeysToSnake({ subjectId })
  })
}

export function exportExamsBySubject(subjectId, format = 'markdown') {
  return request({
    url: '/api/exam/export',
    method: 'post',
    responseType: 'blob',
    data: convertKeysToSnake({ subjectId, format })
  })
}
