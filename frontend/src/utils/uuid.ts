/**
 * UUID 生成工具：crypto.randomUUID 仅在安全上下文（HTTPS 或 localhost）可用，
 * 手机经局域网 http://IP 访问时它是 undefined，因此回退到不受安全上下文限制的
 * crypto.getRandomValues 手动构造 v4，保证请求标识仍满足后端的 UUID 校验。
 */
export function createUuid(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  // 按 RFC 4122 设置版本号 4 与 variant 位，其余字节保持随机。
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}
