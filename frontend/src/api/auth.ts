import type { LoginRequest, RegisterRequest, AuthResponse } from '@/types'
/**
 * 认证相关API
 */
import request from './request'

/**
 * 用户注册
 * @param {Object} data 注册数据
 * @param {string} data.username 用户名
 * @param {string} data.password 密码
 * @param {string} data.email 邮箱
 * @returns {Promise} API响应
 */
export function register(data: RegisterRequest) {
  return request<null>({
    url: '/api/auth/register',
    method: 'post',
    data
  })
}

/**
 * 用户登录
 * @param {Object} data 登录数据
 * @param {string} data.username 用户名
 * @param {string} data.password 密码
 * @returns {Promise} API响应（包含Token）
 */
export function login(data: LoginRequest) {
  return request<AuthResponse>({
    url: '/api/auth/login',
    method: 'post',
    data
  })
}

