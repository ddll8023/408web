import type { Subject, SubjectCreateRequest, SubjectUpdateRequest } from '@/types'
/**
 * 科目 API
 */
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

export const getEnabledSubjects = () => {
  return request<Subject[]>({
    url: '/api/subject/query',
    method: 'post'
  })
}

export const getAllSubjects = () => {
  return request<Subject[]>({
    url: '/api/subject/query-all',
    method: 'post'
  })
}

export const getSubjectById = (id: number) => {
  return request<Subject>({
    url: `/api/subject/${id}/detail`,
    method: 'post'
  })
}

export const createSubject = (data: SubjectCreateRequest) => {
  return request<Subject>({
    url: '/api/subject',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const updateSubject = (id: number, data: SubjectUpdateRequest) => {
  return request<Subject>({
    url: `/api/subject/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const deleteSubject = (id: number) => {
  return request<null>({
    url: `/api/subject/${id}/delete`,
    method: 'post'
  })
}
