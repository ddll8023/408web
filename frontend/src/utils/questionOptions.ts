/** 网络/导入数据可能是对象或 JSON 字符串；复制和导出共用同一解析边界。 */
export function parseQuestionOptions(input: unknown): Record<string, string> | null {
  let value: unknown = input
  if (typeof value === 'string') {
    try { value = JSON.parse(value) } catch { return null }
  }
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return null
  const options: Record<string, string> = {}
  for (const key of ['A', 'B', 'C', 'D']) {
    if (!(key in value)) return null
    const option: unknown = Reflect.get(value, key)
    if (typeof option !== 'string') return null
    options[key] = option
  }
  return options
}
