/**
 * Token管理工具类
 * 使用localStorage存储JWT Token
 * 遵循KISS原则：简单的存储逻辑
 */

const TOKEN_KEY = 'web408_token'

/**
 * 获取Token
 * @returns {string|null} Token字符串
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 设置Token
 * @param {string} token Token字符串
 */
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 移除Token
 */
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

