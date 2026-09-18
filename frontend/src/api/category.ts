/**
 * 分类标签 API
 */
import type { CategoryQuestionType, CategoryNode, CategoryTreeNode, CategoryCreateRequest, CategoryUpdateRequest, CategoryMoveRequest, CategoryStats } from '@/types'
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

export const getAllCategories = (questionType: CategoryQuestionType = 'exam') => {
  return request<CategoryNode[]>({
    url: '/api/exam-category/query',
    method: 'post',
    data: { question_type: questionType }
  })
}

export const getCategoriesBySubject = (subjectId: number, questionType: CategoryQuestionType = 'exam') => {
  return request<CategoryNode[]>({
    url: `/api/exam-category/subject/${subjectId}/query`,
    method: 'post',
    data: { question_type: questionType }
  })
}

export const getEnabledCategoriesBySubject = (subjectId: number) => {
  return request<CategoryNode[]>({
    url: `/api/exam-category/subject/${subjectId}/enabled`,
    method: 'post'
  })
}

export const getEnabledCategoryTreeBySubject = (subjectId: number) => {
  return request<CategoryTreeNode[]>({
    url: `/api/exam-category/subject/${subjectId}/tree/enabled`,
    method: 'post'
  })
}

export const getEnabledCategoryTreeBySubjectWithStats = (subjectId: number, questionType: CategoryQuestionType) => {
  return request<CategoryTreeNode[]>({
    url: `/api/exam-category/subject/${subjectId}/tree/enabled-with-stats`,
    method: 'post',
    data: { question_type: questionType }
  })
}

export const getAvailableParentCategories = (subjectId: number, excludeId: number | null = null) => {
  return request<CategoryNode[]>({
    url: '/api/exam-category/available-parents',
    method: 'post',
    data: convertKeysToSnake({ subjectId, excludeId })
  })
}

export const checkCategoryUsage = (id: number) => {
  return request<number>({
    url: `/api/exam-category/${id}/usage`,
    method: 'post'
  })
}

export const createCategory = (data: CategoryCreateRequest) => {
  return request<CategoryNode>({
    url: '/api/exam-category',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const updateCategory = (id: number, data: CategoryUpdateRequest) => {
  return request<CategoryNode>({
    url: `/api/exam-category/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const moveCategory = (id: number, { targetId = null, position }: CategoryMoveRequest) => {
  return request<CategoryNode[]>({
    url: `/api/exam-category/${id}/move`,
    method: 'post',
    data: convertKeysToSnake({ targetId, position })
  })
}

export const deleteCategory = (id: number) => {
  return request<null>({
    url: `/api/exam-category/${id}/delete`,
    method: 'post'
  })
}

/** 重排科目或指定分类子树的同级编码序号；categoryId 为空时按科目整体重排。 */
export const rebuildCategoryCodes = (subjectId: number, categoryId: number | null = null) => {
  return request<CategoryNode[]>({
    url: '/api/exam-category/rebuild-codes',
    method: 'post',
    data: convertKeysToSnake({ subjectId, categoryId })
  })
}

export const getCategoryStats = (questionType: CategoryQuestionType = 'exam') => {
  return request<CategoryStats>({
    url: '/api/exam-category/stats',
    method: 'post',
    data: { question_type: questionType }
  })
}
