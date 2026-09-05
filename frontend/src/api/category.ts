import type { CategoryQuestionType, CategoryNode, CategoryTreeNode, CategoryCreateRequest, CategoryUpdateRequest, CategoryMoveRequest, CategoryStats } from '@/types'
/**
 * 分类标签 API
 */
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

export const getCategoryStats = (questionType: CategoryQuestionType = 'exam') => {
  return request<CategoryStats>({
    url: '/api/exam-category/stats',
    method: 'post',
    data: { question_type: questionType }
  })
}
