/**
 * 第三方模块类型补充：编辑器封装用到的 v-md-editor 接口，以及 markdown-it 的最小可用类型；
 * 声明形状与已安装包源码核对，不做超出项目用法的扩展。
 */

/**
 * markdown-it 未随包提供类型声明，此处只声明项目实际用到的渲染规则形状（fence 钩子）；
 * 若后续安装官方 @types/markdown-it，应删除本声明并改用官方类型。
 */
declare module 'markdown-it' {
  export interface MarkdownItToken {
    info: string
    content: string
  }
  export interface MarkdownItRenderer {
    rules: Record<string, MarkdownItRenderRule | undefined>
    renderToken(tokens: MarkdownItToken[], idx: number, options: unknown): string
  }
  export type MarkdownItRenderRule = (
    tokens: MarkdownItToken[],
    idx: number,
    options: unknown,
    env: unknown,
    self: MarkdownItRenderer,
  ) => string
  export default class MarkdownIt {
    renderer: MarkdownItRenderer
    constructor(preset?: unknown, options?: unknown)
    /** 覆盖实例选项（项目用于开启 HTML 支持） */
    set(options: Record<string, unknown>): void
  }
}

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
