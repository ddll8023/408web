import type { ImageResource } from '@/types'
/**
 * 文件上传 API 模块
 */
import request, { API_BASE_URL } from './request'

export const uploadImage = async (file: Blob) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await request<string>({
    url: '/api/upload/image',
    method: 'post',
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    data: formData
  })
  return response.data
}

export const getImageUrl = (relativePath: string) => {
  return API_BASE_URL + relativePath
}

export const getImageList = (params: { onlyUnreferenced?: boolean } = {}) => {
  return request<ImageResource[]>({
    url: '/api/upload/images',
    method: 'post',
    data: {
      only_unreferenced: Boolean(params.onlyUnreferenced)
    }
  })
}

export const deleteImage = (filename: string) => {
  return request<null>({
    url: '/api/upload/image/delete',
    method: 'post',
    data: { filename, confirm: true }
  })
}

export const deleteUnreferencedImages = () => {
  return request<number>({
    url: '/api/upload/images/cleanup',
    method: 'post',
    data: { confirm: true }
  })
}
