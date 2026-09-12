/**
 * 与后端 `backend-fastapi/src/web408/schemas/common.py` 对应的通用响应结构。
 * 拦截器返回的是转换后的信封本身（非 AxiosResponse）。
 */

/** 统一 API 响应信封 `{code, message, data}`，业务成功为 code === 200 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页元数据（对应 PageInfo，已转驼峰） */
export interface PageInfo {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

/** 统一列表分页数据（对应 PaginatedResponse） */
export interface Paginated<T> {
  lists: T[]
  pagination: PageInfo
}

/** 排序方向（后端仅接受 asc/desc） */
export type SortOrder = 'asc' | 'desc'

/** label/value 形式的下拉选项 */
export interface LabeledOption {
  label: string
  value: string | number
}
