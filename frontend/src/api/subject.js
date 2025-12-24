/**
 * 科目API接口
 * 用途：科目数据的HTTP请求封装
 * 遵循KISS原则：简单清晰的API方法
 * Source: Axios官方文档
 */
import request from './request'

/**
 * 查询所有启用的科目
 * @returns Promise
 */
export const getEnabledSubjects = () => {
  return request({
    url: '/api/subject',
    method: 'get'
  })
}

/**
 * 查询所有科目（包含禁用，ADMIN专用）
 * @returns Promise
 */
export const getAllSubjects = () => {
  return request({
    url: '/api/subject/all',
    method: 'get'
  })
}
/**
 * 创建科目（ADMIN专用）
 * @param {Object} data 科目数据
 * @returns Promise
 */
export const createSubject = (data) => {
  return request({
    url: '/api/subject',
    method: 'post',
    data
  })
}

/**
 * 更新科目（ADMIN专用）
 * @param {Number} id 科目ID
 * @param {Object} data 科目数据
 * @returns Promise
 */
export const updateSubject = (id, data) => {
  return request({
    url: `/api/subject/${id}`,
    method: 'post',
    data
  })
}

/**
 * 删除科目（ADMIN专用）
 * @param {Number} id 科目ID
 * @returns Promise
 */
export const deleteSubject = (id) => {
  return request({
    url: `/api/subject/${id}/delete`,
    method: 'post'
  })
}

