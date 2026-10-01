/** 题型（后端 QuestionTypeEnum） */
export type QuestionType = 'CHOICE' | 'ESSAY'

/** 难度（后端 DifficultyEnum） */
export type Difficulty = 'EASY' | 'MEDIUM' | 'HARD'

/** 出题工作台的题目来源类型，用于在同一出题篮内区分模拟题与改编题 */
export type QuestionKind = 'mock' | 'adaptation'

/** 选择题 A-D 选项（对应 QuestionOptions） */
export interface QuestionOptions {
  A: string
  B: string
  C: string
  D: string
}

/** 题目创建共用字段（对应 QuestionCreateFields，已转驼峰） */
export interface QuestionCreateFields {
  questionNumber?: number | null
  questionType?: QuestionType
  title?: string | null
  content: string
  options?: QuestionOptions | null
  answer?: string | null
  /** 分类名称列表 */
  category?: string[] | null
  subjectId?: number | null
  difficulty?: Difficulty | null
}

/** 题目更新共用字段（对应 QuestionUpdateFields，全部可选） */
export interface QuestionUpdateFields {
  questionType?: QuestionType | null
  title?: string | null
  content?: string
  options?: QuestionOptions | null
  answer?: string | null
  category?: string[] | null
  subjectId?: number | null
  difficulty?: Difficulty | null
}
