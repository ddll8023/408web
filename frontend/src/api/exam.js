/**
 * 真题相关API
 */
import request from './request'

/**
 * 获取真题列表（分页）
 * @param {Object} params 查询参数
 * @param {number} params.page 页码（从1开始）
 * @param {number} params.size 每页大小
 * @param {number} params.year 年份（可选）
 * @param {string} params.category 分类（可选）
 * @param {string} params.difficulty 难度（可选）
 * @param {string} params.keyword 搜索关键词（可选，匹配title或content）
 * @returns {Promise} API响应（分页数据）
 */
export function getExamList(params) {
  return request({
    url: '/api/exam',
    method: 'get',
    params
  })
}

export function getExamYearStats(params) {
  return request({
    url: '/api/exam/year-stats',
    method: 'get',
    params
  })
}

export function getExamIndex(params) {
  return request({
    url: '/api/exam/index',
    method: 'get',
    params
  })
}

/**
 * 获取真题导航索引（轻量级，用于侧边栏）
 * @param {object} params 筛选参数
 * @returns {Promise} API响应（轻量级索引数据）
 */
export function getExamNavIndex(params) {
  return request({
    url: '/api/exam/nav-index',
    method: 'get',
    params
  })
}

/**
 * 获取真题详情
 * @param {number} id 真题ID
 * @returns {Promise} API响应（真题详情）
 */
export function getExamDetail(id) {
  return request({
    url: `/api/exam/${id}`,
    method: 'get'
  })
}

/**
 * 创建真题（仅ADMIN）
 * @param {Object} data 真题数据
 * @param {number} data.year 年份
 * @param {number} data.questionNumber 题号（可选）
 * @param {string} data.title 标题（可选）
 * @param {string} data.content 题目内容（Markdown）
 * @param {string} data.answer 答案（Markdown，可选）
 * @param {string} data.category 分类
 * @param {string} data.difficulty 难度（可选）
 * @returns {Promise} API响应
 */
export function createExam(data) {
  return request({
    url: '/api/exam',
    method: 'post',
    data
  })
}

/**
 * 更新真题（仅ADMIN）
 * @param {number} id 真题ID
 * @param {Object} data 真题数据
 * @returns {Promise} API响应
 */
export function updateExam(id, data) {
  return request({
    url: `/api/exam/${id}`,
    method: 'post',
    data
  })
}

/**
 * 删除真题（仅ADMIN）
 * @param {number} id 真题ID
 * @returns {Promise} API响应
 */
export function deleteExam(id) {
  return request({
    url: `/api/exam/${id}/delete`,
    method: 'post'
  })
}

/**
 * 获取指定年份的所有真题(按题号排序)
 * 用于年份页面展示：一次性加载指定年份的所有题目
 * @param {number} year 年份
 * @returns {Promise} API响应(真题列表)
 */
export function getExamByYear(year, params) {
  return request({
    url: `/api/exam/year/${year}`,
    method: 'get',
    params
  })
}

/**
 * 按科目查询该科目下实际存在真题的分类列表
 * 由后端聚合分类，前端仅负责展示
 * @param {number} subjectId 科目ID
 * @returns {Promise} API响应（分类名称字符串数组）
 */
export function getExamCategoriesBySubject(subjectId) {
  return request({
    url: `/api/exam/categories/${subjectId}`,
    method: 'get'
  })
}

/**
 * 获取真题分类统计信息
 * @param {number} subjectId 科目ID（可选）
 * @returns {Promise} API响应（分类统计列表）
 */
export function getExamCategoryStats(subjectId) {
  return request({
    url: '/api/exam/category-stats',
    method: 'get',
    params: { subjectId }
  })
}

