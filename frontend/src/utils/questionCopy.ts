/** 图片复制命令支持的内容范围；题干和选项始终作为一个整体。 */
export type QuestionImageCopyScope = 'question-options' | 'answer' | 'all'

export type ImageCopyResult = 'clipboard' | 'download'

const imageCopyScopes: readonly QuestionImageCopyScope[] = [
  'question-options',
  'answer',
  'all'
]

/** 将复制命令转换为图片渲染范围；非图片命令返回 null。 */
export const getImageCopyScope = (command: string): QuestionImageCopyScope | null => {
  if (!command.startsWith('image-')) return null

  const scope = command.slice('image-'.length) as QuestionImageCopyScope
  return imageCopyScopes.includes(scope) ? scope : null
}

const supportsImageClipboard = () => {
  return typeof window !== 'undefined' &&
    window.isSecureContext &&
    typeof navigator !== 'undefined' &&
    typeof navigator.clipboard?.write === 'function' &&
    typeof ClipboardItem !== 'undefined'
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
