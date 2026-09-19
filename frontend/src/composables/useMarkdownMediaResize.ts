/**
 * Markdown 正文插图的拖拽调尺寸能力
 * 只为独立大图（.markdown-media-block）挂载把手，尺寸按图片地址保存在 localStorage，
 * DOM 重建后由 MarkdownViewer 重放；不修改 Markdown 原文、不改变作者声明的 media-wide/media-inline 语义。
 */
import { icon } from '@fortawesome/fontawesome-svg-core'
import { faArrowRotateLeft, faUpRightAndDownLeftFromCenter } from '@fortawesome/free-solid-svg-icons'

/** 尺寸存储键：值为 { [图片标识]: 宽度px } */
const STORAGE_KEY = 'markdownMediaSize'
/** 存储条目上限，超出后丢弃最早写入的记录，避免无限增长 */
const MAX_ENTRIES = 200
/** 最小宽度，同时保留容器宽度的百分比下限，避免被拖成不可见的一条 */
const MIN_WIDTH_PX = 40
const MIN_WIDTH_RATE = 0.1
/** 键盘单次步进：默认 5%，按住 Shift 为 20% */
const KEYBOARD_STEP = 0.05
const KEYBOARD_STEP_LARGE = 0.2
/** 尺寸气泡自动隐藏延时 */
const BUBBLE_HIDE_DELAY = 700

const HANDLE_ICON = icon(faUpRightAndDownLeftFromCenter).html.join('')
const RESET_ICON = icon(faArrowRotateLeft).html.join('')

type ResizableMedia = HTMLImageElement | SVGSVGElement

export interface MediaResizeController {
  /** 为一张独立插图挂载把手并重放已保存尺寸；重复调用同一节点直接返回 */
  attach: (media: ResizableMedia) => void
  /** 卸载仍在进行的拖拽监听，供组件销毁时调用 */
  dispose: () => void
}

interface MediaResizeControllerOptions {
  /** 图片所在的 Markdown 容器，用于解析当前可用宽度 */
  getRoot: () => HTMLElement | null
}

/** 从 localStorage 读取有效记录；一页多图共享同一份缓存，内容损坏时按空记录处理。 */
let storeCache: Record<string, number> | null = null

const parseStore = (): Record<string, number> => {
  const store: Record<string, number> = {}
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
        if (typeof value === 'number' && Number.isFinite(value) && value > 0) store[key] = value
      }
    }
  } catch {
    return {}
  }
  return store
}

const readStore = (): Record<string, number> => {
  if (!storeCache) storeCache = parseStore()
  return storeCache
}

const writeStore = (store: Record<string, number>) => {
  try {
    const keys = Object.keys(store)
    for (const key of keys.slice(0, Math.max(0, keys.length - MAX_ENTRIES))) delete store[key]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
  } catch {
    // 隐私模式或存储已满时只保留当前会话效果
  }
}

const saveMediaSize = (key: string, width: number) => {
  const store = readStore()
  store[key] = Math.round(width)
  writeStore(store)
}

const removeMediaSize = (key: string) => {
  const store = readStore()
  if (!(key in store)) return
  delete store[key]
  writeStore(store)
}

/** djb2 字符串散列，用于把 SVG 标记压缩成稳定的短标识。 */
const hashText = (text: string) => {
  let hash = 5381
  for (let index = 0; index < text.length; index++) {
    hash = ((hash << 5) + hash + text.charCodeAt(index)) | 0
  }
  return (hash >>> 0).toString(36)
}

/** img 用原始地址、SVG 用标记散列做键，保证内容重渲染后仍命中同一张图。 */
const resolveMediaKey = (media: ResizableMedia) => {
  if (media instanceof HTMLImageElement) return `img:${media.getAttribute('src') || media.src}`
  return `svg:${hashText(media.outerHTML)}`
}

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

/** 作者可能用百分比声明宽度；换算成像素后再放入拖拽框架，避免循环尺寸。 */
const normalizeAuthoredWidth = (media: ResizableMedia, container: HTMLElement) => {
  const raw = media.style.getPropertyValue('--media-preferred-width').trim()
  if (!raw) return ''
  if (!raw.endsWith('%')) return raw

  const percent = Number.parseFloat(raw)
  if (!Number.isFinite(percent) || percent <= 0) return ''
  return `${Math.round((container.clientWidth * percent) / 100)}px`
}

export const useMarkdownMediaResize = ({ getRoot }: MediaResizeControllerOptions): MediaResizeController => {
  /** 卸载仍在拖拽中的全局监听，旧 DOM 由 MarkdownViewer 重建时自然回收 */
  let detachActiveDrag: (() => void) | null = null

  const attach = (media: ResizableMedia) => {
    // 公式恢复与媒体准备可能对同一份 DOM 重复执行，已包装过的节点直接跳过
    if (media.closest('.markdown-media-frame')) return
    const paragraph = media.parentElement
    if (!paragraph) return

    const key = resolveMediaKey(media)
    // 记住作者声明的显示宽度（已归一化为像素），还原时回填，避免把 media-wide 之类语义一起抹掉
    const authoredWidth = normalizeAuthoredWidth(media, paragraph)
    if (authoredWidth) media.style.setProperty('--media-preferred-width', authoredWidth)

    const frame = document.createElement('span')
    frame.className = 'markdown-media-frame'
    const bubble = document.createElement('span')
    bubble.className = 'markdown-media-size-tip'
    const handle = document.createElement('button')
    handle.type = 'button'
    handle.className = 'markdown-media-handle'
    handle.innerHTML = HANDLE_ICON
    handle.setAttribute('role', 'separator')
    handle.setAttribute('aria-orientation', 'vertical')
    handle.setAttribute('aria-label', '拖拽调整图片宽度')
    handle.setAttribute('aria-valuemin', String(Math.round(MIN_WIDTH_RATE * 100)))
    handle.setAttribute('aria-valuemax', '100')
    handle.title = '拖拽调整宽度，双击还原'
    const resetButton = document.createElement('button')
    resetButton.type = 'button'
    resetButton.className = 'markdown-media-reset'
    resetButton.innerHTML = RESET_ICON
    resetButton.setAttribute('aria-label', '还原图片默认宽度')
    resetButton.title = '还原默认宽度'

    paragraph.insertBefore(frame, media)
    frame.append(media, bubble, handle, resetButton)

    /** 可用宽度取图片所在块级容器的内容宽度 */
    const resolveLimits = () => {
      const rootWidth = getRoot()?.clientWidth ?? 0
      const max = Math.max(MIN_WIDTH_PX, paragraph.clientWidth || rootWidth || MIN_WIDTH_PX)
      return { max, min: Math.min(max, Math.max(MIN_WIDTH_PX, max * MIN_WIDTH_RATE)) }
    }

    const measureWidth = () => media.getBoundingClientRect().width
    /** 宽高比（宽/高），与媒体准备阶段写入的 --media-ratio 语义一致。 */
    const measureAspect = () => {
      const cssAspect = Number.parseFloat(getComputedStyle(media).getPropertyValue('--media-ratio'))
      if (Number.isFinite(cssAspect) && cssAspect > 0) return cssAspect
      const rect = media.getBoundingClientRect()
      return rect.width > 0 && rect.height > 0 ? rect.width / rect.height : 1
    }

    const syncAriaValue = () => {
      const { max } = resolveLimits()
      const width = measureWidth()
      const percent = Math.round(clamp((width / max) * 100, MIN_WIDTH_RATE * 100, 100))
      handle.setAttribute('aria-valuenow', String(percent))
      handle.setAttribute('aria-valuetext', `宽 ${Math.round(width)} 像素，占可显示宽度 ${percent}%`)
    }

    /** 同时收敛框架宽度，保证放大后的图片能突破原生分辨率上限又不溢出容器 */
    const applyWidth = (width: number) => {
      const rounded = Math.round(width)
      media.style.setProperty('--media-preferred-width', `${rounded}px`)
      media.classList.add('media-manual')
      frame.classList.add('is-customized')
      frame.style.width = `${rounded}px`
      syncAriaValue()
    }

    const showBubble = (width: number, aspect: number) => {
      bubble.textContent = `${Math.round(width)} × ${Math.round(width / aspect)}`
      bubble.classList.add('is-visible')
    }

    let bubbleTimer: ReturnType<typeof setTimeout> | undefined
    const hideBubbleSoon = (delay = BUBBLE_HIDE_DELAY) => {
      if (bubbleTimer) clearTimeout(bubbleTimer)
      bubbleTimer = setTimeout(() => {
        bubbleTimer = undefined
        bubble.classList.remove('is-visible')
        frame.classList.remove('is-limit')
      }, delay)
    }

    const resetSize = () => {
      media.classList.remove('media-manual')
      frame.classList.remove('is-customized', 'is-resizing', 'is-limit')
      frame.style.removeProperty('width')
      if (authoredWidth) media.style.setProperty('--media-preferred-width', authoredWidth)
      else media.style.removeProperty('--media-preferred-width')
      removeMediaSize(key)
      syncAriaValue()
    }

    const persist = (width: number) => {
      saveMediaSize(key, width)
      syncAriaValue()
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (event.pointerType === 'mouse' && event.button !== 0) return
      event.preventDefault()
      event.stopPropagation()

      const startX = event.clientX
      const startWidth = measureWidth()
      const aspect = measureAspect()
      const { max, min } = resolveLimits()
      let latest = startWidth

      const handlePointerMove = (moveEvent: PointerEvent) => {
        latest = clamp(startWidth + (moveEvent.clientX - startX), min, max)
        applyWidth(latest)
        showBubble(latest, aspect)
        frame.classList.toggle('is-limit', latest <= min || latest >= max)
      }

      const stopDrag = () => {
        window.removeEventListener('pointermove', handlePointerMove)
        window.removeEventListener('pointerup', stopDrag)
        window.removeEventListener('pointercancel', stopDrag)
        if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId)
        frame.classList.remove('is-resizing')
        detachActiveDrag = null
        hideBubbleSoon()
        if (Math.round(latest) !== Math.round(startWidth)) persist(latest)
      }

      detachActiveDrag?.()
      detachActiveDrag = stopDrag
      // 拖拽期间保持键盘焦点，松手后可继续用方向键微调
      handle.focus()
      frame.classList.remove('is-limit')
      // 指针已失效时捕获会抛错，忽略即可，后续仍走全局监听
      try {
        handle.setPointerCapture(event.pointerId)
      } catch {
        // ignore
      }
      frame.classList.add('is-resizing')
      window.addEventListener('pointermove', handlePointerMove)
      window.addEventListener('pointerup', stopDrag)
      window.addEventListener('pointercancel', stopDrag)
      showBubble(startWidth, aspect)
    }

    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        event.stopPropagation()
        resetSize()
        return
      }

      const direction = event.key === 'ArrowRight' || event.key === 'ArrowUp'
        ? 1
        : event.key === 'ArrowLeft' || event.key === 'ArrowDown'
          ? -1
          : 0
      if (direction === 0) return

      event.preventDefault()
      event.stopPropagation()
      const { max, min } = resolveLimits()
      const aspect = measureAspect()
      const step = (event.shiftKey ? KEYBOARD_STEP_LARGE : KEYBOARD_STEP) * max
      const next = clamp(measureWidth() + direction * step, min, max)
      applyWidth(next)
      frame.classList.toggle('is-limit', next <= min || next >= max)
      showBubble(next, aspect)
      hideBubbleSoon()
      persist(next)
    }

    // 把手与还原按钮的点击不参与图片的其他交互（全屏查看、选项作答等）
    const stopClick = (event: Event) => event.stopPropagation()
    const handleDoubleClick = (event: Event) => {
      event.stopPropagation()
      resetSize()
    }

    handle.addEventListener('pointerdown', handlePointerDown)
    handle.addEventListener('click', stopClick)
    handle.addEventListener('dblclick', handleDoubleClick)
    handle.addEventListener('keydown', handleKeydown)
    resetButton.addEventListener('pointerdown', stopClick)
    resetButton.addEventListener('click', (event) => {
      event.stopPropagation()
      resetSize()
    })

    // 重放已保存尺寸：必须在媒体准备阶段同步完成，否则会出现先紧凑后跳大的闪动
    const storedWidth = readStore()[key]
    if (storedWidth) {
      const { max } = resolveLimits()
      applyWidth(Math.min(storedWidth, max))
    } else {
      syncAriaValue()
    }
  }

  return {
    attach,
    dispose: () => {
      detachActiveDrag?.()
      detachActiveDrag = null
    }
  }
}
