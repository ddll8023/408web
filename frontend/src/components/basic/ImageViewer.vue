<!--
  ImageViewer 全屏图片查看器
  功能描述：把图片直接铺满屏幕展示，不套弹窗外框；支持滚轮/按钮缩放、双击切换、拖拽平移、适应窗口和一键关闭。
  依赖组件：FontAwesomeIcon（全局注册）
-->
<template>
  <teleport to="body">
    <transition name="image-viewer-fade">
      <div
        v-if="visible"
        ref="rootRef"
        class="image-viewer fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden bg-black/85 outline-none select-none"
        :class="dragging ? 'cursor-grabbing' : 'cursor-grab'"
        role="dialog"
        aria-modal="true"
        :aria-label="`图片查看：${alt || '插图'}`"
        tabindex="-1"
        @keydown="handleKeydown"
        @wheel.prevent="handleWheel"
        @pointerdown="handlePointerDown"
        @pointermove="handlePointerMove"
        @pointerup="handlePointerUp"
        @pointercancel="handlePointerUp"
        @dblclick="handleDoubleClick"
      >
        <img
          ref="imageRef"
          class="image-viewer__image"
          :src="src"
          :alt="alt"
          :style="imageStyle"
          draggable="false"
          @load="applyFitToViewport"
        />

        <!-- 工具栏：阻止事件冒泡，避免拖动图片或触发遮罩关闭 -->
        <div
          class="image-viewer__toolbar absolute bottom-6 left-1/2 flex -translate-x-1/2 cursor-default items-center gap-1 rounded-full bg-black/60 px-2 py-1 text-white shadow-lg backdrop-blur"
          @pointerdown.stop
          @dblclick.stop
          @wheel.prevent.stop
        >
          <button
            type="button"
            class="image-viewer__button"
            aria-label="缩小"
            title="缩小"
            @click="zoomByStep(1 / ZOOM_STEP)"
          >
            <font-awesome-icon :icon="['fas', 'magnifying-glass-minus']" aria-hidden="true" />
          </button>
          <button
            type="button"
            class="image-viewer__scale"
            aria-label="重置为 100%"
            title="重置为 100%"
            @click="resetTransform(1)"
          >
            {{ zoomPercent }}
          </button>
          <button
            type="button"
            class="image-viewer__button"
            aria-label="放大"
            title="放大"
            @click="zoomByStep(ZOOM_STEP)"
          >
            <font-awesome-icon :icon="['fas', 'magnifying-glass-plus']" aria-hidden="true" />
          </button>
          <span class="image-viewer__divider" aria-hidden="true"></span>
          <button
            type="button"
            class="image-viewer__button"
            aria-label="适应窗口"
            title="适应窗口"
            @click="applyFitToViewport"
          >
            <font-awesome-icon :icon="['fas', 'expand']" aria-hidden="true" />
          </button>
        </div>

        <button
          type="button"
          class="image-viewer__button absolute top-5 right-5 bg-black/60 text-white shadow-lg"
          aria-label="关闭图片查看"
          title="关闭（Esc）"
          @pointerdown.stop
          @dblclick.stop
          @click="close"
        >
          <font-awesome-icon :icon="['fas', 'times']" aria-hidden="true" />
        </button>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
/**
 * 全屏图片查看器
 * 缩放与平移只修改图片自身的 transform，不改变页面布局；滚轮缩放以指针位置为锚点。
 */
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

/** 缩放上下限，避免图片被缩到不可见或放大到失控。 */
const MIN_SCALE = 0.05
const MAX_SCALE = 10
/** 按钮与键盘单次缩放倍率。 */
const ZOOM_STEP = 1.25
/** 滚轮灵敏度：按 deltaY 指数缩放，保证不同设备的缩放手感接近。 */
const WHEEL_SENSITIVITY = 0.0015
/** 适应窗口时四周保留的间距，单位像素。 */
const FIT_PADDING = 24
/** 超过该位移才判定为拖拽，用于区分点击遮罩关闭。 */
const DRAG_THRESHOLD = 3

const props = defineProps({
  /** 是否显示查看器 */
  visible: {
    type: Boolean,
    default: false
  },
  /** 图片地址，支持 http(s) 与 Blob URL */
  src: {
    type: String,
    default: ''
  },
  /** 图片替代文本，用于可访问名称 */
  alt: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{ close: [] }>()

const rootRef = ref<HTMLElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const dragging = ref(false)
/** 适应窗口时的缩放比例，作为双击与重置的基准。 */
const fitScale = ref(1)

const imageStyle = computed(() => ({
  transform: `translate3d(${translateX.value}px, ${translateY.value}px, 0) scale(${scale.value})`,
  // 拖拽过程去掉过渡，避免跟手滞后
  transition: dragging.value ? 'none' : 'transform 0.15s ease-out'
}))

const zoomPercent = computed(() => `${Math.round(scale.value * 100)}%`)

const clampScale = (value: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value))

/** 计算图片完整放入视口所需的缩放比例，小图不放大。 */
const computeFitScale = () => {
  const root = rootRef.value
  const image = imageRef.value
  if (!root || !image || !image.naturalWidth || !image.naturalHeight) return 1

  const availableWidth = Math.max(1, root.clientWidth - FIT_PADDING * 2)
  const availableHeight = Math.max(1, root.clientHeight - FIT_PADDING * 2)
  return clampScale(Math.min(1, availableWidth / image.naturalWidth, availableHeight / image.naturalHeight))
}

/** 以指定锚点缩放：锚点取视口中心为原点，保证光标下的像素位置不动。 */
const zoomTo = (nextScale: number, anchorX = 0, anchorY = 0) => {
  const target = clampScale(nextScale)
  if (target === scale.value) return

  const ratio = target / scale.value
  translateX.value = anchorX - ratio * (anchorX - translateX.value)
  translateY.value = anchorY - ratio * (anchorY - translateY.value)
  scale.value = target
}

/** 重置缩放比例并回到居中位置。 */
const resetTransform = (nextScale: number) => {
  scale.value = clampScale(nextScale)
  translateX.value = 0
  translateY.value = 0
}

/** 图片加载完成后按视口计算适应比例；源尺寸信息缺失时保持 100%。 */
const applyFitToViewport = () => {
  fitScale.value = computeFitScale()
  resetTransform(fitScale.value)
}

const zoomByStep = (factor: number) => {
  zoomTo(scale.value * factor)
}

/** 指针相对视口中心的偏移，作为缩放锚点。 */
const resolveAnchor = (clientX: number, clientY: number) => {
  const rect = rootRef.value?.getBoundingClientRect()
  if (!rect) return { anchorX: 0, anchorY: 0 }
  return {
    anchorX: clientX - (rect.left + rect.width / 2),
    anchorY: clientY - (rect.top + rect.height / 2)
  }
}

const handleWheel = (event: WheelEvent) => {
  const delta = event.deltaMode === 1 ? event.deltaY * 16 : event.deltaY
  const { anchorX, anchorY } = resolveAnchor(event.clientX, event.clientY)
  zoomTo(scale.value * Math.exp(-delta * WHEEL_SENSITIVITY), anchorX, anchorY)
}

/** 双击在适应窗口与 100% 之间切换，放大状态下先回到适应窗口。 */
const handleDoubleClick = (event: MouseEvent) => {
  if (scale.value >= 1) {
    applyFitToViewport()
    return
  }
  const { anchorX, anchorY } = resolveAnchor(event.clientX, event.clientY)
  zoomTo(1, anchorX, anchorY)
}

let activePointerId = -1
let startPointerX = 0
let startPointerY = 0
let startTranslateX = 0
let startTranslateY = 0
let pressedOnBackdrop = false
let pointerMoved = false

const handlePointerDown = (event: PointerEvent) => {
  if (event.pointerType === 'mouse' && event.button !== 0) return

  pressedOnBackdrop = event.target === rootRef.value
  pointerMoved = false
  activePointerId = event.pointerId
  startPointerX = event.clientX
  startPointerY = event.clientY
  startTranslateX = translateX.value
  startTranslateY = translateY.value
  dragging.value = true
  rootRef.value?.setPointerCapture(event.pointerId)
}

const handlePointerMove = (event: PointerEvent) => {
  if (!dragging.value || event.pointerId !== activePointerId) return

  const deltaX = event.clientX - startPointerX
  const deltaY = event.clientY - startPointerY
  if (!pointerMoved && Math.hypot(deltaX, deltaY) > DRAG_THRESHOLD) pointerMoved = true
  if (!pointerMoved) return

  translateX.value = startTranslateX + deltaX
  translateY.value = startTranslateY + deltaY
}

const handlePointerUp = (event: PointerEvent) => {
  if (!dragging.value || event.pointerId !== activePointerId) return

  dragging.value = false
  activePointerId = -1
  if (rootRef.value?.hasPointerCapture(event.pointerId)) rootRef.value.releasePointerCapture(event.pointerId)
  if (!pointerMoved && pressedOnBackdrop) close()
  pressedOnBackdrop = false
}

/** 键盘快捷键：Esc 关闭，+/- 缩放，0 适应窗口，1 回到 100%，Tab 只在查看器内循环。 */
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Tab') {
    trapFocus(event)
    return
  }

  const shortcuts: Record<string, () => void> = {
    Escape: close,
    '+': () => zoomByStep(ZOOM_STEP),
    '=': () => zoomByStep(ZOOM_STEP),
    '-': () => zoomByStep(1 / ZOOM_STEP),
    '0': applyFitToViewport,
    '1': () => resetTransform(1)
  }
  const action = shortcuts[event.key]
  if (!action) return

  event.preventDefault()
  action()
}

const trapFocus = (event: KeyboardEvent) => {
  const buttons = Array.from(rootRef.value?.querySelectorAll<HTMLElement>('button') ?? [])
  if (buttons.length === 0) return

  const first = buttons[0]
  const last = buttons[buttons.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

const close = () => {
  emit('close')
}

let previouslyFocused: HTMLElement | null = null
let previousBodyOverflow = ''

/** 打开时锁定页面滚动并把焦点移入查看器，关闭后恢复焦点与滚动。 */
const syncVisibility = async (visible: boolean) => {
  if (typeof document === 'undefined') return

  if (visible) {
    previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    // 重新打开时先回到 100%，避免沿用上一次的缩放与位移
    fitScale.value = 1
    resetTransform(1)
    await nextTick()
    rootRef.value?.focus()
    // 缓存命中时 load 可能早于挂载回调，这里补算一次适应比例
    if (imageRef.value?.complete) applyFitToViewport()
    return
  }

  document.body.style.overflow = previousBodyOverflow
  previousBodyOverflow = ''
  dragging.value = false
  activePointerId = -1
  if (previouslyFocused?.isConnected) previouslyFocused.focus()
  previouslyFocused = null
}

watch(
  () => props.visible,
  (visible) => {
    void syncVisibility(visible)
  },
  { immediate: true }
)

// 同一查看器内切换图片时清除上一张的缩放与位移
watch(() => props.src, () => {
  if (!props.visible) return
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
})

onBeforeUnmount(() => {
  if (typeof document !== 'undefined' && document.body?.style) {
    document.body.style.overflow = previousBodyOverflow
  }
})
</script>

<style scoped>
.image-viewer {
  /* 触屏环境禁用浏览器默认滚动与缩放，交给组件自己处理 */
  touch-action: none;
}

.image-viewer__image {
  display: block;
  max-width: none;
  max-height: none;
  /* 以原始像素尺寸渲染，transform 缩放才是真实倍率 */
  width: auto;
  height: auto;
  transform-origin: center center;
  will-change: transform;
  user-select: none;
  -webkit-user-drag: none;
}

.image-viewer__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 9999px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.image-viewer__button:hover {
  background-color: rgb(255 255 255 / 0.18);
}

.image-viewer__button:focus-visible,
.image-viewer__scale:focus-visible {
  outline: 2px solid #fff;
  outline-offset: 2px;
}

.image-viewer__scale {
  min-width: 3.5rem;
  padding: 0 0.5rem;
  height: 2.25rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.image-viewer__scale:hover {
  background-color: rgb(255 255 255 / 0.18);
}

.image-viewer__divider {
  width: 1px;
  height: 1.25rem;
  margin: 0 0.25rem;
  background-color: rgb(255 255 255 / 0.3);
}

.image-viewer-fade-enter-active,
.image-viewer-fade-leave-active {
  transition: opacity 0.2s ease;
}

.image-viewer-fade-enter-from,
.image-viewer-fade-leave-to {
  opacity: 0;
}
</style>
