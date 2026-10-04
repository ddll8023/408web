<!-- 生成答案预览：正文复用安全 AI 渲染，仅为独立 svg 代码块开放受限图形，不修改咨询白名单。 -->
<template>
  <div class="generated-answer-viewer">
    <template v-for="(block, index) in blocks" :key="index">
      <div v-if="block.svg" class="answer-diagram" role="img" aria-label="答案图示" v-html="block.svg"></div>
      <AiAnswerViewer v-else :content="block.text" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import AiAnswerViewer from '@/components/basic/AiAnswerViewer.vue'

const props = withDefaults(defineProps<{ content: string; renderSvg?: boolean }>(), { renderSvg: true })
const emit = defineEmits<{ 'validity-change': [valid: boolean] }>()

const markdown = new MarkdownIt('commonmark', { html: false })
const SVG_NS = 'http://www.w3.org/2000/svg'
const elements = new Set(['svg', 'g', 'line', 'path', 'circle', 'ellipse', 'rect', 'polygon', 'polyline', 'text', 'tspan'])
const attributes = new Set([
  'viewBox', 'preserveAspectRatio', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
  'width', 'height', 'd', 'points', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity',
  'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin', 'opacity',
  'font-size', 'font-weight', 'font-family', 'text-anchor', 'dominant-baseline', 'dx', 'dy', 'transform',
])

/** XML 在离线文档中解析，再逐节点重建；不复制原始 HTML、命名空间属性或资源引用。 */
function safeSvg(source: string): string | null {
  if (source.length > 65536 || /<!DOCTYPE|<!ENTITY/i.test(source)) return null
  const parsed = new DOMParser().parseFromString(source, 'image/svg+xml')
  const root = parsed.documentElement
  if (parsed.querySelector('parsererror') || root.localName !== 'svg' || root.namespaceURI !== SVG_NS) return null
  const viewBox = root.getAttribute('viewBox')?.trim().split(/[\s,]+/).map(Number)
  if (!viewBox || viewBox.length !== 4 || viewBox.some(value => !Number.isFinite(value) || Math.abs(value) > 100000)
    || viewBox[2] <= 0 || viewBox[3] <= 0) return null
  let count = 0
  function copy(node: Element, depth = 0): SVGElement | null {
    if (depth > 64 || ++count > 2000 || !elements.has(node.localName) || node.namespaceURI !== SVG_NS) return null
    const clean = document.createElementNS(SVG_NS, node.localName)
    for (const attr of Array.from(node.attributes)) {
      if (attr.name === 'xmlns' && attr.value === SVG_NS) continue
      if (/^on|href|style/i.test(attr.name) || /url\s*\(|javascript:|data:|https?:/i.test(attr.value)) return null
      if (!attributes.has(attr.name) || attr.namespaceURI) return null
      if (attr.value.length > 50000) return null
      if (['fill', 'stroke'].includes(attr.name)
        && !/^(?:none|transparent|currentColor|#[\da-f]{3,8}|[a-z]+|rgba?\([\d\s.,%]+\))$/i.test(attr.value.trim())) return null
      clean.setAttribute(attr.name, attr.value)
    }
    for (const child of Array.from(node.childNodes)) {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const copied = copy(child as Element, depth + 1)
        if (!copied) return null
        clean.append(copied)
      } else if (child.nodeType === Node.TEXT_NODE || child.nodeType === Node.CDATA_SECTION_NODE) {
        clean.append(document.createTextNode(child.textContent || ''))
      }
    }
    return clean
  }
  const clean = copy(root)
  if (!clean) return null
  clean.setAttribute('xmlns', SVG_NS)
  clean.removeAttribute('width')
  clean.removeAttribute('height')
  return new XMLSerializer().serializeToString(clean)
}

/** 流式阶段只显示源码，完整终态才解析图形；失败图形回显代码而不注入 DOM。 */
const parsedBlocks = computed(() => {
  const blocks: { text: string; svg?: string }[] = []
  const lineOffsets = [0]
  for (let index = 0; index < props.content.length; index++) {
    if (props.content[index] === '\n') lineOffsets.push(index + 1)
  }
  let offset = 0
  let valid = true
  for (const token of markdown.parse(props.content, {})) {
    if (token.type !== 'fence' || token.info.trim().toLowerCase() !== 'svg' || !token.map) continue
    const start = lineOffsets[token.map[0]] ?? props.content.length
    const end = lineOffsets[token.map[1]] ?? props.content.length
    if (start > offset) blocks.push({ text: props.content.slice(offset, start) })
    const svg = props.renderSvg ? safeSvg(token.content) : null
    if (props.renderSvg && !svg) valid = false
    blocks.push(svg ? { text: '', svg } : { text: props.content.slice(start, end) })
    offset = end
  }
  if (offset < props.content.length) blocks.push({ text: props.content.slice(offset) })
  return { blocks, valid }
})
const blocks = computed(() => parsedBlocks.value.blocks)
watch(() => parsedBlocks.value.valid, valid => emit('validity-change', valid), { immediate: true })
</script>

<style scoped>
.generated-answer-viewer { overflow-wrap: anywhere; min-width: 0; }
.answer-diagram { margin: 1rem 0; padding: .75rem; border: 1px solid var(--brand-line, #e5e7eb); border-radius: .5rem; overflow-x: auto; background: white; }
.answer-diagram :deep(svg) { display: block; width: 100%; height: auto; max-height: 520px; font-family: inherit; }
</style>
