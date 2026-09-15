/** 真题讲解过程图片（对应 ExamProcessImageResponse，已转驼峰）。 */
export interface ExamProcessImage {
  id: number
  examId: number
  filename: string
  url: string
  sortOrder: number
  createTime?: string | null
  updateTime?: string | null
}
