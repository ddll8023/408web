/**
 * Axios HTTP客户端封装
 * 配置请求/响应拦截器
 * 遵循KISS原则：简单的拦截器逻辑
 * 
 * Source: Axios 1.7.2 官方文档
 */
import axios from 'axios'
import { getToken, removeToken } from '@/utils/token'
import { ElMessage } from 'element-plus'

// 创建axios实例
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'

const request = axios.create({
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
request.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * 统一处理响应和错误
 */
request.interceptors.response.use(
  response => {
    const res = response.data

    // 判断业务状态码
    if (res.code === 200) {
      return res
    } else {
      // 业务错误
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  error => {
    console.error('响应错误：', error)

    // HTTP状态码错误处理
    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.message || '请求失败'
      const reqUrl = error.config?.url || ''
      const reqMethod = (error.config?.method || '').toLowerCase()

      switch (status) {
        case 401:
          // 登录接口凭证错误：展示后端消息，不清除 Token、不跳转
          if (reqUrl.includes('/api/auth/login') && reqMethod === 'post') {
            ElMessage.error(message || '用户名或密码错误')
          } else {
            // 其他接口 401：按过期处理
            ElMessage.error('登录已过期，请重新登录')
            removeToken()
            // 跳转到登录页
            window.location.href = '/login'
          }
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          // 展示后端返回的业务错误消息（如重复校验失败等），而非笼统的"服务器错误"
          ElMessage.error(message || '服务器错误')
          break
        default:
          ElMessage.error(message)
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

export default request

