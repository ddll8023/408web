/**
 * 前端响应式断点定义。
 * CSS 与需要 JavaScript 行为切换的组件均以这里的断点约定为准，避免各处出现不同阈值。
 */

export const BREAKPOINTS = {
  xs: 420,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const

export const MEDIA_QUERIES = {
  compact: `(max-width: ${BREAKPOINTS.md - 1}px)`,
  wide: `(min-width: ${BREAKPOINTS.md}px)`,
  navigationCompact: `(max-width: ${BREAKPOINTS.xl - 1}px)`,
  navigationWide: `(min-width: ${BREAKPOINTS.xl}px)`,
} as const

export type ViewportMode = 'compact' | 'wide'
