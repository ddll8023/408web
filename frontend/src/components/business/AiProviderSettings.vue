<!-- 单供应商配置：内置供应商只保存 Key，自定义供应商可编辑名称、接口地址与协议；检测单独确认额度。 -->
<template>
  <section class="space-y-4" :aria-busy="busy" aria-labelledby="ai-provider-title">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 id="ai-provider-title" class="text-lg font-medium text-ink">{{ provider.name }}</h3>
      <span class="text-sm text-ink-soft">{{ provider.hasApiKey ? '凭据已保存 · 调用权限未自动检测' : '尚未保存凭据' }}</span>
    </div>
    <div v-if="!provider.custom && provider.baseUrls.length" class="rounded-md border border-line bg-surface p-3 text-xs text-ink-soft">
      <p>服务端固定的服务地址</p>
      <p v-for="url in provider.baseUrls" :key="url" class="mt-1 break-all font-mono">{{ url }}</p>
    </div>
    <Alert v-if="!provider.supported" type="warning">{{ provider.unsupportedReason }}</Alert>
    <Alert v-if="errorMessage" type="error">{{ errorMessage }}</Alert>
    <form v-if="provider.supported" class="space-y-4" @submit.prevent="save">
      <template v-if="provider.custom">
        <div>
          <FormLabel label="供应商名称" :for-id="`${keyInputId}-name`" :required="true" class="mb-1" />
          <input :id="`${keyInputId}-name`" v-model="name" type="text" autocomplete="off" maxlength="200"
            :disabled="disabled || busy" :required="true" placeholder="例如 本机 Ollama、公司网关"
            class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        </div>
        <div>
          <FormLabel label="接口地址" :for-id="`${keyInputId}-base`" :required="true" class="mb-1" />
          <input :id="`${keyInputId}-base`" v-model="baseUrl" type="url" autocomplete="off" autocapitalize="none" :spellcheck="false"
            maxlength="2048" :disabled="disabled || busy" :required="true" placeholder="https://api.example.com/v1"
            :aria-describedby="`${keyInputId}-base-help`"
            class="h-[42px] w-full rounded-md border border-line bg-white px-4 font-mono text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
          <p :id="`${keyInputId}-base-help`" class="mt-1 text-xs text-ink-soft">填写上游服务的基础地址，通常以 /v1 结尾；支持 http(s)，服务端不跟随重定向。题目内容会发送到该地址。</p>
        </div>
        <div>
          <FormLabel label="上游协议" :for-id="`${keyInputId}-protocol`" :required="true" class="mb-1" />
          <Select :id="`${keyInputId}-protocol`" v-model="protocol" :options="PROTOCOLS" :disabled="disabled || busy" aria-label="上游协议" />
          <p class="mt-1 text-xs text-ink-soft">协议决定请求路径与参数形状；选错会在检测或咨询时暴露为调用失败。</p>
        </div>
      </template>
      <div>
        <FormLabel label="API Key" :for-id="keyInputId" :required="!provider.hasApiKey" class="mb-1" />
        <input :id="keyInputId" v-model="apiKey" type="password" autocomplete="off" autocapitalize="none" :spellcheck="false" maxlength="4096"
          :disabled="disabled || busy" :required="!provider.hasApiKey" :placeholder="provider.hasApiKey ? '已保存，留空保留；填写新值则替换' : '填写该供应商的 API Key'"
          :aria-describedby="`${keyInputId}-help`" class="h-[42px] w-full rounded-md border border-line bg-white px-4 text-ink focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50" />
        <p :id="`${keyInputId}-help`" class="mt-1 text-xs text-ink-soft">服务端加密保存，不回显、不写浏览器持久化存储。保存不会发送模型请求。</p>
      </div>
      <div class="flex items-center gap-2">
        <Switch :id="`${keyInputId}-enabled`" v-model="enabled" :disabled="disabled || busy" aria-label="启用该供应商" />
        <FormLabel label="启用该供应商" :for-id="`${keyInputId}-enabled`" />
      </div>
      <div class="flex flex-wrap gap-2">
        <CustomButton type="primary" :loading="operation === 'save'" :disabled="disabled || busy" @click="save">保存供应商</CustomButton>
        <CustomButton v-if="provider.configured" type="danger" :loading="operation === 'delete'" :disabled="disabled || busy" @click="remove">清除供应商</CustomButton>
      </div>
    </form>
    <div v-if="provider.supported" class="border-t border-line pt-4">
      <div class="flex flex-wrap items-center gap-3">
        <CustomButton :loading="operation === 'check'" :disabled="!canCheck" @click="check">检测所选模型</CustomButton>
        <CustomButton v-if="operation === 'check'" @click="cancelCheck">停止检测</CustomButton>
        <span v-if="checkedModel" role="status" class="text-sm text-ink">{{ checkedModel }} · 本次检测成功</span>
      </div>
      <p class="mt-2 text-xs text-ink-soft">先在目录中选择型号。检测会发一次短文本请求并可能消耗额度；不发送题目或聊天历史，不自动重试。</p>
      <p v-if="dirty" class="mt-1 text-xs text-ink-soft">有未保存的凭据设置，请先保存再检测。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { AiSettingsError, checkAiModel, deleteAiCustomProvider, deleteAiProvider, saveAiCustomProvider,
  saveAiProvider, type AiCatalogModelView, type AiCustomProviderView, type AiProtocol,
  type AiProviderConfigView, type AiProviderView } from '@/api/ai'
import Alert from '@/components/basic/Alert.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import Select from '@/components/basic/Select.vue'
import Switch from '@/components/basic/Switch.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { createUuid } from '@/utils/uuid'
import { useAuthStore } from '@/stores/auth'

const PROTOCOLS: { label: string; value: AiProtocol }[] = [
  { label: 'OpenAI Chat Completions', value: 'openai-completions' },
  { label: 'OpenAI Responses', value: 'openai-responses' },
  { label: 'Anthropic Messages', value: 'anthropic-messages' },
]

const props = defineProps<{ provider: AiProviderView; model: AiCatalogModelView | null; disabled?: boolean }>()
const emit = defineEmits<{
  saved: [config: AiProviderConfigView | AiCustomProviderView]
  deleted: [providerId: string]
  busyChange: [busy: boolean]
}>()
const authStore = useAuthStore()
const { showConfirm } = useConfirm()
const { showToast } = useToast()
const apiKey = ref('')
const name = ref(props.provider.name)
const baseUrl = ref(props.provider.baseUrl ?? '')
const protocol = ref<AiProtocol | ''>(props.provider.protocol ?? 'openai-completions')
const enabled = ref(props.provider.enabled || !props.provider.configured)
const operation = ref<'save' | 'delete' | 'check' | null>(null)
// 单供应商操作互斥，等待确认也属于操作中。
const busy = computed(() => operation.value !== null)
// 为当前供应商的 Key、帮助和启用开关生成稳定的关联标识。
const keyInputId = computed(() => `ai-key-${props.provider.id}`)
// 内置供应商只比较 Key 与启用状态；自定义供应商还需比较名称、地址与协议。
const dirty = computed(() => {
  if (Boolean(apiKey.value.trim()) || enabled.value !== props.provider.enabled) return true
  if (!props.provider.custom) return false
  return name.value.trim() !== props.provider.name || baseUrl.value.trim() !== (props.provider.baseUrl ?? '') ||
    protocol.value !== (props.provider.protocol ?? 'openai-completions')
})
// 检测只能使用已保存且未被局部修改的当前修订，不能偷偷检测未保存的 Key。
const canCheck = computed(() => !props.disabled && !busy.value && !dirty.value && props.provider.supported &&
  props.provider.hasApiKey && props.provider.enabled && props.provider.revision !== null && props.model?.provider === props.provider.id)
const errorMessage = ref('')
const checkedModel = ref('')
let sequence = 0
let controller: AbortController | null = null

/** 只接受三种已知协议，拒绝把空值或未知字符串当作可执行协议。 */
function isProtocol(value: string): value is AiProtocol {
  return value === 'openai-completions' || value === 'openai-responses' || value === 'anthropic-messages'
}

/** 校验自定义接口地址：只允许 http(s)，拒绝内嵌账号、查询串与片段，与服务端规则一致。 */
function validEndpoint(value: string): boolean {
  try {
    const url = new URL(value)
    return (url.protocol === 'http:' || url.protocol === 'https:') && Boolean(url.hostname) &&
      !url.username && !url.password && !url.search && !url.hash
  } catch {
    return false
  }
}

/** 绑定账号、供应商和序号并建立取消控制，清除旧检测结论，不保存请求对象。 */
function begin(action: 'save' | 'delete' | 'check') {
  const abort = new AbortController()
  controller = abort
  operation.value = action
  checkedModel.value = ''
  errorMessage.value = ''
  emit('busyChange', true)
  return { sequence: ++sequence, token: authStore.token, providerId: props.provider.id, abort }
}
type Context = ReturnType<typeof begin>
/** 只接受当前账号和供应商最新操作的未取消结果。 */
function current(context: Context): boolean {
  return context.sequence === sequence && context.token === authStore.token &&
    context.providerId === props.provider.id && !context.abort.signal.aborted
}
/** 原操作结束才释放子组件忙状态，迟到请求不能解除新操作的锁定。 */
function finish(context: Context): void {
  if (context.sequence !== sequence) return
  controller = null
  operation.value = null
  emit('busyChange', false)
}
/** 取消和失效结果不报错，只展示经过 API 边界脱敏的安全消息。 */
function fail(error: unknown, context: Context): void {
  if (!current(context) || (error instanceof AiSettingsError && error.cancelled)) return
  errorMessage.value = error instanceof AiSettingsError ? error.message : '供应商操作失败，请稍后重试'
}
/** 内置供应商保存 Key；自定义供应商同时保存名称、地址与协议，成功后清空局部明文且不自动检测。 */
async function save(): Promise<void> {
  if (props.disabled || busy.value || !authStore.token || !props.provider.supported) return
  if (!props.provider.hasApiKey && !apiKey.value.trim()) { errorMessage.value = '首次保存请填写 API Key'; return }
  if (props.provider.custom) {
    const endpoint = baseUrl.value.trim()
    if (!name.value.trim()) { errorMessage.value = '请填写供应商名称'; return }
    if (!validEndpoint(endpoint)) { errorMessage.value = '接口地址格式无效，请填写 http(s) 地址'; return }
    if (!isProtocol(protocol.value)) { errorMessage.value = '请选择上游协议'; return }
  }
  const selectedProtocol = isProtocol(protocol.value) ? protocol.value : 'openai-completions'
  const context = begin('save')
  try {
    const response = props.provider.custom
      ? await saveAiCustomProvider({ providerId: props.provider.id, name: name.value.trim(), baseUrl: baseUrl.value.trim(),
        protocol: selectedProtocol, enabled: enabled.value,
        ...(apiKey.value.trim() ? { apiKey: apiKey.value.trim() } : {}) }, context.abort.signal)
      : await saveAiProvider({ providerId: props.provider.id, enabled: enabled.value,
        ...(apiKey.value.trim() ? { apiKey: apiKey.value.trim() } : {}) }, context.abort.signal)
    if (!current(context)) return
    if (!response.data) throw new AiSettingsError('保存响应缺少供应商状态')
    apiKey.value = ''
    emit('saved', response.data)
    showToast('供应商已保存，尚未检测模型调用权限', 'success')
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/** 确认后清除本站供应商配置及必要默认引用，不撤销上游 Key；自定义供应商会连同型号一起删除。 */
async function remove(): Promise<void> {
  if (props.disabled || busy.value || !authStore.token || !props.provider.configured) return
  const context = begin('delete')
  try {
    const confirmed = await showConfirm({
      title: props.provider.custom ? '删除自定义供应商' : '清除供应商',
      message: props.provider.custom
        ? `删除本站保存的 ${props.provider.name} 加密密钥、接口地址与其下全部自定义型号。若它是当前默认供应商，也会清除默认选择；不会撤销供应商账户中的 Key。`
        : `删除本站保存的 ${props.provider.name} 加密密钥。若它是当前默认供应商，也会清除默认选择；不会撤销供应商账户中的 Key。`,
      confirmText: props.provider.custom ? '删除供应商' : '清除供应商', cancelText: '取消', type: 'danger',
    })
    if (!confirmed || !current(context)) return
    if (props.provider.custom) await deleteAiCustomProvider(context.providerId, context.abort.signal)
    else await deleteAiProvider(context.providerId, context.abort.signal)
    if (!current(context)) return
    apiKey.value = ''
    emit('deleted', context.providerId)
    showToast('供应商配置已清除', 'success')
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/**
 * 明确确认额度后仅检测已保存修订与所选型号，不发送题目或聊天。
 * 返回结果仍须匹配账号、修订、型号与未修改表单，不能把旧成功带到新配置。
 */
async function check(): Promise<void> {
  const model = props.model
  const revision = props.provider.revision
  if (!canCheck.value || !model || !revision) return
  const context = begin('check')
  try {
    const confirmed = await showConfirm({ title: '检测模型连接',
      message: `使用已保存的 ${props.provider.name} 凭据检测 ${model.name}（${model.id}），会发一次真实请求并可能消耗额度。确定继续吗？`,
      confirmText: '确认并检测', cancelText: '取消', type: 'warning' })
    if (!confirmed || !current(context)) return
    const response = await checkAiModel({ providerId: context.providerId, providerRevision: revision,
      modelId: model.id, requestId: createUuid(), confirmUsage: true }, context.abort.signal)
    if (!current(context) || props.provider.revision !== revision || props.model?.id !== model.id || dirty.value) return
    if (!response.data) throw new AiSettingsError('检测响应缺少结果')
    checkedModel.value = `${model.name}（${model.id}）`
  } catch (error: unknown) { fail(error, context) }
  finally { finish(context) }
}
/** 中止本地等待并关闭内部请求，不能把停止等待伪装成上游已停止。 */
function reset(): void {
  sequence += 1
  controller?.abort()
  controller = null
  operation.value = null
  apiKey.value = ''
  checkedModel.value = ''
  errorMessage.value = ''
  name.value = props.provider.name
  baseUrl.value = props.provider.baseUrl ?? ''
  protocol.value = props.provider.protocol ?? 'openai-completions'
  enabled.value = props.provider.enabled || !props.provider.configured
  emit('busyChange', false)
}
/** 取消本地检测等待并提示停止确认边界，不保证上游已停止或允许立即重发。 */
function cancelCheck(): void {
  reset()
  errorMessage.value = '已请求停止检测；上游未确认停止前，新的检测或咨询会被拒绝。'
}
// 账号、供应商或修订变化时取消旧请求，并清除局部明文和检测结论。
watch(() => [props.provider.id, props.provider.revision, authStore.token] as const, reset)
// 表单或型号一旦变化，本次成功结论立即失效。
watch(() => [apiKey.value, name.value, baseUrl.value, protocol.value, enabled.value, props.model?.id], () => { checkedModel.value = '' })
onBeforeUnmount(reset)
</script>
