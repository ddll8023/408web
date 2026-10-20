/** 答案生成的数据转换与格式检查；不把格式合格当作答案正确，也不校验内容是否正确。 */
import MarkdownIt, { type Token } from 'markdown-it'
import type { QuestionType } from '@/types'
import type { QuestionForm } from '@/composables/questionFormTypes'
import type { AiAnswerSource } from '@/types/aiAnswer'
import { parseQuestionOptions } from '@/utils/questionOptions'

const answerMarkdown = new MarkdownIt('commonmark', { html: true })

/** 选择题允许的加粗小节；与答案生成提示词的封闭模板保持一致。 */
const FEATURE_SECTIONS = new Set(['解析', '选项辨析'])
/** 主观题除逐小问解析外只允许“答案”与“解析”两个加粗小节。 */
const ESSAY_SECTIONS = new Set(['答案', '解析'])
/** 单独一行加粗即视为小节标题，用于定位非法小节。 */
const BOLD_LINE = /^\*\*(.+?)\*\*$/
/** 主观题逐小问解析标题，如“(1) 解析”。 */
const NUMBERED_SECTION = /^[（(]\s*\d+\s*[）)]\s*解析$/
/** 选择题首行的正确答案行，属规定格式而非非法小节。 */
const ANSWER_KEY_LINE = /^\*\*正确答案：[A-D]+\*\*$/
/** 禁止的 Markdown 标题行，代码块内部不参与判断。 */
const MARKDOWN_HEADING = /^#{1,6}\s/
/** 禁止的分隔线与斜体小标题。 */
const DIVIDER_LINE = /^(?:-{3,}|\*{3,}|_{3,})$/
const ITALIC_LINE = /^\*[^*\s][^*]*\*$/

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

/**
 * 校验答案小节结构：收集代码块外的加粗小标题，禁止白名单外的标题、Markdown 标题、分隔线与斜体小标题，
 * 并要求选择题出现必备的选项辨析。返回首个违规说明；无违规返回空字符串。
 */
function answerStructureError(text: string, type: QuestionType): string {
  const allowed = type === 'CHOICE' ? FEATURE_SECTIONS : ESSAY_SECTIONS
  let fenceMarker = ''
  let hasOptionReview = false
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim()
    const fence = line.match(/^(`{3,}|~{3,})$/)
    if (fence) {
      if (!fenceMarker) fenceMarker = fence[1][0]
      else if (fence[1][0] === fenceMarker) fenceMarker = ''
      continue
    }
    if (fenceMarker || !line) continue
    if (MARKDOWN_HEADING.test(line)) return '新答案包含 Markdown 标题小节，请重新生成'
    if (DIVIDER_LINE.test(line)) return '新答案包含分隔线，请重新生成'
    const bold = line.match(BOLD_LINE)
    if (bold) {
      const title = bold[1].trim()
      if (ANSWER_KEY_LINE.test(bold[0])) continue
      if (title === '选项辨析') hasOptionReview = true
      if (allowed.has(title)) continue
      if (type === 'ESSAY' && NUMBERED_SECTION.test(title)) continue
      return '新答案包含多余小节，请重新生成'
    }
    if (ITALIC_LINE.test(line)) return '新答案包含斜体小节标题，请重新生成'
  }
  if (type === 'CHOICE' && !hasOptionReview) return '选择题缺少选项辨析，请重新生成'
  return ''
}

/** 仅校验可机械识别的首行、小节结构与围栏；求解正确性与是否需要图示仍由用户判断。 */
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
  const structureError = answerStructureError(text, type)
  if (structureError) return structureError
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
