/** 题目表单类型与 JSON 导入边界，区分通用题目字段和改编题来源引用。 */
import type { AdaptationSourceRefInput, Difficulty, QuestionType, QuestionOptions } from '@/types'

export interface QuestionForm {
  questionType: QuestionType
  subjectId: number | null
  title: string
  content: string
  optionA: string
  optionB: string
  optionC: string
  optionD: string
  answer: string
  category: string[]
  difficulty: Difficulty | ''
  year: number
  source: string
  questionNumber: number | null
}
export interface QuestionFormData {
  questionType?: QuestionType
  question_type?: QuestionType
  subjectId?: number | null
  subject_id?: number | null
  title?: string | null
  content?: string
  answer?: string | null
  category?: string[] | string | null
  difficulty?: Difficulty | null
  options?: Partial<QuestionOptions> | string | null
  year?: number
  source?: string
  questionNumber?: number | null
  sources?: AdaptationSourceRefInput[]
}
export function parseOptions(value: unknown): Partial<QuestionOptions> {
  const parsed: unknown = typeof value === 'string' ? JSON.parse(value) : value
  if (!parsed || typeof parsed !== 'object') return {}
  return {
    A: 'A' in parsed && typeof parsed.A === 'string' ? parsed.A : '',
    B: 'B' in parsed && typeof parsed.B === 'string' ? parsed.B : '',
    C: 'C' in parsed && typeof parsed.C === 'string' ? parsed.C : '',
    D: 'D' in parsed && typeof parsed.D === 'string' ? parsed.D : ''
  }
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
export function validateImportedQuestion(value: unknown): QuestionFormData {
  if (!isRecord(value)) throw new Error('题目必须是 JSON 对象')
  const result: QuestionFormData = {}
  for (const key of ['title', 'content', 'answer', 'source'] as const) {
    if (key in value) {
      const field = value[key]
      if (field !== null && typeof field !== 'string') throw new Error(`${key} 必须为字符串`)
      if (typeof field === 'string') result[key] = field
    }
  }
  for (const key of ['year', 'subjectId', 'subject_id', 'questionNumber'] as const) {
    if (key in value) {
      const field = value[key]
      if (field !== null && (typeof field !== 'number' || !Number.isFinite(field))) throw new Error(`${key} 必须为数字`)
      if (typeof field === 'number') result[key] = field
    }
  }
  for (const key of ['questionType', 'question_type'] as const) {
    if (key in value && value[key] != null && value[key] !== '') {
      const field = value[key]
      if (field !== 'CHOICE' && field !== 'ESSAY') throw new Error(`${key} 必须是 CHOICE 或 ESSAY`)
      result[key] = field
    }
  }
  if ('difficulty' in value && value.difficulty != null && value.difficulty !== '') {
    if (value.difficulty !== 'EASY' && value.difficulty !== 'MEDIUM' && value.difficulty !== 'HARD') throw new Error('difficulty 必须是 EASY、MEDIUM 或 HARD')
    result.difficulty = value.difficulty
  }
  if ('category' in value) {
    const field = value.category
    if (typeof field === 'string' || field === null) result.category = field
    else if (Array.isArray(field) && field.every((item: unknown) => typeof item === 'string')) result.category = field
    else throw new Error('category 必须是字符串或字符串数组')
  }
  if ('options' in value) result.options = parseOptions(value.options)
  if ('sources' in value) {
    if (!Array.isArray(value.sources)) throw new Error('sources 必须是数组')
    result.sources = value.sources.map((item: unknown, index: number) => {
      if (!isRecord(item)) throw new Error(`sources[${index}] 必须是对象`)
      const sourceYear = item.sourceYear
      const sourceQuestionNumber = item.sourceQuestionNumber
      if (
        typeof sourceYear !== 'number' ||
        !Number.isInteger(sourceYear) ||
        sourceYear < 1990 ||
        sourceYear > 2100
      ) {
        throw new Error(`sources[${index}].sourceYear 必须是 1990—2100 的整数`)
      }
      if (
        typeof sourceQuestionNumber !== 'number' ||
        !Number.isInteger(sourceQuestionNumber) ||
        sourceQuestionNumber < 1 ||
        sourceQuestionNumber > 47
      ) {
        throw new Error(`sources[${index}].sourceQuestionNumber 必须是 1—47 的整数`)
      }
      return { sourceYear, sourceQuestionNumber }
    })
  }
  return result
}
