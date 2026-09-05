/** 图片引用的真题信息（对应 ImageUsageResponse） */
export interface ImageUsageExam {
  id: number
  year?: number | null
  questionNumber?: number | null
  title: string
}

/** 图片资源（对应 ImageResourceResponse，已转驼峰） */
export interface ImageResource {
  filename: string
  url: string
  size: number
  /** 毫秒时间戳 */
  lastModified: number
  referenced: boolean
  exams: ImageUsageExam[]
}
