/**
 * 格式化工具函数
 * 遵循 KISS 原则：简单、通用的格式化方法
 */

/**
 * 格式化日期时间
 * @param {string|Date} dateTime - 日期时间
 * @returns {string} 格式化后的字符串
 */
export const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
