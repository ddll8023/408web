/** 答案生成的数据转换与基本格式检查；不把格式合格当作答案正确。 */
import MarkdownIt, { type Token } from 'markdown-it'
import type { QuestionType } from '@/types'
import type { QuestionForm } from '@/composables/questionFormTypes'
import type { AiAnswerSource } from '@/types/aiAnswer'
import { parseQuestionOptions } from '@/utils/questionOptions'

const answerMarkdown = new MarkdownIt('commonmark', { html: true })

interface QuestionSource {
  questionType: QuestionType
  subjectId?: number | null
  content: string
  options?: unknown
  answer?: string | null
}

export function answerSourceFromQuestion(question: QuestionSource): AiAnswerSource {
  const options = parseQuestionOptions(question.options)
  return {
    questionType: question.questionType,
    subjectId: question.subjectId ?? null,
    content: question.content,
    options: question.questionType === 'CHOICE' && options
      ? { A: options.A, B: options.B, C: options.C, D: options.D } : null,
    answer: question.answer || null,
  }
}

export function answerSourceFromForm(form: QuestionForm): AiAnswerSource {
  return {
    questionType: form.questionType,
    subjectId: form.subjectId,
    content: form.content,
    options: form.questionType === 'CHOICE'
      ? { A: form.optionA, B: form.optionB, C: form.optionC, D: form.optionD } : null,
    answer: form.answer || null,
  }
}

/** 固定字段顺序，同时检测题面和原答案变化，避免采用覆盖生成期间的新编辑。 */
export function answerSourceKey(source: AiAnswerSource): string {
  return JSON.stringify([
    source.questionType, source.subjectId, source.content,
    source.options ? [source.options.A, source.options.B, source.options.C, source.options.D] : null,
    source.answer || null,
  ])
}

export function answerSourceError(source: AiAnswerSource): string {
  if (!source.content.trim()) return '请先填写题干'
  if (source.questionType === 'CHOICE' && (!source.options || Object.values(source.options).some(text => !text.trim()))) {
    return '请先完善 A-D 四个选项'
  }
  return ''
}

/** 仅校验可机械识别的首行和围栏；求解正确性与是否需要图示仍由用户判断。 */
export function generatedAnswerError(answer: string, type: QuestionType): string {
  const text = answer.trim()
  const firstLine = text.split(/\r?\n/, 1)[0]
  if (type === 'CHOICE' ? !/^\*\*正确答案：[A-D]+\*\*$/.test(firstLine) : firstLine !== '**答案**') {
    return '答案首行不符合题库格式，或模型未能可靠求解，请重新生成'
  }
  if (type === 'CHOICE') {
    const letters = firstLine.slice('**正确答案：'.length, -2)
    if (letters !== [...new Set(letters)].sort().join('')) return '答案字母须按 A-D 顺序排列且不能重复'
  }
  const tokens = answerMarkdown.parse(text, {})
  const lines = text.split(/\r?\n/)
  for (const token of tokens) {
    if (token.type !== 'fence' || !token.map) continue
    const closing = lines[token.map[1] - 1]?.trim().match(/^(`{3,}|~{3,})$/)?.[1]
    if (!closing || closing[0] !== token.markup[0] || closing.length < token.markup.length) {
      return '答案代码块尚未闭合，请重新生成'
    }
  }
  function hasUnsafeMarkup(items: Token[]): boolean {
    return items.some(token => token.type === 'html_block' || token.type === 'html_inline' || token.type === 'image'
      || (token.children !== null && hasUnsafeMarkup(token.children)))
  }
  if (hasUnsafeMarkup(tokens)) return '新答案包含图示代码块之外的 HTML 或图片，请重新生成'
  if (!text.includes('\n') || !text.slice(firstLine.length).trim()) return '缺少答案解析，请重新生成'
  return ''
}
