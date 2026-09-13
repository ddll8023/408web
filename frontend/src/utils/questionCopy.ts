/** 图片复制命令支持的内容范围；题干和选项始终作为一个整体。 */
export type QuestionImageCopyScope = 'question-options' | 'answer' | 'all'

/** 富文本复制支持分别复制题干、选项、答案或完整内容。 */
export type QuestionRichCopyScope = 'question' | 'options' | 'answer' | 'all'

/** 隐藏渲染器可展示的内容范围。 */
export type QuestionContentScope = QuestionImageCopyScope | QuestionRichCopyScope

export interface RichCopyContent {
  html: string
  text: string
}

export type ImageCopyResult = 'clipboard' | 'download'
export type RichCopyResult = 'rich' | 'plain'

const imageCopyScopes: readonly QuestionImageCopyScope[] = [
  'question-options',
  'answer',
  'all'
]

const richCopyScopes: readonly QuestionRichCopyScope[] = [
  'question',
  'options',
  'answer',
  'all'
]

/** 将复制命令转换为图片渲染范围；非图片命令返回 null。 */
export const getImageCopyScope = (command: string): QuestionImageCopyScope | null => {
  if (!command.startsWith('image-')) return null

  const scope = command.slice('image-'.length) as QuestionImageCopyScope
  return imageCopyScopes.includes(scope) ? scope : null
}

/** 将复制命令转换为 Word 富文本渲染范围；非 Word 命令返回 null。 */
export const getRichCopyScope = (command: string): QuestionRichCopyScope | null => {
  if (!command.startsWith('word-')) return null

  const scope = command.slice('word-'.length) as QuestionRichCopyScope
  return richCopyScopes.includes(scope) ? scope : null
}

const supportsImageClipboard = () => {
  return typeof window !== 'undefined' &&
    window.isSecureContext &&
    typeof navigator !== 'undefined' &&
    typeof navigator.clipboard?.write === 'function' &&
    typeof ClipboardItem !== 'undefined'
}

const supportsRichClipboard = () => {
  return typeof window !== 'undefined' &&
    window.isSecureContext &&
    typeof navigator !== 'undefined' &&
    typeof navigator.clipboard?.write === 'function' &&
    typeof ClipboardItem !== 'undefined'
}

const copyPlainText = async (text: string) => {
  if (typeof window !== 'undefined' && typeof navigator !== 'undefined' &&
    typeof navigator.clipboard?.writeText === 'function' && window.isSecureContext) {
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
    if (typeof document.execCommand !== 'function' || !document.execCommand('copy')) {
      throw new Error('TEXT_COPY_UNSUPPORTED')
    }
  } finally {
    document.body.removeChild(textArea)
  }
}

/** 使用旧版选区复制 API 兼容不支持 ClipboardItem 的浏览器。 */
const copyHtmlBySelection = (html: string) => {
  if (typeof document.execCommand !== 'function') return false

  const container = document.createElement('div')
  container.innerHTML = html
  container.style.position = 'fixed'
  container.style.left = '-999999px'
  container.style.top = '0'
  container.style.width = '1px'
  container.style.height = '1px'
  container.style.overflow = 'hidden'
  document.body.appendChild(container)

  const selection = window.getSelection()
  if (!selection) {
    document.body.removeChild(container)
    return false
  }

  const previousRanges = Array.from({ length: selection.rangeCount }, (_, index) =>
    selection.getRangeAt(index).cloneRange(),
  )

  try {
    const range = document.createRange()
    range.selectNodeContents(container)
    selection.removeAllRanges()
    selection.addRange(range)
    return document.execCommand('copy')
  } finally {
    selection.removeAllRanges()
    previousRanges.forEach(range => selection.addRange(range))
    document.body.removeChild(container)
  }
}

/**
 * 同时写入 HTML 与纯文本，让 Word/WPS 优先使用排版内容。
 * 接受 Promise 是为了像图片复制一样尽早调用 clipboard.write，保留用户手势上下文。
 */
export const copyRichContent = async (
  content: RichCopyContent | Promise<RichCopyContent>,
): Promise<RichCopyResult> => {
  const contentPromise = Promise.resolve(content)

  if (supportsRichClipboard()) {
    try {
      const item = new ClipboardItem({
        'text/html': contentPromise.then(({ html }) => {
          if (!html.trim()) throw new Error('NO_COPY_CONTENT')
          return new Blob([html], { type: 'text/html' })
        }),
        'text/plain': contentPromise.then(({ text }) => {
          if (!text.trim()) throw new Error('NO_COPY_CONTENT')
          return new Blob([text], { type: 'text/plain' })
        }),
      })
      await navigator.clipboard.write([item])
      return 'rich'
    } catch {
      // 权限或目标应用不支持时，继续尝试旧版选区复制。
    }
  }

  const { html, text } = await contentPromise
  if (!html.trim() && !text.trim()) throw new Error('NO_COPY_CONTENT')

  try {
    if (copyHtmlBySelection(html)) return 'rich'
  } catch {
    // 继续回退为纯文本，确保复制动作仍然可用。
  }

  await copyPlainText(text)
  return 'plain'
}

const downloadPng = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'

  let appended = false
  try {
    document.body.appendChild(link)
    appended = true
    link.click()
  } finally {
    if (appended) document.body.removeChild(link)
    // 延迟释放对象 URL，确保浏览器已经接收下载请求。
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  }
}

/**
 * 优先写入图片剪贴板；浏览器能力或权限不满足时下载 PNG 作为兜底。
 * 使用 Blob Promise 尽早调用 clipboard.write，尽量保留用户手势上下文。
 * 不回退为纯文本，避免用户选择图片复制后得到错误格式。
 */
export const copyImageBlob = async (
  blob: Blob | Promise<Blob>,
  filename: string,
): Promise<ImageCopyResult> => {
  const blobPromise = Promise.resolve(blob)

  if (supportsImageClipboard()) {
    try {
      const item = new ClipboardItem({ 'image/png': blobPromise })
      await navigator.clipboard.write([item])
      return 'clipboard'
    } catch {
      // 剪贴板权限、浏览器实现或目标应用不支持时继续走下载兜底。
    }
  }

  downloadPng(await blobPromise, filename)
  return 'download'
}
