/** 用户角色（后端 UserRoleEnum） */
export type UserRole = 'ADMIN' | 'USER' | 'GUEST'

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
}

/** 注册请求 */
export interface RegisterRequest {
  username: string
  password: string
  email?: string | null
}

/** 认证成功响应（对应 AuthResponse） */
export interface AuthResponse {
  token: string
  username: string
  role: UserRole
}

/** 本地持久化的用户信息（localStorage `userInfo`） */
export interface UserInfo {
  username: string
  role: UserRole
}
