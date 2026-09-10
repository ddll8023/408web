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

const IMAGE_PATH_PREFIX = '/uploads/images/'

/**
 * 将图片地址统一映射到当前后端，兼容历史数据中的旧域名和端口。
 * 非上传目录图片保持原值，避免影响外部图片或前端静态资源。
 */
export const getImageUrl = (imagePath: string) => {
  const value = imagePath.trim()
  if (!value) return ''

  const baseUrl = API_BASE_URL.replace(/\/+$/, '')
  try {
    const parsed = new URL(value, `${baseUrl}/`)
    if (!parsed.pathname.startsWith(IMAGE_PATH_PREFIX)) {
      return value
    }
    return `${baseUrl}${parsed.pathname}${parsed.search}${parsed.hash}`
  } catch {
    return value
  }
}

/** 将 Markdown 或 HTML 中的后端图片地址转换为当前可访问地址。 */
export const normalizeImageUrls = (markdown: string) => {
  if (!markdown) return markdown

  const normalizedMarkdown = markdown.replace(
    /(!\[[^\]]*\]\()([^\s)]+)([^)]*\))/g,
    (_match, prefix: string, url: string, suffix: string) =>
      `${prefix}${getImageUrl(url)}${suffix}`,
  )

  return normalizedMarkdown.replace(
    /(<img\b[^>]*\bsrc\s*=\s*["'])([^"']+)(["'])/gi,
    (_match, prefix: string, url: string, suffix: string) =>
      `${prefix}${getImageUrl(url)}${suffix}`,
  )
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
