/** Markdown 双栏滚动控制：配对源码范围与预览块，隔离用户操作、渲染版本和布局更新。 */
import { onMounted, onUnmounted, watch } from 'vue'
import type { MarkdownRenderSnapshot } from '@/utils/markdownSourceMapping'

interface ScrollSyncOptions {
  getEditor: () => HTMLElement | null
  getPreview: () => HTMLElement | null
  getContent: () => string
  isEnabled: () => boolean
  isSplit: () => boolean
}

type Side = 'edit' | 'preview'
interface Knot {
  offset: number
  edit: number
  preview: number
}
interface BlockRange {
  start: number
  end: number
  editTop: number
  editBottom: number
  previewTop: number
  previewBottom: number
}

const SOURCE_SELECTOR = '[data-md-source-start][data-md-source-end][data-md-source-id]'
const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

/** 单调坐标表内插值；两侧共享同一张表，避免各自猜测源码行号后再二次换算。 */
const interpolate = (knots: Knot[], value: number, from: keyof Knot, to: keyof Knot) => {
  if (!knots.length) return 0
  if (value <= knots[0][from]) return knots[0][to]
  let low = 0
  let high = knots.length - 1
  while (low + 1 < high) {
    const mid = Math.floor((low + high) / 2)
    if (knots[mid][from] <= value) low = mid
    else high = mid
  }
  const previous = knots[low]
  const next = knots[high]
  const span = next[from] - previous[from]
  const progress = span > 0 ? clamp((value - previous[from]) / span, 0, 1) : 0
  return previous[to] + progress * (next[to] - previous[to])
}

/** 内容修改时保留改动前后未变文本的阅读位置；替换区内的位置收敛到替换区内。 */
const rebaseOffset = (offset: number, before: string, after: string) => {
  let prefix = 0
  const common = Math.min(before.length, after.length)
  while (prefix < common && before[prefix] === after[prefix]) prefix += 1
  let suffix = 0
  while (suffix < common - prefix && before[before.length - suffix - 1] === after[after.length - suffix - 1]) suffix += 1
  if (offset <= prefix) return offset
  if (offset >= before.length - suffix) return offset + after.length - before.length
  return Math.min(offset, after.length - suffix)
}

export const useMarkdownScrollSync = (options: ScrollSyncOptions) => {
  let editPane: HTMLElement | null = null
  let previewPane: HTMLElement | null = null
  let ready: MarkdownRenderSnapshot | null = null
  let currentSource = options.getContent()
  let knots: Knot[] = []
  let leader: Side = 'edit'
  let bookmark: number | null = null
  let dirty = true
  let mounted = false
  let disposed = false
  let frame = 0
  let pendingSide: Side | null = null
  let reflowPending = false
  let pointerOwner: Side | null = null
  let inputOwner: Side | null = null
  let inputUntil = 0
  let observer: ResizeObserver | null = null
  const observed = new Set<Element>()
  const expected: Partial<Record<Side, number>> = {}

  const paneFor = (side: Side) => side === 'edit' ? editPane : previewPane
  const active = () => mounted && options.isEnabled() && options.isSplit() && ready?.source === options.getContent()

  /** 缓存源码字符偏移，布局变动后不再沿用旧的像素位置。 */
  const rememberPosition = (side: Side) => {
    const pane = paneFor(side)
    if (pane && knots.length) bookmark = interpolate(knots, pane.scrollTop, side, 'offset')
  }

  /** 设置滚动位置并记住浏览器实际采纳的值；只抑制这一次目标回调，不锁住另一侧输入。 */
  const writePosition = (side: Side, top: number) => {
    const pane = paneFor(side)
    if (!pane) return
    const next = clamp(top, 0, Math.max(0, pane.scrollHeight - pane.clientHeight))
    if (Math.abs(next - pane.scrollTop) < 0.5) return
    expected[side] = next
    pane.scrollTop = next
    expected[side] = pane.scrollTop
  }

  /** 观察集合只做增删，不能每次测量都重新 observe，否则初始通知会形成持续重排。 */
  const updateObserved = (elements: Element[]) => {
    const next = new Set(elements)
    for (const element of observed) {
      if (!next.has(element)) {
        observer?.unobserve(element)
        observed.delete(element)
      }
    }
    for (const element of next) {
      if (!observed.has(element)) {
        observer?.observe(element)
        observed.add(element)
      }
    }
  }

  /** 重建同版本的配对坐标；嵌套容器只保留子块之前的独立内容，不把父子高度重叠计算。 */
  const measure = () => {
    if (!editPane || !previewPane || !ready || ready.source !== options.getContent()) return
    const source = ready.source
    const lineStarts = [0]
    for (let index = 0; index < source.length; index += 1) {
      if (source[index] === '\n') lineStarts.push(index + 1)
    }
    const editRect = editPane.getBoundingClientRect()
    const editScrollTop = editPane.scrollTop
    const previewRect = previewPane.getBoundingClientRect()
    if (!editPane.clientHeight || !previewPane.clientHeight) return
    // 弹窗进入动画可能缩放祖先；DOMRect 是变换后的像素，scrollTop 则仍是布局坐标。
    const editScale = editPane.offsetHeight ? editRect.height / editPane.offsetHeight : 1
    const previewScale = previewPane.offsetHeight ? previewRect.height / previewPane.offsetHeight : 1
    if (editScale <= 0 || previewScale <= 0) return
    const sourceLines = new Map<number, HTMLElement>()
    editPane.querySelectorAll<HTMLElement>('pre section[data-line]').forEach(element => {
      sourceLines.set(Number(element.dataset.line), element)
    })

    /** 按镜像行和字符的真实矩形定位，包含自动换行，不使用固定字号推算。 */
    const sourceY = (offset: number, end: boolean) => {
      const position = clamp(offset, 0, source.length)
      // end 是开区间边界：落在下一行起点时应取上一行底边，而不是下一行首字底边。
      const probe = end && position > 0 ? position - 1 : position
      let low = 0
      let high = lineStarts.length - 1
      while (low < high) {
        const mid = Math.ceil((low + high) / 2)
        if (lineStarts[mid] <= probe) low = mid
        else high = mid - 1
      }
      const row = sourceLines.get(low + 1)
      if (!row) return null
      const rect = row.getBoundingClientRect()
      const text = row.firstChild
      if (text?.nodeType === Node.TEXT_NODE && text.textContent?.length) {
        const length = text.textContent.length
        const column = clamp(position - lineStarts[low], 0, length)
        const index = clamp(end ? column - 1 : column, 0, length - 1)
        const range = document.createRange()
        range.setStart(text, index)
        range.setEnd(text, index + 1)
        const charRect = range.getBoundingClientRect()
        if (charRect.height > 0) return ((end ? charRect.bottom : charRect.top) - editRect.top) / editScale + editScrollTop
      }
      return ((end ? rect.bottom : rect.top) - editRect.top) / editScale + editScrollTop
    }

    const seen = new Set<string>()
    const candidates = Array.from(previewPane.querySelectorAll<HTMLElement>(SOURCE_SELECTOR)).filter(element => {
      const id = element.getAttribute('data-md-source-id') || ''
      const start = Number(element.getAttribute('data-md-source-start'))
      const end = Number(element.getAttribute('data-md-source-end'))
      const rect = element.getBoundingClientRect()
      if (seen.has(id) || !Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start || end > source.length || !rect.height || !rect.width) return false
      seen.add(id)
      return true
    })
    const candidateSet = new Set(candidates)
    const blocks: BlockRange[] = []
    for (const element of candidates) {
      const start = Number(element.getAttribute('data-md-source-start'))
      let end = Number(element.getAttribute('data-md-source-end'))
      const rect = element.getBoundingClientRect()
      let bottom = rect.bottom
      const child = Array.from(element.querySelectorAll<HTMLElement>(SOURCE_SELECTOR)).find(node => candidateSet.has(node))
      if (child) {
        const childStart = Number(child.getAttribute('data-md-source-start'))
        if (childStart <= start) continue
        end = Math.min(end, childStart)
        bottom = Math.min(bottom, child.getBoundingClientRect().top)
      }
      const editTop = sourceY(start, false)
      const editBottom = sourceY(end, true)
      const previewTop = (rect.top - previewRect.top) / previewScale + previewPane.scrollTop
      const previewBottom = (bottom - previewRect.top) / previewScale + previewPane.scrollTop
      if (editTop === null || editBottom === null || editBottom <= editTop || previewBottom <= previewTop) continue
      blocks.push({ start, end, editTop, editBottom, previewTop, previewBottom })
    }
    blocks.sort((a, b) => a.start - b.start || a.end - b.end)

    // 多个预览块可能来自源码同一物理行（旧字面换行）；这时只能合并，不能伪造可逆的垂直位置。
    const merged: BlockRange[] = []
    for (const block of blocks) {
      const previous = merged[merged.length - 1]
      if (previous && (block.start < previous.end || block.editTop < previous.editBottom - 0.5 || block.previewTop < previous.previewBottom - 0.5)) {
        previous.end = Math.max(previous.end, block.end)
        previous.editBottom = Math.max(previous.editBottom, block.editBottom)
        previous.previewBottom = Math.max(previous.previewBottom, block.previewBottom)
      } else merged.push({ ...block })
    }
    const pre = editPane.querySelector('pre')
    const viewer = previewPane.querySelector('.markdown-viewer')
    updateObserved([editPane, previewPane, ...(pre ? [pre] : []), ...(viewer ? [viewer] : []), ...candidates])
    dirty = false
    // 无有效范围时暂停同步，不能悄悄退回全文百分比并制造看似正常的错误对齐。
    if (!merged.length) {
      knots = []
      return
    }
    const next: Knot[] = [{ offset: -1, edit: 0, preview: 0 }]
    for (const block of merged) {
      const last = next[next.length - 1]
      if (block.start < last.offset || block.editTop < last.edit || block.previewTop < last.preview) continue
      if (block.start > last.offset) next.push({ offset: block.start, edit: block.editTop, preview: block.previewTop })
      next.push({ offset: block.end, edit: block.editBottom, preview: block.previewBottom })
    }
    if (next.length === 1) {
      knots = []
      return
    }
    // 文末只表示内容边界；不把一侧的最大 scrollTop 硬映射到另一侧最大值。
    const last = next[next.length - 1]
    next.push({ offset: source.length + 1, edit: Math.max(last.edit, editPane.scrollHeight), preview: Math.max(last.preview, previewPane.scrollHeight) })
    knots = next
  }

  /** 跟随当前主动侧的内容位置；目标已到边界时只裁剪，不反向拖动主动侧。 */
  const follow = (side: Side) => {
    const pane = paneFor(side)
    if (!pane || knots.length < 2) return
    const target: Side = side === 'edit' ? 'preview' : 'edit'
    const top = pane.scrollTop <= 0 ? 0 : interpolate(knots, pane.scrollTop, side, target)
    writePosition(target, top)
    rememberPosition(side)
  }

  /** 同一帧只采用最后一次用户输入；版本未就绪时不消费旧表。 */
  const schedule = () => {
    if (disposed || frame || !mounted) return
    frame = requestAnimationFrame(() => {
      frame = 0
      if (!active()) return
      const side = pendingSide
      pendingSide = null
      const restore = reflowPending && !side && bookmark !== null
      reflowPending = false
      if (dirty) measure()
      if (!knots.length || dirty) return
      if (restore && bookmark !== null) {
        writePosition(leader, interpolate(knots, bookmark, 'offset', leader))
      }
      follow(side ?? leader)
    })
  }

  /** 布局变化使用旧表保留的阅读位置；新表要在下一帧统一测量。 */
  const invalidateLayout = () => {
    dirty = true
    reflowPending = true
    schedule()
  }

  const claim = (side: Side, event: Event) => {
    if (event instanceof KeyboardEvent && !['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(event.key)) return
    leader = side
    inputOwner = side
    inputUntil = performance.now() + 250
    if (event.type === 'pointerdown' || event.type === 'touchstart') pointerOwner = side
    delete expected[side]
  }

  const releasePointer = () => {
    pointerOwner = null
    inputUntil = performance.now() + 250
  }

  const handleScroll = (side: Side) => {
    const pane = paneFor(side)
    if (!pane) return
    const expectedTop = expected[side]
    if (expectedTop !== undefined) {
      delete expected[side]
      if (Math.abs(pane.scrollTop - expectedTop) < 1) return
    }
    if (!active()) return
    const userInput = pointerOwner === side || (inputOwner === side && performance.now() < inputUntil)
    // 内容重排也会触发 scroll；没有输入证据时必须保留重排前的源码书签。
    if (dirty && !userInput) return
    // 没有主动输入的另一侧事件通常来自浏览器布局锚定，不能反过来抢走控制权。
    if (side !== leader && !userInput && !pane.contains(document.activeElement)) return
    leader = side
    if (!dirty) rememberPosition(side)
    pendingSide = side
    schedule()
  }

  const onEditScroll = () => handleScroll('edit')
  const onPreviewScroll = () => handleScroll('preview')
  const onEditInput = (event: Event) => claim('edit', event)
  const onPreviewInput = (event: Event) => claim('preview', event)
  const inputs = ['wheel', 'pointerdown', 'touchstart', 'keydown'] as const

  const unbind = () => {
    editPane?.removeEventListener('scroll', onEditScroll)
    previewPane?.removeEventListener('scroll', onPreviewScroll)
    for (const name of inputs) {
      editPane?.removeEventListener(name, onEditInput, true)
      previewPane?.removeEventListener(name, onPreviewInput, true)
    }
    previewPane?.removeEventListener('load', invalidateLayout, true)
    previewPane?.removeEventListener('error', invalidateLayout, true)
    observer?.disconnect()
    observed.clear()
    editPane = null
    previewPane = null
    delete expected.edit
    delete expected.preview
    pointerOwner = null
    inputOwner = null
  }

  /** 库或 Teleport 重建节点后重新绑定；普通阅读不调用该控制器。 */
  const refresh = () => {
    if (!mounted || disposed) return
    const edit = options.getEditor()
    const preview = options.getPreview()
    if (edit !== editPane || preview !== previewPane) {
      unbind()
      editPane = edit
      previewPane = preview
      editPane?.addEventListener('scroll', onEditScroll, { passive: true })
      previewPane?.addEventListener('scroll', onPreviewScroll, { passive: true })
      for (const name of inputs) {
        editPane?.addEventListener(name, onEditInput, { capture: true, passive: name !== 'keydown' })
        previewPane?.addEventListener(name, onPreviewInput, { capture: true, passive: name !== 'keydown' })
      }
      previewPane?.addEventListener('load', invalidateLayout, true)
      previewPane?.addEventListener('error', invalidateLayout, true)
    }
    invalidateLayout()
  }

  /** 文本一变立即停用旧表；连续编辑期间逐次重定位书签，而不是等旧预览的延时回调。 */
  const invalidateContent = () => {
    const source = options.getContent()
    if (source !== currentSource && bookmark !== null) bookmark = rebaseOffset(bookmark, currentSource, source)
    currentSource = source
    ready = null
    pendingSide = null
    dirty = true
    reflowPending = true
    delete expected.edit
    delete expected.preview
  }

  /** 只接受当前源码已经完成 DOM 更新的通知。 */
  const acceptRender = (snapshot: MarkdownRenderSnapshot) => {
    if (snapshot.source !== options.getContent()) return
    ready = snapshot
    // 输入时的光标自动滚动应以编辑器现位置为准，不能被旧书签拉回去。
    if (editPane?.contains(document.activeElement)) {
      leader = 'edit'
      pendingSide = 'edit'
    }
    refresh()
  }

  const alignFromEdit = () => {
    leader = 'edit'
    pendingSide = 'edit'
    dirty = true
    schedule()
  }

  watch(options.getContent, invalidateContent, { flush: 'sync' })
  watch([options.isEnabled, options.isSplit], () => {
    if (options.isEnabled() && options.isSplit()) {
      refresh()
      alignFromEdit()
    }
  }, { flush: 'post' })

  onMounted(() => {
    mounted = true
    observer = new ResizeObserver(invalidateLayout)
    document.fonts?.addEventListener('loadingdone', invalidateLayout)
    document.addEventListener('pointerup', releasePointer, true)
    document.addEventListener('pointercancel', releasePointer, true)
    document.addEventListener('touchend', releasePointer, true)
    document.addEventListener('touchcancel', releasePointer, true)
    refresh()
  })
  onUnmounted(() => {
    disposed = true
    mounted = false
    cancelAnimationFrame(frame)
    document.fonts?.removeEventListener('loadingdone', invalidateLayout)
    document.removeEventListener('pointerup', releasePointer, true)
    document.removeEventListener('pointercancel', releasePointer, true)
    document.removeEventListener('touchend', releasePointer, true)
    document.removeEventListener('touchcancel', releasePointer, true)
    unbind()
    knots = []
    ready = null
  })

  return { refresh, invalidateLayout, acceptRender }
}
