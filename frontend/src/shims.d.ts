/**
 * 无官方类型声明的第三方库 shim。
 * 仅覆盖本项目实际使用的导入路径，保持最小声明。
 */
declare module '@kangc/v-md-editor' {
  import type { DefineComponent } from 'vue'
  const VMdEditor: DefineComponent<Record<string, never>, Record<string, never>, unknown>
  export default VMdEditor
}

declare module '@kangc/v-md-editor/lib/preview' {
  import type { DefineComponent } from 'vue'
  const VMdPreview: DefineComponent<Record<string, never>, Record<string, never>, unknown>
  export default VMdPreview
}

declare module '@kangc/v-md-editor/lib/theme/github.js' {
  const githubTheme: (md: unknown) => void
  export default githubTheme
}
