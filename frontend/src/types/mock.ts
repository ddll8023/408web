import type { Difficulty, QuestionCreateFields, QuestionOptions, QuestionType, QuestionUpdateFields } from './question'

/** 模拟题（对应 MockResponse，已转驼峰） */
export interface MockQuestion {
  id: number
  source: string
  questionNumber?: number | null
  questionType: QuestionType
  title?: string | null
  content: string
  options?: QuestionOptions | null
  answer?: string | null
  /** 拦截器已将后端 JSON 字符串统一解析为数组，此处是前端视图形状而非线格式 */
  category?: string[] | null
  subjectId?: number | null
  subjectName?: string | null
  difficulty?: Difficulty | null
  authorId: number
  authorName?: string | null
  createTime?: string | null
  updateTime?: string | null
}

/** 模拟题分页查询参数（对应 MockQueryParams，size 为页面分页组件的历史别名） */
export interface MockQueryParams {
  page?: number
  pageSize?: number
  /** 兼容别名：等价于 pageSize */
  size?: number
  source?: string | null
  category?: string | null
  subjectId?: number | null
  noCategory?: boolean | null
  keyword?: string | null
  sortField?: string
  sortOrder?: 'asc' | 'desc'
}

/** 模拟题来源统计项（对应 MockSourceStatResponse） */
export interface MockSourceStat {
  source: string
  count: number
}

/** 模拟题来源列表项（对应 MockSourceItem） */
export interface MockSourceItem {
  source: string
  questionCount: number
}

/** 模拟题来源列表（对应 MockSourcesResponse） */
export interface MockSources {
  sources: MockSourceItem[]
}

/** 模拟题分类统计（对应 MockCategoryStatsResponse） */
export interface MockCategoryStats {
  subjectId: number
  subjectName?: string | null
  stats: { category: string; count: number }[]
  totalCount: number
}

/** 按科目统计项（对应 MockSubjectStatItem） */
export interface MockSubjectStat {
  subjectId: number
  subjectName: string
  count: number
}

/** 模拟题查重响应（对应 MockDuplicateCheckResponse） */
export interface MockDuplicateCheck {
  isDuplicate: boolean
  existingQuestion?: MockQuestion | null
}

/** 模拟题创建请求（对应 MockCreateRequest） */
export interface MockCreateRequest extends QuestionCreateFields {
  source: string
}

/** 模拟题更新请求（对应 MockUpdateRequest） */
export interface MockUpdateRequest extends QuestionUpdateFields {
  source?: string | null
  questionNumber?: number | null
}
