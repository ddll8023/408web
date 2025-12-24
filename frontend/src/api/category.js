/**
 * 分类标签API接口
 * 用途：分类标签数据的HTTP请求封装
 * 遵循KISS原则：简单清晰的API方法
 * 
 * 后端路径：/api/exam-category
 */
import request from './request'

/**
 * 查询所有分类
 * @param {String} questionType 题目类型：exam=真题, mock=模拟题（默认exam）
 * @returns Promise
 */
export const getAllCategories = (questionType = 'exam') => {
  return request({
    url: '/api/exam-category',
    method: 'get',
    params: { questionType }
  })
}

/**
 * 按科目查询所有分类（包含引用统计）
 * @param {Number} subjectId 科目ID
 * @param {String} questionType 题目类型：exam=真题, mock=模拟题（默认exam）
 * @returns Promise
 */
export const getCategoriesBySubject = (subjectId, questionType = 'exam') => {
  return request({
    url: `/api/exam-category/subject/${subjectId}`,
    method: 'get',
    params: { questionType }
  })
}

/**
 * 按科目查询启用的分类（用于选择器）
 * @param {Number} subjectId 科目ID
 * @returns Promise
 */
export const getEnabledCategoriesBySubject = (subjectId) => {
  return request({
    url: `/api/exam-category/subject/${subjectId}/enabled`,
    method: 'get'
  })
}

/**
 * 按科目查询分类树形结构
 * @param {Number} subjectId 科目ID
 * @returns Promise - 返回树形结构（顶级分类包含 children）
 */
export const getCategoryTreeBySubject = (subjectId) => {
  return request({
    url: `/api/exam-category/subject/${subjectId}/tree`,
    method: 'get'
  })
}

/**
 * 按科目查询启用的分类树形结构（用于侧边栏）
 * @param {Number} subjectId 科目ID
 * @returns Promise - 返回树形结构
 */
export const getEnabledCategoryTreeBySubject = (subjectId) => {
  return request({
    // 后端路径：/api/exam-category/subject/{subjectId}/tree/enabled
    url: `/api/exam-category/subject/${subjectId}/tree/enabled`,
    method: 'get'
  })
}

/**
 * 按科目和题型查询启用的分类树形结构（带题型特定统计）
 * 用途：模拟题侧边栏需要显示各自的题目数量
 * @param {Number} subjectId 科目ID
 * @param {String} questionType 题目类型：exam=真题, mock=模拟题
 * @returns Promise - 返回树形结构（questionCount 为指定题型的数量）
 */
export const getEnabledCategoryTreeBySubjectWithStats = (subjectId, questionType) => {
  return request({
    // 后端路径：/api/exam-category/subject/{subjectId}/tree/enabled/{questionType}
    url: `/api/exam-category/subject/${subjectId}/tree/enabled/${questionType}`,
    method: 'get'
  })
}

/**
 * 查询可作为父分类的列表（仅顶级分类）
 * @param {Number} subjectId 科目ID
 * @param {Number} excludeId 排除的分类ID（编辑时排除自身）
 * @returns Promise
 */
export const getAvailableParentCategories = (subjectId, excludeId = null) => {
  return request({
    // 后端路径：/api/exam-category/available-parents?subjectId=xxx&excludeId=xxx
    url: `/api/exam-category/available-parents`,
    method: 'get',
    params: { subjectId, ...(excludeId ? { excludeId } : {}) }
  })
}

/**
 * 根据ID查询分类详情
 * @param {Number} id 分类ID
 * @returns Promise
 */
export const getCategoryById = (id) => {
  return request({
    url: `/api/exam-category/${id}`,
    method: 'get'
  })
}

/**
 * 检查分类引用数量
 * @param {Number} id 分类ID
 * @returns Promise
 */
export const checkCategoryUsage = (id) => {
  return request({
    url: `/api/exam-category/${id}/usage`,
    method: 'get'
  })
}

/**
 * 创建分类（ADMIN专用）
 * @param {Object} data 分类数据
 * @returns Promise
 */
export const createCategory = (data) => {
  return request({
    url: '/api/exam-category',
    method: 'post',
    data
  })
}

/**
 * 更新分类（ADMIN专用）
 * @param {Number} id 分类ID
 * @param {Object} data 分类数据
 * @returns Promise
 */
export const updateCategory = (id, data) => {
  return request({
    url: `/api/exam-category/${id}`,
    method: 'post',
    data
  })
}

/**
 * 删除分类（ADMIN专用）
 * @param {Number} id 分类ID
 * @returns Promise
 */
export const deleteCategory = (id) => {
  return request({
    url: `/api/exam-category/${id}/delete`,
    method: 'post'
  })
}

/**
 * 获取分类统计信息（去重后的题目数）
 * 用于解决一道题目有多个标签时的重复计数问题
 * @param {String} questionType 题目类型：exam=真题, mock=模拟题（默认exam）
 * @returns Promise - 返回 { subjectStats: [{subjectId, subjectName, questionCount}], totalQuestionCount }
 */
export const getCategoryStats = (questionType = 'exam') => {
  return request({
    url: '/api/exam-category/stats',
    method: 'get',
    params: { questionType }
  })
}
