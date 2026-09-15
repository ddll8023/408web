/** 真题讲解过程图片 API，保持与题目主体查询和维护解耦。 */
import type { ExamProcessImage } from '@/types'
import { convertKeysToSnake } from '@/utils/convertKeys'
import request from './request'

export function listExamProcessImages(examId: number) {
  return request<ExamProcessImage[]>({
    url: `/api/exam/${examId}/process-images`,
    method: 'post',
  })
}

export function uploadExamProcessImage(examId: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)

  return request<ExamProcessImage>({
    url: `/api/exam/${examId}/process-images/upload`,
    method: 'post',
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    data: formData,
  })
}

export function deleteExamProcessImage(examId: number, imageId: number) {
  return request<null>({
    url: `/api/exam/${examId}/process-images/${imageId}/delete`,
    method: 'post',
  })
}

export function reorderExamProcessImages(examId: number, imageIds: number[]) {
  return request<ExamProcessImage[]>({
    url: `/api/exam/${examId}/process-images/reorder`,
    method: 'post',
    data: convertKeysToSnake({ imageIds }),
  })
}
