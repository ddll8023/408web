/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 基础地址（生产构建时注入） */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'vue-router' {
  interface RouteMeta {
    /** 需要登录才能访问 */
    requiresAuth?: boolean
    /** 需要管理员权限才能访问 */
    requiresAdmin?: boolean
  }
}
