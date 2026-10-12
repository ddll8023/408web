/**
 * 自定义分类 API
 */
import type {
  CustomCategoryNode,
  CustomCategoryStats,
  CustomCategoryTreeNode,
  CustomCategoryCreateRequest,
  CustomCategoryUpdateRequest,
  CustomCategoryMoveRequest,
} from '@/types'
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

export const getCustomCategoryTree = (subjectId: number, options: { enabledOnly?: boolean } = {}) => {
  return request<CustomCategoryTreeNode[]>({
    url: `/api/custom-category/subject/${subjectId}/tree`,
    method: 'post',
    data: { enabledOnly: options.enabledOnly ?? false }
  })
}

export const getCustomCategoryStats = () => {
  return request<CustomCategoryStats>({
    url: '/api/custom-category/stats',
    method: 'post'
  })
}

export const getAvailableParentCustomCategories = (subjectId: number, excludeId: number | null = null) => {
  return request<CustomCategoryNode[]>({
    url: '/api/custom-category/available-parents',
    method: 'post',
    data: convertKeysToSnake({ subjectId, excludeId })
  })
}

export const createCustomCategory = (data: CustomCategoryCreateRequest) => {
  return request<CustomCategoryNode>({
    url: '/api/custom-category',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const updateCustomCategory = (id: number, data: CustomCategoryUpdateRequest) => {
  return request<CustomCategoryNode>({
    url: `/api/custom-category/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const moveCustomCategory = (id: number, { targetId = null, position }: CustomCategoryMoveRequest) => {
  return request<CustomCategoryNode[]>({
    url: `/api/custom-category/${id}/move`,
    method: 'post',
    data: convertKeysToSnake({ targetId, position })
  })
}

export const deleteCustomCategory = (id: number) => {
  return request<null>({
    url: `/api/custom-category/${id}/delete`,
    method: 'post'
  })
}

/** 重排科目或指定分类子树的同级编码序号；categoryId 为空时按科目整体重排。 */
export const rebuildCustomCategoryCodes = (subjectId: number, categoryId: number | null = null) => {
  return request<CustomCategoryNode[]>({
    url: '/api/custom-category/rebuild-codes',
    method: 'post',
    data: convertKeysToSnake({ subjectId, categoryId })
  })
}
