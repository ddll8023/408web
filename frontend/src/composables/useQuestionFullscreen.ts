/**
 * 题目卡片全屏 composable。
 * 优先使用 Fullscreen API 让单选题目卡片真正占满屏幕；环境不支持元素全屏
 * （例如 iOS Safari）或请求被拒绝时，降级为固定覆盖层的沉浸模式。
 */
import { computed, onBeforeUnmount, ref, type Ref } from 'vue'

/**
 * 单张题目卡片的进入/退出全屏能力。
 * 退出方法单独导出，供打开弹层的场景在调用模型前先退出全屏或沉浸模式。
 * @param target 卡片根元素引用，全屏目标同时也是全屏状态的判定依据
 */
export function useQuestionFullscreen(target: Ref<HTMLElement | null>) {
  const isFullscreen = ref(false)
  const isImmersive = ref(false)
  /** 全屏或沉浸模式是否处于激活状态，供卡片与头部按钮统一使用。 */
  const isActive = computed(() => isFullscreen.value || isImmersive.value)

  /** 进入沉浸模式前的 body 溢出值，用于退出时恢复原状。 */
  let previousBodyOverflow = ''

  /** 检测当前环境是否支持对任意元素调用全屏。 */
  const supportsElementFullscreen = () =>
    typeof document !== 'undefined' &&
    document.fullscreenEnabled === true &&
    typeof Element !== 'undefined' &&
    typeof Element.prototype.requestFullscreen === 'function'

  /** 同步浏览器实际的全屏元素，覆盖 Esc 退出等由浏览器触发的变化。 */
  const syncFullscreenState = () => {
    isFullscreen.value = document.fullscreenElement === target.value
  }

  const lockBodyScroll = () => {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  }

  const unlockBodyScroll = () => {
    document.body.style.overflow = previousBodyOverflow
  }

  /** 沉浸模式不支持浏览器级退出键，需要自行响应 Esc。 */
  function handleImmersiveKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') void exit()
  }

  function enterImmersive() {
    isImmersive.value = true
    lockBodyScroll()
    document.addEventListener('keydown', handleImmersiveKeydown)
  }

  function leaveImmersive() {
    if (!isImmersive.value) return
    isImmersive.value = false
    document.removeEventListener('keydown', handleImmersiveKeydown)
    unlockBodyScroll()
  }

  /** 退出全屏或沉浸模式，两种状态都归零。 */
  async function exit() {
    leaveImmersive()
    if (document.fullscreenElement === target.value) {
      await document.exitFullscreen().catch(() => undefined)
    }
    syncFullscreenState()
  }

  /** 进入全屏；浏览器请求失败时回退到沉浸模式，避免按钮点了没反应。 */
  const enter = async () => {
    const element = target.value
    if (!element) return

    if (!supportsElementFullscreen()) {
      enterImmersive()
      return
    }

    try {
      await element.requestFullscreen()
    } catch {
      enterImmersive()
      return
    }
    syncFullscreenState()
  }

  /** 切换当前卡片的展示模式。 */
  const toggleFullscreen = () => {
    if (isActive.value) {
      void exit()
      return
    }
    void enter()
  }

  document.addEventListener('fullscreenchange', syncFullscreenState)

  onBeforeUnmount(() => {
    document.removeEventListener('fullscreenchange', syncFullscreenState)
    leaveImmersive()
    if (document.fullscreenElement === target.value) {
      void document.exitFullscreen().catch(() => undefined)
    }
  })

  return { isFullscreen, isImmersive, isActive, toggleFullscreen, exit }
}
