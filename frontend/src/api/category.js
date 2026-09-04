/**
 * 分类标签 API
 */
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

export const getAllCategories = (questionType = 'exam') => {
  return request({
    url: '/api/exam-category/query',
    method: 'post',
    data: { question_type: questionType }
  })
}

export const getCategoriesBySubject = (subjectId, questionType = 'exam') => {
  return request({
    url: `/api/exam-category/subject/${subjectId}/query`,
    method: 'post',
    data: { question_type: questionType }
  })
}

export const getEnabledCategoriesBySubject = (subjectId) => {
  return request({
    url: `/api/exam-category/subject/${subjectId}/enabled`,
    method: 'post'
  })
}

export const getEnabledCategoryTreeBySubject = (subjectId) => {
  return request({
    url: `/api/exam-category/subject/${subjectId}/tree/enabled`,
    method: 'post'
  })
}

export const getEnabledCategoryTreeBySubjectWithStats = (subjectId, questionType) => {
  return request({
    url: `/api/exam-category/subject/${subjectId}/tree/enabled-with-stats`,
    method: 'post',
    data: { question_type: questionType }
  })
}

export const getAvailableParentCategories = (subjectId, excludeId = null) => {
  return request({
    url: '/api/exam-category/available-parents',
    method: 'post',
    data: convertKeysToSnake({ subjectId, excludeId })
  })
}

export const checkCategoryUsage = (id) => {
  return request({
    url: `/api/exam-category/${id}/usage`,
    method: 'post'
  })
}

export const createCategory = (data) => {
  return request({
    url: '/api/exam-category',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const updateCategory = (id, data) => {
  return request({
    url: `/api/exam-category/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const deleteCategory = (id) => {
  return request({
    url: `/api/exam-category/${id}/delete`,
    method: 'post'
  })
}

export const getCategoryStats = (questionType = 'exam') => {
  return request({
    url: '/api/exam-category/stats',
    method: 'post',
    data: { question_type: questionType }
  })
}
