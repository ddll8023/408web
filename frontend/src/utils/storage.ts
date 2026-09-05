import type { UserInfo } from '@/types'

/** 本地存储属于外部输入；损坏或不完整的数据不能成为认证状态。 */
export function parseUserInfo(raw: string | null): UserInfo | null {
  if (!raw) return null
  try {
    const value: unknown = JSON.parse(raw)
    if (typeof value !== 'object' || value === null) return null
    if (!('username' in value) || typeof value.username !== 'string' || !('role' in value)) return null
    if (value.role !== 'ADMIN' && value.role !== 'USER' && value.role !== 'GUEST') return null
    return { username: value.username, role: value.role }
  } catch {
    return null
  }
}

export function queryString(value: string | null | (string | null)[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? ''
}
