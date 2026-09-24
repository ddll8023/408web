import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import test from 'node:test'
import { parse, compileScript } from '@vue/compiler-sfc'
import { transform } from 'esbuild'
import { createRenderer, h, nextTick, Teleport } from 'vue'

const require = createRequire(import.meta.url)
const vueUrl = pathToFileURL(require.resolve('vue')).href

// 编译实际 SFC，仅替换过渡动画和响应式弹窗外壳；被测模板与事件处理保持真实。
function createDialogStub(tag = 'div', teleport = false) {
  return {
    props: ['visible', 'title'],
    setup(props, { slots }) {
      return () => {
        if (!props.visible) return null
        const children = [
          ...(props.title ? [h('h2', null, props.title)] : []),
          ...(slots.default?.() ?? []),
          ...(slots.footer?.() ?? []),
        ]
        const shell = h(tag, null, children)
        return teleport ? h(Teleport, { to: 'body' }, shell) : shell
      }
    },
  }
}

async function loadComponent(name) {
  if (name === 'ResponsiveDialog') return createDialogStub('div', true)
  const source = await readFile(new URL(`../src/components/basic/${name}.vue`, import.meta.url), 'utf8')
  const { descriptor } = parse(source.replaceAll('<transition ', '<test-transition ').replaceAll('</transition>', '</test-transition>'))
  const compiled = compileScript(descriptor, { id: name, inlineTemplate: true })
  const { code } = await transform(compiled.content, { loader: 'ts', format: 'esm' })
  let moduleCode = code.replaceAll('from "vue"', `from ${JSON.stringify(vueUrl)}`).replaceAll("from 'vue'", `from ${JSON.stringify(vueUrl)}`)
  const responsiveTestModules = {
    '@/shared/responsive/breakpoints': 'export const MEDIA_QUERIES = { compact: "(max-width: 767px)" }',
    '@/shared/responsive/useViewport': 'export const useMediaQuery = () => ({ value: false })',
  }
  for (const [specifier, source] of Object.entries(responsiveTestModules)) {
    const childUrl = `data:text/javascript,${encodeURIComponent(source)}`
    moduleCode = moduleCode.replaceAll(JSON.stringify(specifier), JSON.stringify(childUrl))
  }
  for (const [, childName] of moduleCode.matchAll(/from ["']\.\/([A-Z][A-Za-z0-9]*)\.vue["']/g)) {
    const child = await loadComponent(childName)
    const key = `__componentTest_${name}_${childName}_${Date.now()}_${Math.random().toString(36).slice(2)}`
    globalThis[key] = child
    const childUrl = `data:text/javascript,${encodeURIComponent(`export default globalThis.${key}`)}`
    moduleCode = moduleCode.replaceAll(JSON.stringify(`./${childName}.vue`), JSON.stringify(childUrl))
  }
  const module = await import(`data:text/javascript;base64,${Buffer.from(moduleCode).toString('base64')}`)
  return module.default
}

class HostElement {
  constructor(tag, text = '') {
    this.tag = tag
    this.tagName = tag.toUpperCase()
    this.text = text
    this.props = {}
    this.children = []
    this.parent = null
    this.style = {}
    this.value = ''
  }
  getBoundingClientRect() { return { top: 0, height: 100 } }
  addEventListener() {}
  removeEventListener() {}
  focus() { this.focused = true }
  contains(target) { return this === target || this.children.some(child => child.contains(target)) }
}

globalThis.HTMLElement = HostElement
globalThis.HTMLInputElement = HostElement
globalThis.HTMLSelectElement = HostElement
globalThis.Element = HostElement
globalThis.Node = HostElement
globalThis.document = { addEventListener() {}, removeEventListener() {} }
globalThis.window = {
  innerWidth: 1024,
  innerHeight: 768,
  addEventListener() {},
  removeEventListener() {},
}

function mount(component, props = {}) {
  const root = new HostElement('root')
  const body = new HostElement('body')
  const renderer = createRenderer({
    createElement: tag => new HostElement(tag),
    createText: text => new HostElement('#text', text),
    createComment: text => new HostElement('#comment', text),
    setText: (node, text) => { node.text = text },
    setElementText: (node, text) => { node.text = text; node.children = [] },
    parentNode: node => node.parent,
    nextSibling: node => node.parent?.children[node.parent.children.indexOf(node) + 1] ?? null,
    querySelector: () => body,
    patchProp: (node, key, oldValue, value) => { node.props[key] = value },
    insert(node, parent, anchor = null) {
      if (node.parent) node.parent.children.splice(node.parent.children.indexOf(node), 1)
      const index = anchor ? parent.children.indexOf(anchor) : -1
      parent.children.splice(index < 0 ? parent.children.length : index, 0, node)
      node.parent = parent
    },
    remove(node) {
      if (node.parent) node.parent.children.splice(node.parent.children.indexOf(node), 1)
      node.parent = null
    },
  })
  const app = renderer.createApp(component, props)
  const warnings = []
  app.config.warnHandler = message => warnings.push(message)
  app.component('TestTransition', (_, { slots }) => slots.default?.())
  app.component('FontAwesomeIcon', () => h('icon'))
  const instance = app.mount(root)
  return { root, body, instance, warnings, unmount: () => app.unmount() }
}

function all(node, predicate) {
  return [...(predicate(node) ? [node] : []), ...node.children.flatMap(child => all(child, predicate))]
}
function text(node) { return node.tag === '#comment' ? '' : node.text + node.children.map(text).join('') }
function click(node) { node.props.onClick({ stopPropagation() {}, preventDefault() {} }) }

test('Confirm renders supplied text and calls confirm exactly once', async () => {
  const component = await loadComponent('Confirm')
  const view = mount(component)
  let confirmed = 0
  view.instance.show({ title: '迁移确认', message: '保留测试数据', confirmText: '继续', cancelText: '返回' }, () => confirmed++)
  await nextTick()
  const content = text(view.body)
  for (const expected of ['迁移确认', '保留测试数据', '继续', '返回']) assert.ok(content.includes(expected), expected)
  click(all(view.body, node => node.tag === 'button' && text(node) === '继续')[0])
  await nextTick()
  assert.equal(confirmed, 1)
  assert.equal(all(view.body, node => node.tag === 'button').length, 0)
  view.unmount()
})

test('Select native change preserves numeric option values and emits empty selection', async () => {
  const component = await loadComponent('Select')
  const updates = []
  const changes = []
  const view = mount(component, { modelValue: null, options: [{ label: '零', value: 0 }, { label: '科目', value: 2 }], 'onUpdate:modelValue': value => updates.push(value), onChange: value => changes.push(value) })
  const select = all(view.root, node => node.tag === 'select')[0]
  for (const value of ['0', '2', '']) {
    select.value = value
    select.props.onChange({ target: select })
  }
  assert.deepEqual(updates, [0, 2, ''])
  assert.deepEqual(changes, updates)
  view.unmount()
})

test('WheelPicker clearing emits null and accepts null without prop warnings', async () => {
  const component = await loadComponent('WheelPicker')
  const updates = []
  const view = mount(component, { modelValue: 2024, options: [{ label: '2024年', value: 2024 }], clearable: true, 'onUpdate:modelValue': value => updates.push(value) })
  click(all(view.root, node => String(node.props.class).includes('ml-2 cursor-pointer'))[0])
  assert.deepEqual(updates, [null])
  view.unmount()
  const empty = mount(component, { modelValue: null, options: [{ label: '2024年', value: 2024 }] })
  assert.ok(text(empty.root).includes('请选择'))
  assert.deepEqual(empty.warnings, [])
  empty.unmount()
})

test('SubjectManage renders editable controls and accepts the backend hyphenated code', async () => {
  const updates = []
  const subject = { id: 1, code: 'data-structure', name: '数据结构', description: '基础科目', orderNum: 2, enabled: true }
  globalThis.__subjectTestApi = {
    getAllSubjects: async () => ({ code: 200, data: [subject] }),
    updateSubject: async (id, data) => { updates.push({ id, data }); return { code: 200, data: subject } },
    createSubject: async () => { throw new Error('Unexpected create') },
    deleteSubject: async () => { throw new Error('Unexpected delete') },
  }
  const url = code => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`
  const source = await readFile(new URL('../src/views/admin/SubjectManage.vue', import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const script = compileScript(descriptor, { id: 'subject-manage', inlineTemplate: true })
  let { code } = await transform(script.content, { loader: 'ts', format: 'esm' })
  code = code.replaceAll('from "vue"', `from ${JSON.stringify(vueUrl)}`).replaceAll("from 'vue'", `from ${JSON.stringify(vueUrl)}`)
  for (const [specifier, replacement] of [
    ['@/api/subject', 'export const { getAllSubjects, createSubject, updateSubject, deleteSubject } = globalThis.__subjectTestApi'],
    ['@/composables/useToast', 'export const useToast = () => ({ showToast() {} })'],
    ['@/composables/useConfirm', 'export const useConfirm = () => ({ showConfirm: async () => false })'],
  ]) code = code.replaceAll(JSON.stringify(specifier), JSON.stringify(url(replacement)))

  // Use the actual FormLabel and inputs. Mock only the outer dialog shell, since its layout is tested in-browser.
  globalThis.__subjectTestComponents = {}
  const componentNames = [...code.matchAll(/"@\/components\/basic\/(\w+)\.vue"/g)].map(match => match[1])
  for (const name of componentNames) {
    globalThis.__subjectTestComponents[name] = ['Dialog', 'ResponsiveDialog'].includes(name)
      ? createDialogStub('dialog')
      : await loadComponent(name)
    code = code.replaceAll(JSON.stringify(`@/components/basic/${name}.vue`), JSON.stringify(url(`export default globalThis.__subjectTestComponents.${name}`)))
  }
  const { default: page } = await import(url(code))
  const view = mount(page)
  await new Promise(resolve => setImmediate(resolve))
  await nextTick()
  click(all(view.root, node => node.tag === 'button' && text(node).trim() === '编辑')[0])
  await nextTick()
  const dialog = all(view.root, node => node.tag === 'dialog')[0]
  assert.ok(dialog, 'edit dialog must open')
  assert.equal(all(dialog, node => node.tag === 'input').length, 3, 'code, name and order inputs must render')
  assert.equal(all(dialog, node => node.tag === 'textarea').length, 1)
  assert.equal(all(dialog, node => node.props.role === 'switch').length, 1)
  assert.equal(all(dialog, node => node.props.id === 'subject-code' && node.tag === 'input')[0].props.value, 'data-structure')
  click(all(dialog, node => node.tag === 'button' && text(node).trim() === '确定')[0])
  await new Promise(resolve => setImmediate(resolve))
  assert.equal(updates.length, 1, 'valid hyphenated backend code must not block saving')
  assert.equal(updates[0].id, 1)
  assert.equal(updates[0].data.code, 'data-structure')
  assert.equal(updates[0].data.orderNum, 2)
  view.unmount()
  delete globalThis.__subjectTestApi
  delete globalThis.__subjectTestComponents
})

