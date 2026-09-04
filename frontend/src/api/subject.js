/**
 * 科目 API
 */
import request from './request'
import { convertKeysToSnake } from '@/utils/convertKeys'

export const getEnabledSubjects = () => {
  return request({
    url: '/api/subject/query',
    method: 'post'
  })
}

export const getAllSubjects = () => {
  return request({
    url: '/api/subject/query-all',
    method: 'post'
  })
}

export const getSubjectById = (id) => {
  return request({
    url: `/api/subject/${id}/detail`,
    method: 'post'
  })
}

export const createSubject = (data) => {
  return request({
    url: '/api/subject',
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const updateSubject = (id, data) => {
  return request({
    url: `/api/subject/${id}`,
    method: 'post',
    data: convertKeysToSnake(data)
  })
}

export const deleteSubject = (id) => {
  return request({
    url: `/api/subject/${id}/delete`,
    method: 'post'
  })
}
