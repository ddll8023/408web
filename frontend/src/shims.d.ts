/** Third-party APIs used by the editor wrappers, checked against installed package source. */
declare module '@kangc/v-md-editor' {
  import type { DefineComponent } from 'vue'
  import type MarkdownIt from 'markdown-it'
  import type { HLJSApi } from 'highlight.js'
  export interface EditorInstance {
    $el: HTMLElement
    $refs: { editorEgine?: { getRange(): { start: number; end: number }; setRange(range: { start: number; end: number }): void } }
    insert(callback: () => { text: string; selected: string }): void
    getCurrentSelectedStr(): string
    replaceSelectionText(text: string): void
  }
  export interface ThemeOptions { Hljs: HLJSApi; extend(md: MarkdownIt): void }
  export interface MarkdownStatic { use(theme: unknown, options: ThemeOptions): void; xss: { extend(options: { whiteList: Record<string, string[]> }): void } }
  const editor: DefineComponent<{ modelValue?: string; height?: string; placeholder?: string; leftToolbar?: string; rightToolbar?: string; toolbar?: object; mode?: string }, {}, {}, {}, {}, {}, {}, { 'update:modelValue': (value: string) => void; save: (text: string, html: string) => void }> & MarkdownStatic
  export default editor
}
declare module '@kangc/v-md-editor/lib/preview' {
  import type { DefineComponent } from 'vue'
  import type { MarkdownStatic } from '@kangc/v-md-editor'
  const preview: DefineComponent<{ text?: string }, {}, {}, {}, {}, {}, {}, { imageClick: (images: string[], index: number) => void }> & MarkdownStatic
  export default preview
}
declare module '@kangc/v-md-editor/lib/theme/github.js' {
  const theme: unknown
  export default theme
}
