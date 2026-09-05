/**
 * Axios HTTP客户端封装
 * 配置请求/响应拦截器
 * 遵循KISS原则：简单的拦截器逻辑
 * 
 * Source: Axios 1.7.2 官方文档
 */
import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'
import { getToken, removeToken } from '@/utils/token'
import { toast } from '@/utils/toast'
import { convertKeysToCamel } from '@/utils/convertKeys'

// 创建axios实例
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:7785'

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 请求拦截器
 * 自动添加Token到请求头
 */
client.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: unknown) => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * 统一处理响应和错误
 */
client.interceptors.response.use(
  response => {
    if (response.config?.responseType === 'blob' || response.config?.responseType === 'arraybuffer') {
      return response
    }

    const res: unknown = response.data
    if (!isApiResponse(res)) {
      toast.error('响应格式错误')
      return Promise.reject(new Error('响应格式错误'))
    }
    if (res.code !== 200) {
      toast.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    response.data = { ...res, data: convertKeysToCamel(res.data) }
    return response
  },
  (error: unknown) => {
    console.error('响应错误：', error)

    // HTTP状态码错误处理
    if (axios.isAxiosError<{ message?: string }>(error) && error.response) {
      const status = error.response.status
      const message = error.response.data?.message || '请求失败'
      const reqUrl = error.config?.url || ''
      const reqMethod = (error.config?.method || '').toLowerCase()

      switch (status) {
        case 401:
          // 登录接口凭证错误：展示后端消息，不清除 Token、不跳转
          if (reqUrl.includes('/api/auth/login') && reqMethod === 'post') {
            toast.error(message || '用户名或密码错误')
          } else {
            // 其他接口 401：按过期处理
            toast.error('登录已过期，请重新登录')
            removeToken()
            // 跳转到登录页
            window.location.href = '/login'
          }
          break
        case 403:
          toast.error('没有权限访问')
          break
        case 404:
          toast.error('请求的资源不存在')
          break
        case 500:
          // 展示后端返回的业务错误消息（如重复校验失败等），而非笼统的"服务器错误"
          toast.error(message || '服务器错误')
          break
        default:
          toast.error(message)
      }
    } else {
      toast.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

function isApiResponse(value: unknown): value is ApiResponse<unknown> {
  return typeof value === 'object' && value !== null &&
    'code' in value && typeof value.code === 'number' &&
    'message' in value && typeof value.message === 'string' && 'data' in value
}

/** JSON 响应由统一拦截器校验信封并转换字段，泛型描述各接口已核对的业务契约。 */
type JsonRequestConfig = Omit<AxiosRequestConfig, 'responseType'> & { responseType?: 'json' }

export default async function request<T>(config: JsonRequestConfig): Promise<ApiResponse<T>> {
  const response = await client.request<ApiResponse<T>>(config)
  return response.data
}

/** 文件下载保留响应头，避免与 JSON 业务信封混用。 */
export function requestBlob(config: AxiosRequestConfig): Promise<AxiosResponse<Blob>> {
  return client.request<Blob>({ ...config, responseType: 'blob' })
}
