import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { createRequire } from 'node:module'
import ts from 'typescript'
import { ref, createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'

const require = createRequire(import.meta.url)
const src = resolve(dirname(fileURLToPath(import.meta.url)), '../src')
const cache = new Map()
// 使用真实 composable，仅隔离浏览器通知、科目加载及网络，测试不写服务器数据。
async function moduleUrl(path) {
  if (cache.has(path)) return cache.get(path)
  const source = await readFile(path, 'utf8')
  let output = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  for (const [, specifier] of [...output.matchAll(/from ['"]([^'"]+)['"]/g)]) {
    let url
    if (specifier === 'element-plus') {
      url = 'data:text/javascript,' + encodeURIComponent('export const ElMessage = { warning() {}, error() {}, success() {} }; export const ElMessageBox = { alert() {} }')
    } else if (specifier === './useSubjects') {
      url = 'data:text/javascript,' + encodeURIComponent('export function useSubjects() { return { subjectOptions: [], loadSubjectOptions: async () => {} } }')
    } else if (specifier === '@/api/category') {
      url = 'data:text/javascript,' + encodeURIComponent('export async function getEnabledCategoriesBySubject() { return {code:200,data:[]} }; export async function getEnabledCategoryTreeBySubject() { return {code:200,data:[]} }')
    } else if (specifier.startsWith('@/') || specifier.startsWith('.')) {
      url = await moduleUrl((specifier.startsWith('@/') ? resolve(src, specifier.slice(2)) : resolve(dirname(path), specifier)) + '.ts')
    } else {
      url = pathToFileURL(require.resolve(specifier)).href
    }
    output = output.replaceAll(`'${specifier}'`, JSON.stringify(url)).replaceAll(`"${specifier}"`, JSON.stringify(url))
  }
  const url = 'data:text/javascript;base64,' + Buffer.from(output).toString('base64')
  cache.set(path, url)
  return url
}
const { useJsonImport } = await import(await moduleUrl(resolve(src, 'composables/useJsonImport.ts')))
const { useQuestionForm } = await import(await moduleUrl(resolve(src, 'composables/useQuestionForm.ts')))
const { useFavorites } = await import(await moduleUrl(resolve(src, 'composables/useFavorites.ts')))
const { useCategoryDrag } = await import(await moduleUrl(resolve(src, 'composables/useCategoryDrag.ts')))

test('JSON 导入保留中英文、公式及字符串化选项，拒绝错误字段类型', () => {
  const { parseJsonWithRelaxedSupport: parse } = useJsonImport()
  const data = { questionType: 'CHOICE', year: 2024, questionNumber: 2, subjectId: 1, content: '$\\frac{1}{2}$ 与栈', category: ['栈'], options: JSON.stringify({ A: '甲', B: '乙', C: '丙', D: '丁' }), difficulty: 'MEDIUM' }
  const parsed = parse(JSON.stringify(data))
  assert.equal(parsed.content, data.content)
  assert.deepEqual(parsed.options, { A: '甲', B: '乙', C: '丙', D: '丁' })
  for (const invalid of ['[]', 'null', '{"questionType":"OTHER"}', '{"subjectId":"1"}', '{"category":[1]}', '{"difficulty":"UNKNOWN"}', '{"content":{}}']) {
    assert.throws(() => parse(invalid))
  }
})

test('宽松 JSON 导入修复 LaTeX 无效转义而不丢反斜杠', () => {
  const { parseJsonWithRelaxedSupport: parse } = useJsonImport()
  const parsed = parse(String.raw`{
  "content": "公式 \\alpha 与 \sqrt{x}",
  "answer": "完成"
}`)
  assert.equal(parsed.content, String.raw`公式 \alpha 与 \sqrt{x}`)
})

test('题目表单填充与提交：分类字符串、A-D、空值及主观题选项清理', async () => {
  const state = useQuestionForm({ extraFields: { source: '来源' } })
  await state.fillFormFromData({ questionType: 'CHOICE', subjectId: 1, content: '题干', options: '{"A":"甲","B":"乙","C":"丙","D":"丁"}', category: '["树","图"]', answer: 'B', difficulty: 'HARD' })
  assert.deepEqual(state.form.category, ['树', '图'])
  const request = state.buildSubmitData({ source: state.form.source, questionNumber: 3 })
  assert.deepEqual(request.options, { A: '甲', B: '乙', C: '丙', D: '丁' })
  assert.equal(request.source, '来源')
  assert.equal(request.questionNumber, 3)
  await state.fillFormFromData({ question_type: 'ESSAY', content: '主观题', category: '链表', answer: null })
  assert.deepEqual(state.form.category, ['链表'])
  assert.equal(state.form.optionA, '')
  const essay = state.buildSubmitData({ source: '来源' })
  assert.equal(essay.options, null)
  assert.equal(essay.subjectId, null)
  assert.equal(essay.answer, null)
  assert.equal(essay.difficulty, null)
})

test('收藏恢复过滤损坏结构，并保持去重、删除和持久化一致', t => {
  const errors = t.mock.method(console, 'error', () => {})
  let stored = '{bad json'
  globalThis.localStorage = { getItem: () => stored, setItem: (_, value) => { stored = value } }
  const favorites = useFavorites()
  assert.deepEqual(favorites.favorites.value, [])
  assert.equal(errors.mock.callCount(), 1)
  stored = JSON.stringify([{ id: '1_栈', subjectId: 1, subjectName: '数据结构', category: '栈', timestamp: 1 }, { category: '坏数据' }, null])
  favorites.loadFavorites()
  assert.equal(favorites.totalCount.value, 1)
  assert.equal(favorites.addFavorite({ subjectId: 1, subjectName: '数据结构', category: '栈' }), false)
  assert.equal(favorites.addFavorite({ subjectId: 1, subjectName: '数据结构', category: '图' }), true)
  assert.equal(favorites.removeFavorite(1, '栈'), true)
  assert.deepEqual(JSON.parse(stored).map(item => item.category), ['图'])
})

test('分类拖拽拒绝自身、子孙、跨科目及无变化，接受有效同级移动', async () => {
  const node = (id, parentId, orderNum, subjectId = 1) => ({ id, parentId, orderNum, subjectId, name: String(id), code: String(id), enabled: true })
  const categories = ref([node(1, null, 1), node(2, null, 2), node(3, 1, 1), node(4, null, 1, 2)])
  let drag
  await renderToString(createSSRApp({ setup() {
    drag = useCategoryDrag({ categories, enabled: ref(true), containerRef: ref(null), expandedKeys: ref([]), onMove() { throw new Error('不应持久化') } })
    return () => null
  } }))
  assert.equal(drag.canMove(1, { targetId: 1, position: 'inside' }), false)
  assert.equal(drag.canMove(1, { targetId: 3, position: 'inside' }), false)
  assert.equal(drag.canMove(1, { targetId: 4, position: 'before' }), false)
  assert.equal(drag.canMove(1, { targetId: 2, position: 'before' }), false)
  assert.equal(drag.canMove(1, { targetId: 2, position: 'after' }), true)
  assert.equal(drag.canMove(3, { targetId: null, position: 'inside' }), true)
})

test('确认框取消明确返回 false，确认返回 true', async t => {
  const runtimeKey = '__businessConfirmTestRuntime'
  globalThis[runtimeKey] = {
    result: 'confirm'
  }
  t.after(() => { delete globalThis[runtimeKey] })
  const source = await readFile(resolve(src, 'composables/useConfirm.ts'), 'utf8')
  let output = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  const stubs = {
    '@/utils/confirm': `export default () => globalThis.${runtimeKey}.result === 'cancel' ? Promise.reject('cancel') : Promise.resolve('confirm')`
  }
  for (const [specifier, stub] of Object.entries(stubs)) output = output.replaceAll(`'${specifier}'`, JSON.stringify('data:text/javascript,' + encodeURIComponent(stub)))
  const { useConfirm } = await import('data:text/javascript;base64,' + Buffer.from(output).toString('base64'))
  for (const [result, expected] of [['cancel', false], ['confirm', true]]) {
    globalThis[runtimeKey].result = result
    assert.equal(
      await useConfirm().showConfirm({ title: '测试确认', message: '仅内存测试' }),
      expected
    )
  }
})
