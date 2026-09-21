/**
 * 改编题领域类型：改编题实体、来源引用、查询参数和来源占用检查结构。
 * 类型以 HTTP 拦截器转换后的 camelCase 视图为准（非后端 snake_case 线格式）。
 */
import type { Difficulty, QuestionCreateFields, QuestionOptions, QuestionType, QuestionUpdateFields } from './question'

/** 来源标注状态（对应 source_state） */
export type AdaptationSourceState = 'all' | 'with_source' | 'without_source'

/** 来源引用输入（对应 AdaptationSourceRefInput） */
export interface AdaptationSourceRefInput {
  sourceYear: number
  sourceQuestionNumber: number
}

/** 来源引用（对应 AdaptationSourceRefResponse） */
export interface AdaptationSourceRef {
  id?: number | null
  sourceYear: number
  sourceQuestionNumber: number
  examQuestionId?: number | null
  /** 真题库中是否命中该题 */
  sourceExists: boolean
  examTitle?: string | null
}

/** 改编题（对应 AdaptationResponse） */
export interface AdaptationQuestion {
  id: number
  title?: string | null
  questionType: QuestionType
  content: string
  options?: QuestionOptions | null
  answer?: string | null
  category?: string[] | null
  subjectId?: number | null
  subjectName?: string | null
  difficulty?: Difficulty | null
  authorId: number
  authorName?: string | null
  createTime?: string | null
  updateTime?: string | null
  sources: AdaptationSourceRef[]
  /** 来源展示摘要，例如「改编自 2021 年第 15 题」 */
  sourceSummary: string
}

/** 改编题分页查询参数（size 为页面分页组件的历史别名，出站前会被映射为 pageSize） */
export interface AdaptationQueryParams {
  page?: number
  pageSize?: number
  /** 兼容别名：等价于 pageSize */
  size?: number
  subjectId?: number | null
  category?: string | null
  noCategory?: boolean | null
  questionType?: QuestionType | null
  keyword?: string | null
  sourceYear?: number | null
  sourceQuestionNumber?: number | null
  sourceState?: AdaptationSourceState
  sortField?: string
  sortOrder?: 'asc' | 'desc'
}

/** 改编题创建请求（对应 AdaptationCreateRequest） */
export interface AdaptationCreateRequest extends Omit<QuestionCreateFields, 'questionNumber'> {
  sources?: AdaptationSourceRefInput[]
}

/** 改编题更新请求（对应 AdaptationUpdateRequest，sources 缺省表示不修改来源） */
export interface AdaptationUpdateRequest extends QuestionUpdateFields {
  sources?: AdaptationSourceRefInput[] | null
}

/** 来源解析结果项（对应 AdaptationSourceLookupItem） */
export interface AdaptationSourceLookupItem {
  sourceYear: number
  sourceQuestionNumber: number
  exists: boolean
  examQuestionId?: number | null
  examTitle?: string | null
  examQuestionType?: QuestionType | null
}

/** 同源改编提示项（对应 AdaptationSourceUsageItem） */
export interface AdaptationSourceUsage {
  sourceYear: number
  sourceQuestionNumber: number
  adaptationId: number
  title?: string | null
}

/** 改编题来源占用检查响应（对应 AdaptationSourceUsageCheckResponse） */
export interface AdaptationSourceUsageCheck {
  reusedSources: AdaptationSourceUsage[]
}
