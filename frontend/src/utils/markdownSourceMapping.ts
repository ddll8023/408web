/** Markdown 预览解析：保留原始源码范围，并在 HTML 安全清洗后生成公式 DOM。 */
import type MarkdownIt from 'markdown-it'
import katex from 'katex'
import { normalizeImageUrls } from '@/api/upload'

/** 一次完成 DOM 更新的预览；源码用于拒绝已经过期的渲染结果。 */
export interface MarkdownRenderSnapshot {
  source: string
  revision: number
}

interface PreparedSource {
  text: string
  starts: number[]
  ends: number[]
  length: number
}

interface MathMatch {
  content: string
  end: number
  display: boolean
}

const sourceKey = Symbol('markdown-source')
interface SourceEnvironment {
  [sourceKey]?: PreparedSource
}

type RenderToken = Parameters<MarkdownIt['renderer']['render']>[0][number]

/** 反斜杠数量为奇数时，分隔符只是字面量。 */
const isEscaped = (text: string, offset: number) => {
  let slashes = 0
  for (let index = offset - 1; index >= 0 && text[index] === '\\'; index -= 1) slashes += 1
  return slashes % 2 === 1
}

/** 只识别完整公式；未闭合的定界符交还 Markdown 按普通文字处理。 */
const readMath = (text: string, start: number): MathMatch | null => {
  if (isEscaped(text, start)) return null
  const opener = text.startsWith('$$', start) ? '$$'
    : text.startsWith('\\[', start) ? '\\['
      : text.startsWith('\\(', start) ? '\\('
        : text[start] === '$' ? '$' : ''
  if (!opener) return null
  const closer = opener === '\\[' ? '\\]' : opener === '\\(' ? '\\)' : opener
  const display = opener === '$$' || opener === '\\['
  const contentStart = start + opener.length
  for (let end = text.indexOf(closer, contentStart); end >= 0; end = text.indexOf(closer, end + closer.length)) {
    if (isEscaped(text, end)) continue
    if (opener === '$' && (text[end - 1] === '$' || text[end + 1] === '$')) continue
    const content = text.slice(contentStart, end)
    if (!content.trim() || (opener === '$' && /[\r\n]/.test(content))) return null
    return { content, end: end + closer.length, display }
  }
  return null
}

/** 寻找相同长度的反引号闭合串，避免把行内代码中的公式或字面换行当成语法。 */
const codeSpanEnd = (text: string, start: number) => {
  const marker = text.slice(start).match(/^`+/)?.[0]
  if (!marker) return null
  for (let end = text.indexOf(marker, start + marker.length); end >= 0; end = text.indexOf(marker, end + marker.length)) {
    if (text[end - 1] !== '`' && text[end + marker.length] !== '`') return end + marker.length
  }
  return null
}

/**
 * 换行归一只执行一次，逐行记录原始字符边界，不进行公式占位或多轮行号补偿。
 * 真换行、CRLF 与旧数据的字面换行都保留来源；公式、代码和原始媒体内部不展开字面换行。
 */
const prepareSource = (source: string): PreparedSource => {
  const output: string[] = []
  const starts = [0]
  const ends: number[] = []
  let cursor = 0
  let atLineStart = true
  let fence: { marker: string; length: number } | null = null

  const appendOriginal = (end: number) => {
    while (cursor < end) {
      const char = source[cursor]
      if (char === '\r' || char === '\n') {
        ends.push(cursor)
        cursor += char === '\r' && source[cursor + 1] === '\n' ? 2 : 1
        starts.push(cursor)
        output.push('\n')
        atLineStart = true
      } else {
        output.push(char)
        cursor += 1
        atLineStart = false
      }
    }
  }

  while (cursor < source.length) {
    if (atLineStart) {
      let end = cursor
      while (end < source.length && source[end] !== '\r' && source[end] !== '\n') end += 1
      const line = source.slice(cursor, end)
      // 同时保护引用、列表中常见的围栏缩进；这里只保护文字，不代替 Markdown 的块语法判定。
      const marker = line.match(/^[ \t]*(?:>[ \t]*)*(?:[-+*][ \t]+|\d+[.)][ \t]+)?(`{3,}|~{3,})(.*)$/)
      if (fence) {
        if (marker && marker[1][0] === fence.marker && marker[1].length >= fence.length && !marker[2].trim()) fence = null
        appendOriginal(end)
        // 连同物理换行推进，空代码行也不能停留在原位置。
        if (cursor < source.length) appendOriginal(cursor + (source[cursor] === '\r' && source[cursor + 1] === '\n' ? 2 : 1))
        continue
      }
      if (marker) {
        fence = { marker: marker[1][0], length: marker[1].length }
        appendOriginal(end)
        if (cursor < source.length) appendOriginal(cursor + (source[cursor] === '\r' && source[cursor + 1] === '\n' ? 2 : 1))
        continue
      }
      const unquoted = line.replace(/^(?: {0,3}>[ \t]?)+/, '')
      if (/^(?: {4}|\t)/.test(unquoted)) {
        appendOriginal(end)
        if (cursor < source.length) appendOriginal(cursor + (source[cursor] === '\r' && source[cursor + 1] === '\n' ? 2 : 1))
        continue
      }
    }

    const rawTag = source[cursor] === '<'
      ? source.slice(cursor).match(/^<(svg|pre|code|script|style|textarea)\b[^>]*>/i)
      : null
    if (rawTag) {
      const closing = new RegExp(`</${rawTag[1]}\\s*>`, 'ig')
      closing.lastIndex = cursor + rawTag[0].length
      const match = closing.exec(source)
      if (match) {
        appendOriginal(match.index + match[0].length)
        continue
      }
    }
    if (source[cursor] === '`' && !isEscaped(source, cursor)) {
      const end = codeSpanEnd(source, cursor)
      if (end !== null) {
        appendOriginal(end)
        continue
      }
    }
    if (source[cursor] === '$' || source[cursor] === '\\') {
      const math = readMath(source, cursor)
      if (math) {
        appendOriginal(math.end)
        continue
      }
    }
    if (source.startsWith('\\n', cursor) && !isEscaped(source, cursor)) {
      ends.push(cursor)
      cursor += 2
      starts.push(cursor)
      output.push('\n')
      atLineStart = true
      continue
    }
    appendOriginal(cursor + (source[cursor] === '\r' && source[cursor + 1] === '\n' ? 2 : 1))
  }
  ends.push(source.length)
  return { text: normalizeImageUrls(output.join('')), starts, ends, length: source.length }
}

/**
 * 只在 HTML 清洗及 DOM 提交完成后生成公式，避免安全过滤器删除 KaTeX 的定位样式。
 * 节点内容始终按不可信 LaTeX 文本处理；只有 trust:false 的 KaTeX 输出可写入 innerHTML。
 */
export const renderParsedMarkdownMath = (root: HTMLElement) => {
  for (const element of root.querySelectorAll<HTMLElement>('[data-md-math]')) {
    const mode = element.getAttribute('data-md-math')
    if ((mode !== 'display' && mode !== 'inline') || !root.contains(element)) continue
    const content = element.textContent ?? ''
    // 消费标记使处理可重复调用；保留容器上的源码范围，供滚动控制器测量最终高度。
    element.removeAttribute('data-md-math')
    try {
      const processed = content
        .replace(/@\{[^}]*\}/g, '')
        .replace(/\\\\?\s*\\hline\s*/g, '\\\\ \\hline ')
      element.innerHTML = katex.renderToString(processed, {
        displayMode: mode === 'display',
        throwOnError: false,
        strict: false,
        trust: false
      })
    } catch {
      element.classList.add('katex-error')
      element.textContent = content
    }
  }
}

/** 自定义代码/HTML 渲染器不保证输出 token 属性，因此用外层包装承载定位信息。 */
const sourceAttributes = (md: MarkdownIt, token: RenderToken) => (token.attrs ?? [])
  .filter(([name]) => name.startsWith('data-md-source-'))
  .map(([name, value]) => ` ${name}="${md.utils.escapeHtml(value)}"`)
  .join('')

/** 安装到预览解析器；全部来源状态保存在本次 render 的 env 中，不共享组件状态。 */
export const configureMarkdownSourceMapping = (md: MarkdownIt) => {
  md.core.ruler.before('normalize', 'original_source_ranges', state => {
    const env: SourceEnvironment = state.env
    const prepared = prepareSource(state.src)
    env[sourceKey] = prepared
    state.src = prepared.text
  })

  md.block.ruler.before('fence', 'native_math_block', (state, startLine, endLine, silent) => {
    if (state.sCount[startLine] - state.blkIndent >= 4) return false
    const start = state.bMarks[startLine] + state.tShift[startLine]
    if (!state.src.startsWith('$$', start) && !state.src.startsWith('\\[', start)) return false
    const raw = readMath(state.src, start)
    if (!raw?.display) return false
    const count = state.src.slice(start, raw.end).split('\n').length
    if (startLine + count > endLine) return false
    // 只提取当前公式行；引用与列表的缩进由块解析器去除，不复制整篇文档的后缀。
    const text = state.getLines(startLine, startLine + count, state.blkIndent, false)
    const leading = text.search(/\S/)
    const math = readMath(text, Math.max(0, leading))
    if (!math?.display) return false
    // 闭合标记后还有普通文字时留给行内规则，不能吞掉该段后半部分。
    const suffix = text.slice(math.end).split('\n', 1)[0]
    if (suffix.trim()) return false
    if (silent) return true
    const token = state.push('native_math_block', 'div', 0)
    token.block = true
    token.content = math.content
    token.map = [startLine, startLine + count]
    state.line = startLine + count
    return true
  }, { alt: ['paragraph', 'reference', 'blockquote', 'list'] })

  md.inline.ruler.before('escape', 'native_math_inline', (state, silent) => {
    const math = readMath(state.src.slice(0, state.posMax), state.pos)
    if (!math) return false
    if (!silent) {
      const token = state.push('native_math_inline', 'span', 0)
      token.content = math.content
      token.markup = math.display ? '$$' : '$'
    }
    state.pos = math.end
    return true
  })

  md.renderer.rules.native_math_inline = (tokens, index) => {
    const token = tokens[index]
    const display = token.markup === '$$'
    return `<span class="${display ? 'katex-display-wrapper' : 'katex-inline-wrapper'}" data-md-math="${display ? 'display' : 'inline'}">${md.utils.escapeHtml(token.content)}</span>`
  }
  md.renderer.rules.native_math_block = (tokens, index, _options, _env, self) => {
    const token = tokens[index]
    token.attrJoin('class', 'katex-display-wrapper')
    token.attrSet('data-md-math', 'display')
    return `<div${self.renderAttrs(token)}>${md.utils.escapeHtml(token.content)}</div>\n`
  }

  md.core.ruler.push('annotate_original_source', state => {
    const env: SourceEnvironment = state.env
    const source = env[sourceKey]
    if (!source) return
    state.tokens.forEach((token, index) => {
      if (!token.map || token.type === 'inline' || token.hidden || token.nesting < 0) return
      const [first, afterLast] = token.map
      const start = source.starts[first] ?? source.length
      const end = source.ends[Math.max(first, afterLast - 1)] ?? source.length
      token.attrSet('data-md-source-start', String(start))
      token.attrSet('data-md-source-end', String(end))
      token.attrSet('data-md-source-id', String(index))
      token.attrSet('data-md-source-kind', token.type)
    })
  })

  for (const name of ['fence', 'code_block', 'html_block']) {
    const original = md.renderer.rules[name]
    if (!original) continue
    md.renderer.rules[name] = (tokens, index, options, env, self) => {
      const token = tokens[index]
      // SVG 渲染器已透传全部属性；不能再增加一层重复锚点。
      if (name === 'fence' && token.info.trim() === 'svg') return original(tokens, index, options, env, self)
      const attrs = sourceAttributes(md, token)
      const savedAttrs = token.attrs
      token.attrs = savedAttrs?.filter(([key]) => !key.startsWith('data-md-source-')) ?? null
      try {
        return `<div${attrs}>${original(tokens, index, options, env, self)}</div>\n`
      } finally {
        token.attrs = savedAttrs
      }
    }
  }
}
