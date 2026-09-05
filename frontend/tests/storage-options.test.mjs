import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import ts from 'typescript'

async function load(relativePath) {
  const source = await readFile(new URL(relativePath, import.meta.url), 'utf8')
  const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } })
  return import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`)
}
const { parseUserInfo, queryString } = await load('../src/utils/storage.ts')
const { parseQuestionOptions } = await load('../src/utils/questionOptions.ts')
const { errorMessage } = await load('../src/utils/errors.ts')

test('认证恢复拒绝坏 JSON、缺失字段和未知角色', () => {
  for (const input of [null, '{', '[]', '{}', '{"username":"a","role":"ROOT"}', '{"role":"ADMIN"}']) assert.equal(parseUserInfo(input), null)
  assert.deepEqual(parseUserInfo('{"username":"tester","role":"ADMIN"}'), { username: 'tester', role: 'ADMIN' })
})
test('路由重复参数只读取首值，空值归一为空字符串', () => {
  assert.equal(queryString(['栈', '队列']), '栈')
  for (const input of [undefined, null, [], [null]]) assert.equal(queryString(input), '')
})
test('复制导出同时支持对象与字符串选项，不把对象再次 JSON.parse', () => {
  const options = { A: '甲', B: '$x^2$', C: '丙', D: '丁' }
  assert.deepEqual(parseQuestionOptions(options), options)
  assert.deepEqual(parseQuestionOptions(JSON.stringify(options)), options)
  for (const input of [null, '{', [], { A: 1 }, { A: '甲' }]) assert.equal(parseQuestionOptions(input), null)
})
test('异常消息优先后端详情，未知输入有稳定兜底', () => {
  assert.equal(errorMessage({response:{data:{message:'无权限'}},message:'HTTP 403'}, '失败'), '无权限')
  assert.equal(errorMessage(new Error('超时'), '失败'), '超时')
  for (const input of [null, undefined, {}, 1]) assert.equal(errorMessage(input, '失败'), '失败')
})
