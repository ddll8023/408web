/**
 * 章节API接口
 * 用途：章节数据的HTTP请求封装
 * 遵循KISS原则：简单清晰的API方法
 * Source: Axios官方文档
 */
import request from './request'

/**
 * 查询科目的启用章节树
 * @param {Number} subjectId 科目ID
 * @returns Promise
 */
export const getEnabledChapterTree = (subjectId) => {
  return request({
    url: `/api/chapter/subject/${subjectId}`,
    method: 'get'
  })
}

/**
 * 查询科目的所有章节树（包含禁用，ADMIN专用）
 * @param {Number} subjectId 科目ID
 * @returns Promise
 */
export const getChapterTree = (subjectId) => {
  return request({
    url: `/api/chapter/subject/${subjectId}/all`,
    method: 'get'
  })
}
/**
 * 创建章节（ADMIN专用）
 * @param {Object} data 章节数据
 * @returns Promise
 */
export const createChapter = (data) => {
  return request({
    url: '/api/chapter',
    method: 'post',
    data
  })
}

/**
 * 更新章节（ADMIN专用）
 * @param {Number} id 章节ID
 * @param {Object} data 章节数据
 * @returns Promise
 */
export const updateChapter = (id, data) => {
  return request({
    url: `/api/chapter/${id}`,
    method: 'post',
    data
  })
}

/**
 * 删除章节（ADMIN专用）
 * @param {Number} id 章节ID
 * @returns Promise
 */
export const deleteChapter = (id) => {
  return request({
    url: `/api/chapter/${id}/delete`,
    method: 'post'
  })
}

