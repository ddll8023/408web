/**
 * 对象键名转换工具
 * 用于前后端命名规范转换
 * 遵循：前端驼峰(camelCase) <-> 后端下划线(snake_case)
 */

/**
 * 将下划线命名转换为驼峰命名
 * @param {string} str - 下划线命名字符串
 * @returns {string} 驼峰命名字符串
 */
export const snakeToCamel = (str: string): string => {
  return str.replace(/_([a-z])/g, (_: string, letter: string) => letter.toUpperCase())
}

/**
 * 将驼峰命名转换为下划线命名
 * @param {string} str - 驼峰命名字符串
 * @returns {string} 下划线命名字符串
 */
export const camelToSnake = (str: string): string => {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
}

/**
 * 递归转换对象的所有键名（下划线->驼峰）
 * @param {*} data - 要转换的数据
 * @returns {*} 转换后的数据
 */
export const convertKeysToCamel = (data: unknown): unknown => {
  if (data === null || typeof data !== 'object') {
    return data
  }

  if (Array.isArray(data)) {
    return data.map(item => convertKeysToCamel(item))
  }

  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(data)) {
    const camelKey = snakeToCamel(key)
    // 递归转换嵌套对象，但排除category字段（它是JSON字符串，需要特殊处理）
    if (key === 'category' && typeof value === 'string') {
      result[camelKey] = convertCategoryString(value)
    } else if (typeof value === 'object' && value !== null) {
      result[camelKey] = convertKeysToCamel(value)
    } else {
      result[camelKey] = value
    }
  }
  return result
}

/**
 * 转换分类字段（JSON字符串->数组）
 * @param {string} categoryStr - JSON字符串
 * @returns {Array} 分类数组
 */
export const convertCategoryString = (categoryStr: string): string[] => {
  if (!categoryStr) return []
  try {
    const parsed: unknown = JSON.parse(categoryStr)
    return Array.isArray(parsed) && parsed.every((item: unknown) => typeof item === 'string') ? parsed : []
  } catch {
    return []
  }
}

/**
 * 递归转换请求对象键名（驼峰 -> 下划线）
 * @param {*} data - 请求数据
 * @returns {*} 转换后的请求数据
 */
export const convertKeysToSnake = (data: unknown): unknown => {
  if (data === null || typeof data !== 'object') {
    return data
  }

  if (Array.isArray(data)) {
    return data.map(item => convertKeysToSnake(item))
  }

  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined) continue
    // A-D 是选择题选项的协议键，不是需要改写的字段名。
    const snakeKey = /^[A-D]$/.test(key) ? key : camelToSnake(key)
    result[snakeKey] = convertKeysToSnake(value)
  }
  return result
}
