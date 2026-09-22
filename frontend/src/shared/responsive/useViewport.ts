/**
 * 响应式视口状态。
 * 仅为确实存在交互差异的组件提供媒体查询状态，纯布局变化仍由 CSS 负责。
 */
import { computed, onMounted, onUnmounted, ref, type Ref } from 'vue'
import type { ViewportMode } from './breakpoints'
import { MEDIA_QUERIES } from './breakpoints'

/** 监听一个媒体查询并在组件卸载时清理监听器。 */
export function useMediaQuery(query: string): Readonly<Ref<boolean>> {
  const matches = ref(false)
  let mediaQuery: MediaQueryList | null = null

  const createMediaQuery = () => {
    if (mediaQuery || typeof window === 'undefined' || typeof window.matchMedia !== 'function') return

    mediaQuery = window.matchMedia(query)
    matches.value = mediaQuery.matches
  }

  // 浏览器环境下在 setup 阶段同步读取，避免响应式弹层首次渲染到错误形态。
  createMediaQuery()

  const handleChange = (event: MediaQueryListEvent) => {
    matches.value = event.matches
  }

  const removeListener = () => {
    if (!mediaQuery) return

    if (typeof mediaQuery.removeEventListener === 'function') {
      mediaQuery.removeEventListener('change', handleChange)
    } else {
      mediaQuery.removeListener(handleChange)
    }
    mediaQuery = null
  }

  onMounted(() => {
    createMediaQuery()
    if (!mediaQuery) return

    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handleChange)
    } else {
      mediaQuery.addListener(handleChange)
    }
  })

  onUnmounted(removeListener)

  return matches
}

/** 提供项目统一的宽屏/窄屏视口状态。 */
export function useViewport() {
  const isCompact = useMediaQuery(MEDIA_QUERIES.compact)
  const isWide = useMediaQuery(MEDIA_QUERIES.wide)
  const mode = computed<ViewportMode>(() => (isCompact.value ? 'compact' : 'wide'))

  return {
    isCompact,
    isWide,
    mode,
  }
}
