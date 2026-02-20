/**
 * 模拟题API模块
 * 提供模拟题的增删改查接口
 * 遵循KISS原则：简洁的API设计
 */
import request from './request'

/**
 * 分页查询模拟题
 * @param {Object} params 查询参数
 * @param {number} params.page 页码
 * @param {number} params.size 每页大小
 * @param {string} params.source 来源机构（可选）
 * @param {string} params.category 分类（可选）
 * @param {string} params.difficulty 难度（可选）
 * @param {number} params.subjectId 科目ID（可选）
 * @param {string} params.keyword 搜索关键词（可选，匹配title或content）
 * @param {string} params.sortField 排序字段（可选）
 * @param {string} params.sortOrder 排序方向（可选）
 * @returns {Promise} API响应
 */
export function getMockQuestions(params) {
  return request({
    url: '/api/mock',
    method: 'get',
    params
  })
}

/**
 * 根据ID获取模拟题详情
 * @param {number} id 模拟题ID
 * @returns {Promise} API响应
 */
export function getMockQuestionById(id) {
  return request({
    url: `/api/mock/${id}`,
    method: 'get'
  })
}

/**
 * 创建模拟题
 * @param {Object} data 模拟题数据
 * @returns {Promise} API响应
 */
export function createMockQuestion(data) {
  return request({
    url: '/api/mock',
    method: 'post',
    data
  })
}

/**
 * 更新模拟题
 * @param {number} id 模拟题ID
 * @param {Object} data 模拟题数据
 * @returns {Promise} API响应
 */
export function updateMockQuestion(id, data) {
  return request({
    url: `/api/mock/${id}`,
    method: 'post',  // 后端使用 @PostMapping，需要用 POST 方法
    data
  })
}

/**
 * 删除模拟题
 * @param {number} id 模拟题ID
 * @returns {Promise} API响应
 */
export function deleteMockQuestion(id) {
  return request({
    url: `/api/mock/${id}/delete`,
    method: 'post'
  })
}

/**
 * 根据来源获取模拟题列表
 * @param {string} source 来源机构
 * @param {Object} params 其他参数
 * @returns {Promise} API响应
 */
export function getMockQuestionsBySource(source, params = {}) {
  return request({
    url: `/api/mock/source/${encodeURIComponent(source)}`,
    method: 'get',
    params
  })
}

/**
 * 获取所有来源机构列表
 * @returns {Promise} API响应
 */
export function getAllMockSources() {
  return request({
    url: '/api/mock/sources',
    method: 'get'
  })
}

/**
 * 根据科目获取分类列表
 * @param {number} subjectId 科目ID
 * @returns {Promise} API响应
 */
export function getMockCategoriesBySubject(subjectId) {
  return request({
    url: `/api/mock/categories/${subjectId}`,
    method: 'get'
  })
}

/**
 * 按科目统计模拟题数量
 * @returns {Promise} API响应
 */
export function getMockSubjectStats() {
  return request({
    url: '/api/mock/subject-stats',
    method: 'get'
  })
}

/**
 * 根据来源获取标题列表
 * 用于编辑模拟题时的标题下拉选项
 * @param {string} source 来源机构
 * @returns {Promise} API响应
 */
export function getMockTitlesBySource(source) {
  return request({
    url: `/api/mock/titles/${encodeURIComponent(source)}`,
    method: 'get'
  })
}
