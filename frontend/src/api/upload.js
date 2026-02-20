/**
 * 文件上传API模块
 * 统一管理所有文件上传相关的API请求
 * 遵循KISS原则：简单的上传接口封装
 * 遵循SOLID原则：单一职责，与其他API模块保持一致
 *
 * Source: 项目统一的 request.js axios实例
 */
import request, { API_BASE_URL } from './request'

/**
 * 上传图片文件
 * @param {File} file - 图片文件对象
 * @returns {Promise<string>} 返回图片的访问路径（相对路径，如：/uploads/images/xxx.png）
 */
export const uploadImage = async (file) => {
  // 创建FormData
  const formData = new FormData()
  formData.append('file', file)
  
  // 使用项目统一的 request 实例发送请求
  // request 已配置：baseURL、Token拦截器、错误处理
  const response = await request({
    url: '/api/upload/image',
    method: 'POST',
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    data: formData
  })
  
  // 返回图片路径（后端返回的相对路径）
  return response.data
}

/**
 * 获取完整图片URL
 * 将相对路径转换为完整的HTTP URL
 * @param {string} relativePath - 相对路径（如：/uploads/images/xxx.png）
 * @returns {string} 完整的图片URL
 */
export const getImageUrl = (relativePath) => {
  return API_BASE_URL + relativePath
}

export const getImageList = (params) => {
  return request({
    url: '/api/upload/images',
    method: 'get',
    params
  })
}

export const deleteImage = (filename) => {
  return request({
    url: '/api/upload/image/delete',
    method: 'post',
    params: { filename }
  })
}

export const deleteUnreferencedImages = () => {
  return request({
    url: '/api/upload/images/cleanup',
    method: 'post'
  })
}
