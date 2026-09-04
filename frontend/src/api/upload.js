/**
 * 文件上传 API 模块
 */
import request, { API_BASE_URL } from './request'

export const uploadImage = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await request({
    url: '/api/upload/image',
    method: 'post',
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    data: formData
  })
  return response.data
}

export const getImageUrl = (relativePath) => {
  return API_BASE_URL + relativePath
}

export const getImageList = (params = {}) => {
  return request({
    url: '/api/upload/images',
    method: 'post',
    data: {
      only_unreferenced: Boolean(params.only_unreferenced)
    }
  })
}

export const deleteImage = (filename) => {
  return request({
    url: '/api/upload/image/delete',
    method: 'post',
    data: { filename, confirm: true }
  })
}

export const deleteUnreferencedImages = () => {
  return request({
    url: '/api/upload/images/cleanup',
    method: 'post',
    data: { confirm: true }
  })
}
