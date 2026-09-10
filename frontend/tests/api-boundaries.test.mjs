import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { createRequire } from 'node:module'
import ts from 'typescript'

// 转译真实生产模块；只替换浏览器通知和环境变量，不复制业务实现。
const require = createRequire(import.meta.url)
const axios = require('axios')
const src = resolve(dirname(fileURLToPath(import.meta.url)), '../src')
const messages = []
globalThis.__apiTestMessages = messages
globalThis.localStorage = { getItem: () => 'test-token', removeItem() {} }
const cache = new Map()
async function moduleUrl(path) {
  if (cache.has(path)) return cache.get(path)
  const source = (await readFile(path, 'utf8')).replace('import.meta.env.VITE_API_BASE_URL', 'undefined')
  let output = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  const imports = [...output.matchAll(/from ['"]([^'"]+)['"]/g)]
  for (const [, specifier] of imports) {
    let url
    if (specifier === '@/utils/toast') {
      url = 'data:text/javascript,' + encodeURIComponent('export const toast = { error: message => globalThis.__apiTestMessages.push(message) }')
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
let responseData
let lastConfig
axios.defaults.adapter = async config => {
  lastConfig = config
  return { data: responseData, status: 200, statusText: 'OK', headers: { 'content-disposition': 'attachment; filename="exam.md"' }, config }
}
const convert = await import(await moduleUrl(resolve(src, 'utils/convertKeys.ts')))
const exam = await import(await moduleUrl(resolve(src, 'api/exam.ts')))
const mock = await import(await moduleUrl(resolve(src, 'api/mock.ts')))
const upload = await import(await moduleUrl(resolve(src, 'api/upload.ts')))
const { default: request } = await import(await moduleUrl(resolve(src, 'api/request.ts')))

test('转换嵌套响应、空值和分类，拒绝错误分类内容', () => {
  assert.deepEqual(convert.convertKeysToCamel({ subject_id: 2, nested_rows: [{ question_number: 1 }], category: '["栈"]', empty_value: null }), {
    subjectId: 2, nestedRows: [{ questionNumber: 1 }], category: ['栈'], emptyValue: null
  })
  for (const invalid of ['', '{', '{}', '["栈",2]']) assert.deepEqual(convert.convertCategoryString(invalid), [])
  assert.deepEqual(convert.convertKeysToCamel([]), [])
  assert.equal(convert.convertKeysToCamel(null), null)
})

test('请求转换保留 A-D 选项键，省略 undefined 且保留 null', () => {
  assert.deepEqual(convert.convertKeysToSnake({ subjectId: 1, questionType: 'CHOICE', options: { A: '甲', B: '乙', C: '丙', D: '丁' }, category: null, answer: undefined }), {
    subject_id: 1, question_type: 'CHOICE', options: { A: '甲', B: '乙', C: '丙', D: '丁' }, category: null
  })
})

test('真题及模拟题分页映射、优先级、鉴权与 JSON 信封', async () => {
  responseData = { code: 200, message: '成功', data: { lists: [], pagination: { page: 1, page_size: 20, total: 0, total_pages: 0 } } }
  const result = await exam.getExamList({ size: 10, pageSize: 20, subjectId: 2 })
  assert.deepEqual(JSON.parse(lastConfig.data), { page_size: 20, subject_id: 2 })
  assert.equal(lastConfig.headers.Authorization, 'Bearer test-token')
  assert.equal(result.data.pagination.pageSize, 20)
  assert.equal(result.status, undefined)
  await mock.getMockQuestions({ size: 15, noCategory: true })
  assert.deepEqual(JSON.parse(lastConfig.data), { no_category: true, page_size: 15 })
})

test('删除成功的 null 数据不丢失', async () => {
  responseData = { code: 200, message: '删除成功', data: null }
  assert.deepEqual(await request({ url: '/test', method: 'post' }), responseData)
})

test('业务错误和畸形信封拒绝，不返回伪成功', async () => {
  responseData = { code: 400, message: '分类不存在', data: null }
  await assert.rejects(request({ url: '/test' }), /分类不存在/)
  responseData = { code: 200, data: [] }
  await assert.rejects(request({ url: '/test' }), /响应格式错误/)
  assert.ok(messages.includes('分类不存在'))
})

test('导出保留 Blob 与下载文件名响应头', async () => {
  responseData = new Blob(['# 真题'], { type: 'text/markdown' })
  const result = await exam.exportExamsBySubject(2)
  assert.equal(result.data, responseData)
  assert.equal(result.headers['content-disposition'], 'attachment; filename="exam.md"')
  assert.equal(lastConfig.responseType, 'blob')
  assert.deepEqual(JSON.parse(lastConfig.data), { subject_id: 2, format: 'markdown' })
})

 test('图片筛选使用 camelCase 输入并发送 snake_case', async () => {
  responseData = { code: 200, message: '成功', data: [] }
  await upload.getImageList({ onlyUnreferenced: true })
  assert.deepEqual(JSON.parse(lastConfig.data), { only_unreferenced: true })
  await upload.getImageList()
  assert.deepEqual(JSON.parse(lastConfig.data), { only_unreferenced: false })
})

test('图片地址兼容历史端口并保留外部地址', () => {
  assert.equal(upload.getImageUrl('/uploads/images/image.png'), 'http://localhost:7785/uploads/images/image.png')
  assert.equal(upload.getImageUrl('http://localhost:8081/uploads/images/image.png'), 'http://localhost:7785/uploads/images/image.png')
  assert.equal(upload.getImageUrl('https://cdn.example.com/image.png'), 'https://cdn.example.com/image.png')
  assert.equal(
    upload.normalizeImageUrls('![图片](http://localhost:8081/uploads/images/image.png)'),
    '![图片](http://localhost:7785/uploads/images/image.png)',
  )
})

test('图片上传保留 FormData 文件，不进入 JSON 字段转换', async () => {
  responseData = { code: 200, message: '成功', data: '/uploads/test.png' }
  const result = await upload.uploadImage(new Blob(['image-fixture'], { type: 'image/png' }))
  assert.equal(result, '/uploads/test.png')
  assert.ok(lastConfig.data instanceof FormData)
  const file = lastConfig.data.get('file')
  assert.ok(file instanceof Blob)
  assert.equal(await file.text(), 'image-fixture')
  assert.equal(file.type, 'image/png')
})
