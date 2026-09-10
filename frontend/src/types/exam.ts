import type { Difficulty, QuestionCreateFields, QuestionOptions, QuestionType, QuestionUpdateFields } from './question'

/** 真题（对应 ExamResponse，已转驼峰） */
export interface ExamQuestion {
  id: number
  year: number
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

/** 真题分页查询参数（对应 ExamQueryParams，size 为页面分页组件的历史别名，出站前会被映射为 pageSize） */
export interface ExamQueryParams {
  page?: number
  pageSize?: number
  /** 兼容别名：等价于 pageSize */
  size?: number
  year?: number | null
  category?: string | null
  subjectId?: number | null
  noCategory?: boolean | null
  keyword?: string | null
  sortField?: string
  sortOrder?: 'asc' | 'desc'
}

/** 真题年份统计（对应 ExamYearStatResponse） */
export interface ExamYearStat {
  year: number
  count: number
  choiceCount: number
  subjectiveCount: number
}

/** 真题索引项（对应 ExamIndexItem） */
export interface ExamIndexItem {
  id: number
  year: number
  questionNumber?: number | null
}

/** 真题导航索引项（对应 ExamNavItem） */
export interface ExamNavItem {
  id: number
  year: number
  questionNumber?: number | null
  title?: string | null
  category?: string[] | null
}

/** 真题分类统计项（对应 ExamCategoryStatItem） */
export interface ExamCategoryStatItem {
  categoryName: string
  count: number
  choiceCount: number
  subjectiveCount: number
}

/** 真题分类统计树节点（对应 ExamCategoryStatsTreeItem，已转驼峰） */
export interface ExamCategoryStatsTreeItem {
  categoryId: number | null
  parentId: number | null
  categoryName: string
  orderNum: number
  enabled: boolean
  isUnfiled: boolean
  /** 本节点直接引用的题目数 */
  count: number
  choiceCount: number
  subjectiveCount: number
  /** 本节点及后代的题目 ID 去重数 */
  subtreeCount: number
  subtreeChoiceCount: number
  subtreeSubjectiveCount: number
  children: ExamCategoryStatsTreeItem[]
}

/** 单个科目的真题分类统计树（对应 ExamSubjectCategoryStats） */
export interface ExamSubjectCategoryStats {
  subjectId: number | null
  subjectName: string
  totalCount: number
  categoryReferenceCount: number
  categories: ExamCategoryStatsTreeItem[]
}

/** 真题分类统计（对应 ExamCategoryStatsResponse） */
export interface ExamCategoryStats {
  subjectId?: number | null
  subjectName?: string | null
  /** 按题目 ID 去重后的题目总数 */
  totalCount: number
  /** 分类引用总数，一题多分类时分别计入 */
  categoryReferenceCount: number
  /** 保留的平面统计，供兼容和未归档标签使用 */
  stats: ExamCategoryStatItem[]
  /** 按科目、章节和知识点默认层级排列的统计树，表格排序仅作用当前视图 */
  categoryTree: ExamSubjectCategoryStats[]
}

/** 真题查重响应（对应 ExamDuplicateCheckResponse） */
export interface ExamDuplicateCheck {
  isDuplicate: boolean
  existingQuestion?: ExamQuestion | null
}

/** 真题创建请求（对应 ExamCreateRequest） */
export interface ExamCreateRequest extends QuestionCreateFields {
  year: number
  questionNumber?: number | null
}

/** 真题更新请求（对应 ExamUpdateRequest） */
export interface ExamUpdateRequest extends QuestionUpdateFields {
  year?: number | null
  questionNumber?: number | null
}
