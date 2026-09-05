/** 提取可展示的错误信息，不假设 catch 收到的值具有 Axios 结构。 */
export function errorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null) {
    if ('response' in error && typeof error.response === 'object' && error.response !== null && 'data' in error.response) {
      const data = error.response.data
      if (typeof data === 'object' && data !== null && 'message' in data && typeof data.message === 'string' && data.message) return data.message
    }
    if ('message' in error && typeof error.message === 'string' && error.message) return error.message
  }
  return fallback
}
