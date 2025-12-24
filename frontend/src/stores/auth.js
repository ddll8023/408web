/**
 * 认证状态管理Store
 * 使用Pinia管理用户信息和Token
 * 遵循单一职责原则：只管理认证相关状态
 * 
 * Source: Pinia 2.1.7 官方文档
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getToken, setToken as saveToken, removeToken } from '@/utils/token'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(getToken())
  
  // 从localStorage恢复用户信息
  const savedUserInfo = localStorage.getItem('userInfo')
  const userInfo = ref(savedUserInfo ? JSON.parse(savedUserInfo) : null)

  /**
   * 设置Token
   * @param {string} newToken Token字符串
   */
  function setToken(newToken) {
    token.value = newToken
    saveToken(newToken)
  }

  /**
   * 设置用户信息
   * @param {Object} info 用户信息对象
   */
  function setUserInfo(info) {
    userInfo.value = info
    // 持久化到localStorage
    if (info) {
      localStorage.setItem('userInfo', JSON.stringify(info))
    } else {
      localStorage.removeItem('userInfo')
    }
  }

  /**
   * 清除认证信息
   */
  function clearAuth() {
    token.value = null
    userInfo.value = null
    removeToken()
    localStorage.removeItem('userInfo')
  }

  /**
   * 检查是否已登录
   * @returns {boolean} true-已登录，false-未登录
   */
  function isLoggedIn() {
    return !!token.value
  }

  /**
   * 检查是否为管理员
   * @returns {boolean} true-是管理员，false-不是管理员
   */
  function isAdmin() {
    return userInfo.value && userInfo.value.role === 'ADMIN'
  }

  return {
    token,
    userInfo,
    setToken,
    setUserInfo,
    clearAuth,
    isLoggedIn,
    isAdmin
  }
})

