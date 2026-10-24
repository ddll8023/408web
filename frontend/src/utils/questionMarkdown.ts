import toast from '@/utils/toast'
import { parseQuestionOptions } from '@/utils/questionOptions'

/**
 * 题目 Markdown 复制的公共实现。
 * 真题、模拟题与改编题的阅读页和出题菜单共用换行归一、纯文本剪贴板写入和完整内容拼装，
 * 调用方只负责提供自己的标题行，避免同一套逻辑在多处重复导致行为不一致。
 */

/** 参与 Markdown 复制的题目字段，三类题目共用。 */
export interface MarkdownCopyQuestion {
  questionType?: string | null
  content?: string | null
  options?: unknown
  answer?: string | null
  category?: string[] | string | null
  /** 自定义分类名称数组，仅真题提供；导出标签优先使用它 */
  customCategory?: string[] | null
}

/** 完整内容复制的菜单命令与标题级别映射。 */
const fullMarkdownLevels: Record<string, number> = {
  'md-all-1': 1,
  'md-all-2': 2,
  'md-all-3': 3,
  'md-all-4': 4
}

/** 将复制命令转换为完整内容复制的标题级别；非完整内容命令返回 null。 */
export const resolveFullMarkdownLevel = (command: string): number | null => {
  return fullMarkdownLevels[command] ?? null
}

/**
 * 换行归一：在常见编号模式前补换行，并去掉内容里的空行。
 * 支持罗马数字、圆括号数字、带圈数字、方括号数字和大写字母括号五种模式。
 * 只有编号紧跟在中文或中英文标点之后才断行，避免拆散加粗标记、行内公式与行内代码。
 */
export const normalizeLineBreaks = (text?: string | null): string => {
  if (!text || typeof text !== 'string') return ''

  const patterns = [
    // 罗马数字模式: I. II. III. IV. V. VI. VII. VIII. IX. X. XI. XII.
    /(?<!\n)(?<=[\u4e00-\u9fff。；;！!？?：:，,、）)】》])\s*((?:I{1,3}|IV|VI{0,3}|IX|X{1,3}|XI{1,3}|XII)\.\s)/gi,
    // 圆括号数字模式: (1) (2) (3) ...
    /(?<!\n)(?<=[\u4e00-\u9fff。；;！!？?：:，,、）)】》])\s*(\([1-9]\d?\)\s*)/g,
    // 带圈数字模式: ① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ 等
    /(?<!\n)(?<=[\u4e00-\u9fff。；;！!？?：:，,、）)】》])\s*([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])/g,
    // 方括号数字模式: [1] [2] [3] ...
    /(?<!\n)(?<=[\u4e00-\u9fff。；;！!？?：:，,、）)】》])\s*(\[[1-9]\d?\]\s*)/g,
    // 大写字母括号模式: (A) (B) (C) (D) 等
    /(?<!\n)(?<=[\u4e00-\u9fff。；;！!？?：:，,、）)】》])\s*(\([A-Z]\)\s*)/g
  ]

  let result = text
  patterns.forEach(pattern => {
    result = result.replace(pattern, '\n$1')
  })

  // 复制内容不保留空行，连续换行统一压成单个换行。
  return result.replace(/\n{2,}/g, '\n')
}

/**
 * 把内容里原有的 Markdown 标题整体下移，使最浅标题落在目标级别。
 * 内容内部的相对层级保持不变，超过六级的部分封顶在六级；围栏代码块内的行不改写。
 */
export const shiftHeadings = (text: string, targetLevel: number): string => {
  const lines = text.split('\n')
  const insideFence: boolean[] = []
  let fenceMarker = ''

  lines.forEach(line => {
    const fence = line.match(/^\s*(`{3,}|~{3,})/)
    if (fence) {
      if (!fenceMarker) fenceMarker = fence[1][0]
      else if (fence[1][0] === fenceMarker) fenceMarker = ''
      insideFence.push(true)
      return
    }
    insideFence.push(Boolean(fenceMarker))
  })

  const levels: number[] = []
  lines.forEach((line, index) => {
    if (insideFence[index]) return
    const heading = line.match(/^(#{1,6})\s/)
    if (heading) levels.push(heading[1].length)
  })

  if (levels.length === 0) return text

  const offset = targetLevel - Math.min(...levels)
  if (offset === 0) return text

  return lines
    .map((line, index) => {
      if (insideFence[index]) return line
      const heading = line.match(/^(#{1,6})(\s.*)$/)
      if (!heading) return line
      const level = Math.min(6, Math.max(1, heading[1].length + offset))
      return `${'#'.repeat(level)}${heading[2]}`
    })
    .join('\n')
}

/** 写入纯文本剪贴板，非安全上下文回退到临时 textarea。 */
export const copyTextToClipboard = async (text: string): Promise<void> => {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-999999px'
  textArea.style.top = '-999999px'
  document.body.appendChild(textArea)
  try {
    textArea.focus()
    textArea.select()
    if (!document.execCommand('copy')) throw new Error('COPY_FAILED')
  } finally {
    document.body.removeChild(textArea)
  }
}

/** 题目标签：[题型] [分类]；分类优先取自定义分类，为空时回退大纲分类。 */
export const buildTagLine = (question: MarkdownCopyQuestion): string => {
  const questionType = question.questionType === 'CHOICE' ? '选择题' : '主观题'
  const customCategory = Array.isArray(question.customCategory) ? question.customCategory.join(', ') : ''
  const outlineCategory = Array.isArray(question.category) ? question.category.join(', ') : (question.category || '')
  const tags = [questionType, customCategory || outlineCategory].filter(Boolean)
  return tags.length > 0 ? `[${tags.join('] [')}]` : ''
}

/** 真题标题行：年份与题号，缺失项自动省略。 */
export const buildExamTitleLine = (exam: { year?: number | null; questionNumber?: number | null }): string => {
  const year = exam.year ? `${exam.year}年` : ''
  const questionNumber = exam.questionNumber ? `第${exam.questionNumber}题` : ''
  return [year, questionNumber].filter(Boolean).join(' ')
}

/** 模拟题标题行：标题与题号，两者都缺失时回退为「模拟题」。 */
export const buildMockTitleLine = (mock: { title?: string | null; questionNumber?: number | null }): string => {
  const parts = []
  if (mock.title) parts.push(mock.title)
  if (mock.questionNumber) parts.push(`第${mock.questionNumber}题`)
  return parts.join(' · ') || '模拟题'
}

/** 选择题选项拼装为「A. 内容」形式，选项以围栏代码块开头时字母独占一行；主观题或解析失败返回空串。 */
const buildOptionsMarkdown = (question: MarkdownCopyQuestion): string => {
  if (question.questionType !== 'CHOICE' || !question.options) return ''

  let options: Record<string, string> | null = null
  try {
    options = parseQuestionOptions(question.options)
  } catch (error) {
    console.error('解析选项失败:', error)
    return ''
  }
  if (!options) return ''

  return Object.keys(options)
    .sort()
    .map(key => {
      const text = normalizeLineBreaks(options[key])
      // 选项以围栏代码块（如 svg 题图）开头时，字母必须独占一行，否则围栏不在行首，Markdown 不会按代码块解析。
      return /^\s*(`{3,}|~{3,})/.test(text) ? `${key}.\n${text}` : `${key}. ${text}`
    })
    .join('\n')
}

/**
 * 表格块前后补空行。
 * 复制内容不保留空行，而 Obsidian/GFM 的表格不能中断段落，缺少前置空行时不会被识别为表格。
 */
const ensureTableBlankLines = (text: string): string => {
  const lines = text.split('\n')
  const isTableRow = (line: string | undefined): boolean => /^\s*\|.*\|\s*$/.test(line ?? '')
  const isTableDelimiter = (line: string | undefined): boolean => /^\s*\|[\s:|-]+\|\s*$/.test(line ?? '')
  const result: string[] = []

  lines.forEach((line, index) => {
    // 表头行（下一行为分隔行）前补空行，避免严格 GFM 解析器不识别表格。
    const last = result[result.length - 1]
    if (isTableRow(line) && isTableDelimiter(lines[index + 1]) && last !== undefined && last !== '') result.push('')
    result.push(line)
    // 表格末行后补空行，避免后续内容被并入表格。
    const inTable = isTableRow(lines[index - 1]) || isTableDelimiter(lines[index - 1])
    if (isTableRow(line) && inTable && !isTableRow(lines[index + 1]) && lines[index + 1] !== undefined && lines[index + 1] !== '') {
      result.push('')
    }
  })

  return result.join('\n')
}

/** 拼装完整题目 Markdown：题目标题用所选级别，题目/选项/答案低一级，段间不留空行，仅表格块前后补空行。 */
export const buildFullMarkdown = (question: MarkdownCopyQuestion, titleLine: string, level: number): string => {
  const heading = '#'.repeat(level)
  const sectionHeading = '#'.repeat(level + 1)
  const parts: string[] = []

  const title = [titleLine, buildTagLine(question)].filter(Boolean).join(' ')
  if (title) parts.push(`${heading} ${title}`)

  const content = normalizeLineBreaks(question.content)
  if (content) parts.push(`${sectionHeading} 题目`, shiftHeadings(content, level + 2))

  const options = buildOptionsMarkdown(question)
  if (options) parts.push(`${sectionHeading} 选项`, options)

  const answer = normalizeLineBreaks(question.answer)
  if (answer) parts.push(`${sectionHeading} 答案`, shiftHeadings(answer, level + 2))

  if (parts.length === 0) return ''
  // 末尾留一个空行，粘贴后光标落在下一行。
  return `${ensureTableBlankLines(parts.join('\n'))}\n`
}

/**
 * 完整内容复制入口：按命令取标题级别，拼装文本并写入剪贴板。
 * 无内容、成功与失败均在此提示，调用方无需重复处理；
 * 返回值只表示是否真正写入剪贴板，供需要联动出题状态的调用方判断。
 */
export const copyFullMarkdown = async (
  command: string,
  question: MarkdownCopyQuestion,
  titleLine: string
): Promise<boolean> => {
  const level = resolveFullMarkdownLevel(command)
  if (!level) return false

  const text = buildFullMarkdown(question, titleLine, level)
  if (!text) {
    toast.warning('没有可复制的内容')
    return false
  }

  try {
    await copyTextToClipboard(text)
    toast.success('完整内容已复制 (Markdown)')
    return true
  } catch (error) {
    console.error('复制失败:', error)
    toast.error('复制失败，请重试')
    return false
  }
}
