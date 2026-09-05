/** 分类统计的题目类型（对应 CategoryQueryRequest.question_type） */
export type CategoryQuestionType = 'exam' | 'mock' | 'exercise'

/** 分类节点（对应 ExamCategoryResponse，已转驼峰） */
export interface CategoryNode {
  id: number
  subjectId: number
  subjectName?: string | null
  parentId?: number | null
  parentName?: string | null
  name: string
  code: string
  description?: string | null
  orderNum: number
  enabled: boolean
  questionCount?: number | null
  subtreeQuestionCount?: number | null
}

/** 分类树节点（对应 ExamCategoryTreeResponse） */
export interface CategoryTreeNode extends CategoryNode {
  children: CategoryTreeNode[]
}

/** 分类创建请求（对应 ExamCategoryCreateRequest） */
export interface CategoryCreateRequest {
  subjectId: number
  parentId?: number | null
  name: string
  code: string
  description?: string | null
  orderNum: number
  enabled?: boolean
}

/** 分类更新请求（对应 ExamCategoryUpdateRequest，全部可选） */
export interface CategoryUpdateRequest {
  subjectId?: number | null
  parentId?: number | null
  name?: string
  code?: string
  description?: string | null
  orderNum?: number
  enabled?: boolean
}

/** 分类拖拽落点（对应 ExamCategoryMoveRequest.position） */
export type CategoryMovePosition = 'before' | 'inside' | 'after'

/** 分类移动请求（对应 ExamCategoryMoveRequest；targetId 为空表示移至顶级末尾） */
export interface CategoryMoveRequest {
  targetId?: number | null
  position: CategoryMovePosition
}

/** 按科目的分类统计项（对应 SubjectStatItem） */
export interface CategorySubjectStat {
  subjectId: number
  subjectName: string
  categoryCount: number
  enabledCategoryCount: number
  questionCount: number
}

/** 分类统计（对应 ExamCategoryStatResponse） */
export interface CategoryStats {
  subjectStats: CategorySubjectStat[]
  totalQuestionCount: number
  totalCategories: number
  enabledCategories: number
  questionType: CategoryQuestionType
}

/** 分类引用检查（对应 ExamCategoryUsageResponse） */
export interface CategoryUsage {
  id: number
  name: string
  hasChildren: boolean
  questionCount: number
  mockCount: number
  canDelete: boolean
}
