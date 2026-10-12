/**
 * 自定义分类类型。
 * 字段以 HTTP 拦截器转换后的 camelCase 视图为准。
 */

/** 自定义分类节点（对应 CustomCategoryResponse） */
export interface CustomCategoryNode {
  id: number
  subjectId: number
  subjectName?: string | null
  parentId?: number | null
  parentName?: string | null
  name: string
  /** 系统生成的层级分类编码，创建后不可手动修改 */
  code: string
  description?: string | null
  orderNum: number
  enabled: boolean
}

/** 自定义分类树节点（对应 CustomCategoryTreeResponse） */
export interface CustomCategoryTreeNode extends CustomCategoryNode {
  children: CustomCategoryTreeNode[]
}

/** 自定义分类创建请求（对应 CustomCategoryCreateRequest） */
export interface CustomCategoryCreateRequest {
  subjectId: number
  parentId?: number | null
  name: string
  description?: string | null
  orderNum: number
  enabled?: boolean
}

/** 自定义分类更新请求（对应 CustomCategoryUpdateRequest，全部可选） */
export interface CustomCategoryUpdateRequest {
  subjectId?: number | null
  parentId?: number | null
  name?: string
  description?: string | null
  orderNum?: number
  enabled?: boolean
}

/** 自定义分类拖拽落点（对应 CustomCategoryMoveRequest.position） */
export type CustomCategoryMovePosition = 'before' | 'inside' | 'after'

/** 自定义分类移动请求（对应 CustomCategoryMoveRequest；targetId 为空表示移至顶级末尾） */
export interface CustomCategoryMoveRequest {
  targetId?: number | null
  position: CustomCategoryMovePosition
}

/** 按科目的自定义分类数量统计项（对应 CustomCategorySubjectStatItem） */
export interface CustomCategorySubjectStat {
  subjectId: number
  subjectName: string
  categoryCount: number
  enabledCategoryCount: number
}

/** 自定义分类统计（对应 CustomCategoryStatResponse） */
export interface CustomCategoryStats {
  subjectStats: CustomCategorySubjectStat[]
  totalCategories: number
  enabledCategories: number
}
