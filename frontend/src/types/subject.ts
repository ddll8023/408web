/** 科目（对应 SubjectResponse，已转驼峰；后端额外冗余的 questionCount 字段与 question_count 转换后同键） */
export interface Subject {
  id: number
  name: string
  code: string
  description?: string | null
  orderNum: number
  enabled: boolean
  questionCount?: number | null
}

/** 科目创建请求 */
export interface SubjectCreateRequest {
  name: string
  code: string
  description?: string | null
  orderNum: number
  enabled: boolean
}

/** 科目更新请求（全部字段可选） */
export interface SubjectUpdateRequest {
  name?: string
  code?: string
  description?: string | null
  orderNum?: number
  enabled?: boolean
}
