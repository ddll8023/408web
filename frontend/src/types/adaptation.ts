/**
 * 改编题领域类型：改编题实体、来源引用、查询参数、查重、反查与覆盖统计结构。
 * 类型以 HTTP 拦截器转换后的 camelCase 视图为准（非后端 snake_case 线格式）。
 */
import type { Difficulty, QuestionCreateFields, QuestionOptions, QuestionType, QuestionUpdateFields } from './question'

/** 来源标注状态（对应 source_state） */
export type AdaptationSourceState = 'all' | 'with_source' | 'without_source'

/** 来源引用输入（对应 AdaptationSourceRefInput） */
export interface AdaptationSourceRefInput {
  sourceYear: number
  sourceQuestionNumber: number
  /** 小问或备注，整题留空 */
  sourcePart?: string | null
}

/** 来源引用（对应 AdaptationSourceRefResponse） */
export interface AdaptationSourceRef {
  id?: number | null
  sourceYear: number
  sourceQuestionNumber: number
  sourcePart: string
  examQuestionId?: number | null
  /** 真题库中是否命中该题 */
  sourceExists: boolean
  examTitle?: string | null
}

/** 改编题（对应 AdaptationResponse） */
export interface AdaptationQuestion {
  id: number
  title?: string | null
  questionNumber?: number | null
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
export interface AdaptationCreateRequest extends QuestionCreateFields {
  sources?: AdaptationSourceRefInput[]
}

/** 改编题更新请求（对应 AdaptationUpdateRequest，sources 缺省表示不修改来源） */
export interface AdaptationUpdateRequest extends QuestionUpdateFields {
  questionNumber?: number | null
  sources?: AdaptationSourceRefInput[] | null
}

/** 来源解析结果项（对应 AdaptationSourceLookupItem） */
export interface AdaptationSourceLookupItem {
  sourceYear: number
  sourceQuestionNumber: number
  sourcePart: string
  exists: boolean
  examQuestionId?: number | null
  examTitle?: string | null
  examQuestionType?: QuestionType | null
}

/** 同源改编提示项（对应 AdaptationSourceUsageItem） */
export interface AdaptationSourceUsage {
  sourceYear: number
  sourceQuestionNumber: number
  sourcePart: string
  adaptationId: number
  title?: string | null
}

/** 改编题查重响应（对应 AdaptationDuplicateCheckResponse） */
export interface AdaptationDuplicateCheck {
  isDuplicate: boolean
  existingQuestion?: AdaptationQuestion | null
  reusedSources: AdaptationSourceUsage[]
}

/** 按来源反查结果项（对应 AdaptationBySourceItem） */
export interface AdaptationBySourceItem {
  id: number
  title?: string | null
  questionNumber?: number | null
  questionType: QuestionType
  subjectId?: number | null
  subjectName?: string | null
  sourcePart: string
  updateTime?: string | null
}

/** 覆盖统计单题项（对应 AdaptationCoverageCountItem） */
export interface AdaptationCoverageCount {
  questionNumber: number
  adaptationCount: number
}

/** 年份改编覆盖统计项（对应 AdaptationCoverageItem） */
export interface AdaptationCoverageItem {
  year: number
  total: number
  adapted: number
  missingNumbers: number[]
  /** 无法对应真题库的来源引用条数 */
  danglingSources: number
  counts: AdaptationCoverageCount[]
}

/** 科目改编题统计项（对应 AdaptationSubjectStatItem） */
export interface AdaptationSubjectStat {
  subjectId: number
  subjectName: string
  count: number
}
